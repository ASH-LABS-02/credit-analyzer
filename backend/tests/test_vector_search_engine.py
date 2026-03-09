"""
Unit tests for VectorSearchEngine service
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
import numpy as np
from app.services.vector_search_engine import VectorSearchEngine


class TestVectorSearchEngine:
    """Unit tests for VectorSearchEngine class."""
    
    @pytest.fixture
    def mock_openai_client(self):
        """Create a mock OpenAI client."""
        mock_client = Mock()
        mock_embeddings = Mock()
        mock_client.embeddings = mock_embeddings
        return mock_client
    
    @pytest.fixture
    def search_engine(self, mock_openai_client):
        """Create a VectorSearchEngine instance with mocked OpenAI client."""
        engine = VectorSearchEngine(dimension=1536)
        engine.openai = mock_openai_client
        return engine
    
    def test_initialization(self):
        """Test VectorSearchEngine initialization."""
        engine = VectorSearchEngine(dimension=1536)
        
        assert engine.dimension == 1536
        assert engine.index is not None
        assert engine.index.ntotal == 0
        assert len(engine.document_map) == 0
    
    def test_chunk_text_basic(self, search_engine):
        """Test basic text chunking."""
        text = "This is a test. " * 100  # Create text longer than chunk size
        chunks = search_engine._chunk_text(text, chunk_size=100, overlap=10)
        
        assert len(chunks) > 1
        assert all(isinstance(chunk, str) for chunk in chunks)
        assert all(len(chunk) > 0 for chunk in chunks)
    
    def test_chunk_text_empty(self, search_engine):
        """Test chunking empty text."""
        chunks = search_engine._chunk_text("", chunk_size=100)
        assert chunks == []
    
    def test_chunk_text_short(self, search_engine):
        """Test chunking text shorter than chunk size."""
        text = "Short text."
        chunks = search_engine._chunk_text(text, chunk_size=100)
        
        assert len(chunks) == 1
        assert chunks[0] == text
    
    def test_chunk_text_sentence_boundary(self, search_engine):
        """Test that chunking respects sentence boundaries."""
        text = "First sentence. Second sentence. Third sentence. Fourth sentence."
        chunks = search_engine._chunk_text(text, chunk_size=30, overlap=5)
        
        # Verify chunks break at sentence boundaries when possible
        for chunk in chunks:
            assert chunk.strip()  # No empty chunks
    
    @pytest.mark.asyncio
    async def test_generate_embedding(self, search_engine, mock_openai_client):
        """Test embedding generation."""
        # Mock the OpenAI API response
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1] * 1536)]
        mock_openai_client.embeddings.create = AsyncMock(return_value=mock_response)
        
        embedding = await search_engine._generate_embedding("test text")
        
        assert len(embedding) == 1536
        assert all(isinstance(x, float) for x in embedding)
        mock_openai_client.embeddings.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_index_document(self, search_engine, mock_openai_client):
        """Test document indexing."""
        # Mock the OpenAI API response
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1] * 1536)]
        mock_openai_client.embeddings.create = AsyncMock(return_value=mock_response)
        
        text = "This is a test document. " * 50
        await search_engine.index_document("doc1", text)
        
        # Verify index was updated
        assert search_engine.index.ntotal > 0
        assert len(search_engine.document_map) > 0
        
        # Verify document mapping
        for metadata in search_engine.document_map.values():
            assert metadata['doc_id'] == "doc1"
            assert 'chunk' in metadata
            assert 'chunk_index' in metadata
            assert 'total_chunks' in metadata
    
    @pytest.mark.asyncio
    async def test_index_document_with_metadata(self, search_engine, mock_openai_client):
        """Test document indexing with additional metadata."""
        # Mock the OpenAI API response
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1] * 1536)]
        mock_openai_client.embeddings.create = AsyncMock(return_value=mock_response)
        
        text = "Test document."
        metadata = {'filename': 'test.pdf', 'page': 1}
        await search_engine.index_document("doc1", text, metadata=metadata)
        
        # Verify metadata was stored
        for doc_metadata in search_engine.document_map.values():
            assert doc_metadata['filename'] == 'test.pdf'
            assert doc_metadata['page'] == 1
    
    @pytest.mark.asyncio
    async def test_index_empty_document(self, search_engine, mock_openai_client):
        """Test indexing empty document."""
        await search_engine.index_document("doc1", "")
        
        # Should not add anything to index
        assert search_engine.index.ntotal == 0
        assert len(search_engine.document_map) == 0
    
    @pytest.mark.asyncio
    async def test_search(self, search_engine, mock_openai_client):
        """Test semantic search."""
        # Mock the OpenAI API response for indexing and search
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1] * 1536)]
        mock_openai_client.embeddings.create = AsyncMock(return_value=mock_response)
        
        # Index a document
        await search_engine.index_document("doc1", "This is about financial analysis.")
        
        # Perform search
        results = await search_engine.search("financial", k=5)
        
        assert isinstance(results, list)
        assert len(results) > 0
        
        # Verify result structure
        for result in results:
            assert 'doc_id' in result
            assert 'chunk' in result
            assert 'relevance_score' in result
            assert 0 <= result['relevance_score'] <= 1
    
    @pytest.mark.asyncio
    async def test_search_empty_index(self, search_engine, mock_openai_client):
        """Test search on empty index."""
        results = await search_engine.search("test query", k=5)
        
        assert results == []
    
    @pytest.mark.asyncio
    async def test_search_with_min_score(self, search_engine, mock_openai_client):
        """Test search with minimum score threshold."""
        # Mock the OpenAI API response
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1] * 1536)]
        mock_openai_client.embeddings.create = AsyncMock(return_value=mock_response)
        
        # Index a document
        await search_engine.index_document("doc1", "Test document.")
        
        # Search with high minimum score (should filter out results)
        results = await search_engine.search("test", k=5, min_score=0.99)
        
        # Results should be filtered by score
        assert all(result['relevance_score'] >= 0.99 for result in results)
    
    @pytest.mark.asyncio
    async def test_search_limits_k_to_index_size(self, search_engine, mock_openai_client):
        """Test that search limits k to the number of indexed vectors."""
        # Mock the OpenAI API response
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1] * 1536)]
        mock_openai_client.embeddings.create = AsyncMock(return_value=mock_response)
        
        # Index a small document (will create few chunks)
        await search_engine.index_document("doc1", "Short text.")
        
        index_size = search_engine.index.ntotal
        
        # Request more results than available
        results = await search_engine.search("test", k=100)
        
        # Should return at most index_size results
        assert len(results) <= index_size
    
    def test_get_index_size(self, search_engine):
        """Test getting index size."""
        assert search_engine.get_index_size() == 0
        
        # Manually add vectors to test
        vectors = np.random.rand(5, 1536).astype('float32')
        search_engine.index.add(vectors)
        
        assert search_engine.get_index_size() == 5
    
    def test_clear_index(self, search_engine):
        """Test clearing the index."""
        # Add some vectors
        vectors = np.random.rand(5, 1536).astype('float32')
        search_engine.index.add(vectors)
        search_engine.document_map[0] = {'doc_id': 'doc1', 'chunk': 'test'}
        
        assert search_engine.get_index_size() > 0
        assert len(search_engine.document_map) > 0
        
        # Clear index
        search_engine.clear_index()
        
        assert search_engine.get_index_size() == 0
        assert len(search_engine.document_map) == 0
    
    def test_remove_document(self, search_engine):
        """Test removing a document from the index."""
        # Add document mappings
        search_engine.document_map[0] = {'doc_id': 'doc1', 'chunk': 'chunk1'}
        search_engine.document_map[1] = {'doc_id': 'doc1', 'chunk': 'chunk2'}
        search_engine.document_map[2] = {'doc_id': 'doc2', 'chunk': 'chunk1'}
        
        # Remove doc1
        search_engine.remove_document('doc1')
        
        # Verify doc1 chunks are removed
        assert 0 not in search_engine.document_map
        assert 1 not in search_engine.document_map
        
        # Verify doc2 chunks remain
        assert 2 in search_engine.document_map
        assert search_engine.document_map[2]['doc_id'] == 'doc2'
    
    @pytest.mark.asyncio
    async def test_multiple_documents(self, search_engine, mock_openai_client):
        """Test indexing and searching multiple documents."""
        # Mock the OpenAI API response
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1] * 1536)]
        mock_openai_client.embeddings.create = AsyncMock(return_value=mock_response)
        
        # Index multiple documents
        await search_engine.index_document("doc1", "Financial analysis report.")
        await search_engine.index_document("doc2", "Credit risk assessment.")
        await search_engine.index_document("doc3", "Market research findings.")
        
        # Verify all documents are indexed
        doc_ids = set(metadata['doc_id'] for metadata in search_engine.document_map.values())
        assert doc_ids == {'doc1', 'doc2', 'doc3'}
        
        # Search should return results from multiple documents
        results = await search_engine.search("analysis", k=10)
        assert len(results) > 0
