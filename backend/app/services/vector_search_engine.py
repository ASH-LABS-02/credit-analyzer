"""
Vector Search Engine Service

Provides semantic search capabilities over document content using FAISS vector indexing
and OpenAI embeddings. Supports document chunking, embedding generation, and similarity search.
"""

from typing import List, Dict, Optional

# Optional imports for vector search (not available on Vercel)
try:
    import numpy as np
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    np = None
    faiss = None

from openai import AsyncOpenAI
from app.core.config import settings


class VectorSearchEngine:
    """
    Vector search engine for semantic document search.
    
    Uses FAISS for efficient vector similarity search and OpenAI's text-embedding-ada-002
    model for generating embeddings. Documents are chunked into smaller segments for
    better search granularity.
    """
    
    def __init__(self, dimension: int = 1536):
        """
        Initialize the vector search engine.
        
        Args:
            dimension: Dimension of the embedding vectors (default 1536 for OpenAI ada-002)
        """
        self.dimension = dimension
        self.index = faiss.IndexFlatL2(dimension)
        self.document_map: Dict[int, Dict] = {}
        self.openai = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    
    def _chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """
        Split text into overlapping chunks for better search coverage.
        
        Args:
            text: Text to chunk
            chunk_size: Target size of each chunk in characters
            overlap: Number of characters to overlap between chunks
            
        Returns:
            List of text chunks
        """
        if not text:
            return []
        
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = start + chunk_size
            
            # If this is not the last chunk, try to break at a sentence or word boundary
            if end < text_length:
                # Look for sentence boundary (. ! ?)
                sentence_end = max(
                    text.rfind('. ', start, end),
                    text.rfind('! ', start, end),
                    text.rfind('? ', start, end)
                )
                
                if sentence_end > start:
                    end = sentence_end + 1
                else:
                    # Look for word boundary (space)
                    space_pos = text.rfind(' ', start, end)
                    if space_pos > start:
                        end = space_pos
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start position with overlap
            start = end - overlap if end < text_length else text_length
        
        return chunks
    
    async def _generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for text using OpenAI API.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector as list of floats
        """
        response = await self.openai.embeddings.create(
            model="text-embedding-ada-002",
            input=text
        )
        return response.data[0].embedding
    
    async def index_document(self, doc_id: str, text: str, metadata: Optional[Dict] = None):
        """
        Index a document by generating embeddings and adding to FAISS index.
        
        Splits the document into chunks, generates embeddings for each chunk,
        and stores them in the FAISS index with document mapping.
        
        Args:
            doc_id: Unique identifier for the document
            text: Document text content
            metadata: Optional metadata to store with the document (e.g., filename, page numbers)
        """
        # Split text into chunks
        chunks = self._chunk_text(text)
        
        if not chunks:
            return
        
        # Generate embeddings for all chunks
        embeddings = []
        for chunk in chunks:
            embedding = await self._generate_embedding(chunk)
            embeddings.append(embedding)
        
        # Convert to numpy array and add to FAISS index
        embeddings_array = np.array(embeddings).astype('float32')
        start_idx = self.index.ntotal
        self.index.add(embeddings_array)
        
        # Store document mapping for retrieval
        for i, chunk in enumerate(chunks):
            chunk_metadata = {
                'doc_id': doc_id,
                'chunk': chunk,
                'chunk_index': i,
                'total_chunks': len(chunks)
            }
            
            # Add any additional metadata
            if metadata:
                chunk_metadata.update(metadata)
            
            self.document_map[start_idx + i] = chunk_metadata
    
    async def search(self, query: str, k: int = 5, min_score: float = 0.0) -> List[Dict]:
        """
        Perform semantic search across indexed documents.
        
        Generates an embedding for the query and searches for the k most similar
        document chunks in the FAISS index.
        
        Args:
            query: Search query text
            k: Number of results to return
            min_score: Minimum relevance score threshold (0.0 to 1.0)
            
        Returns:
            List of search results, each containing:
                - doc_id: Document identifier
                - chunk: Matching text chunk
                - chunk_index: Index of the chunk within the document
                - total_chunks: Total number of chunks in the document
                - relevance_score: Similarity score (0.0 to 1.0, higher is better)
                - Any additional metadata stored during indexing
        """
        if self.index.ntotal == 0:
            return []
        
        # Generate query embedding
        query_embedding = await self._generate_embedding(query)
        query_array = np.array([query_embedding]).astype('float32')
        
        # Search FAISS index
        # Limit k to the number of indexed vectors
        k = min(k, self.index.ntotal)
        distances, indices = self.index.search(query_array, k)
        
        # Convert results to list of dictionaries
        results = []
        for i, idx in enumerate(indices[0]):
            if idx in self.document_map:
                # Convert L2 distance to similarity score (0 to 1, higher is better)
                # Using formula: score = 1 / (1 + distance)
                distance = float(distances[0][i])
                relevance_score = 1.0 / (1.0 + distance)
                
                # Filter by minimum score
                if relevance_score >= min_score:
                    result = self.document_map[idx].copy()
                    result['relevance_score'] = relevance_score
                    results.append(result)
        
        return results
    
    def get_index_size(self) -> int:
        """
        Get the number of vectors in the index.
        
        Returns:
            Number of indexed vectors
        """
        return self.index.ntotal
    
    def clear_index(self):
        """
        Clear all vectors from the index and reset document mapping.
        """
        self.index.reset()
        self.document_map.clear()
    
    def remove_document(self, doc_id: str):
        """
        Remove all chunks of a document from the index.
        
        Note: FAISS doesn't support efficient deletion, so this marks chunks
        as removed in the document map. For production use, consider rebuilding
        the index periodically to reclaim space.
        
        Args:
            doc_id: Document identifier to remove
        """
        # Find all indices for this document
        indices_to_remove = [
            idx for idx, metadata in self.document_map.items()
            if metadata['doc_id'] == doc_id
        ]
        
        # Remove from document map
        for idx in indices_to_remove:
            del self.document_map[idx]
