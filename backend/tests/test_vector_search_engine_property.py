"""
Property-based tests for VectorSearchEngine service.

These tests validate that vector embedding indexing and semantic search
functionality work correctly across a wide range of inputs.

Feature: intelli-credit-platform
Requirements: 16.1, 16.2, 16.3
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from unittest.mock import Mock, AsyncMock, patch
import numpy as np
from typing import List

from app.services.vector_search_engine import VectorSearchEngine


# Custom strategies for generating test data
@st.composite
def document_text_strategy(draw):
    """Generate realistic document text."""
    # Generate text with sentences
    num_sentences = draw(st.integers(min_value=1, max_value=50))
    sentences = []
    for _ in range(num_sentences):
        sentence = draw(st.text(
            min_size=10,
            max_size=200,
            alphabet=st.characters(
                whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs'),
                whitelist_characters='.,!?-'
            )
        ))
        sentences.append(sentence.strip())
    
    return ' '.join(sentences)


@st.composite
def document_id_strategy(draw):
    """Generate valid document IDs."""
    return draw(st.text(
        min_size=1,
        max_size=50,
        alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            whitelist_characters='-_'
        )
    ))


@st.composite
def search_query_strategy(draw):
    """Generate realistic search queries."""
    return draw(st.text(
        min_size=1,
        max_size=200,
        alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs'),
            whitelist_characters='.,!?-'
        )
    ))


@st.composite
def metadata_strategy(draw):
    """Generate document metadata."""
    return draw(st.dictionaries(
        keys=st.text(
            min_size=1,
            max_size=20,
            alphabet=st.characters(
                whitelist_categories=('Lu', 'Ll'),
                whitelist_characters='_'
            )
        ),
        values=st.one_of(
            st.text(max_size=100),
            st.integers(min_value=1, max_value=10000),
            st.floats(min_value=0, max_value=1000, allow_nan=False, allow_infinity=False)
        ),
        min_size=0,
        max_size=10
    ))


def create_mock_openai_client():
    """Create a mock OpenAI client that returns consistent embeddings."""
    mock_client = Mock()
    mock_embeddings = Mock()
    
    # Create a function that generates deterministic embeddings based on text
    def create_embedding_response(text: str) -> List[float]:
        """Generate a deterministic embedding based on text hash."""
        # Use hash of text to generate deterministic but varied embeddings
        text_hash = hash(text)
        np.random.seed(abs(text_hash) % (2**32))
        embedding = np.random.rand(1536).tolist()
        return embedding
    
    async def mock_create(**kwargs):
        text = kwargs.get('input', '')
        embedding = create_embedding_response(text)
        
        mock_response = Mock()
        mock_response.data = [Mock(embedding=embedding)]
        return mock_response
    
    mock_embeddings.create = AsyncMock(side_effect=mock_create)
    mock_client.embeddings = mock_embeddings
    
    return mock_client


# Property 34: Vector Embedding Indexing
# **Validates: Requirements 16.1**
@pytest.mark.property
@settings(max_examples=20, deadline=None)
@given(
    doc_id=document_id_strategy(),
    text=document_text_strategy(),
    metadata=metadata_strategy()
)
def test_vector_embedding_indexing(doc_id, text, metadata):
    """
    Property 34: Vector Embedding Indexing
    
    For any processed document, the system should generate vector embeddings
    for the document content and store them in the FAISS index, enabling
    semantic search.
    
    **Validates: Requirements 16.1**
    """
    # Skip empty or whitespace-only text
    assume(text.strip() != '')
    
    # Create search engine with mocked OpenAI client
    search_engine = VectorSearchEngine(dimension=1536)
    search_engine.openai = create_mock_openai_client()
    
    # Get initial index size
    initial_size = search_engine.get_index_size()
    
    # Index the document
    import asyncio
    try:
        asyncio.run(search_engine.index_document(doc_id, text, metadata))
    except Exception as e:
        pytest.fail(f"Failed to index document: {e}")
    
    # Verify embeddings were generated and stored
    final_size = search_engine.get_index_size()
    assert final_size > initial_size, "Index size should increase after indexing a document"
    
    # Verify document mapping was created
    assert len(search_engine.document_map) > 0, "Document map should contain entries"
    
    # Verify all document map entries have the correct doc_id
    for idx, doc_metadata in search_engine.document_map.items():
        assert doc_metadata['doc_id'] == doc_id, f"Document ID should match for index {idx}"
        assert 'chunk' in doc_metadata, "Each entry should have a chunk"
        assert 'chunk_index' in doc_metadata, "Each entry should have a chunk_index"
        assert 'total_chunks' in doc_metadata, "Each entry should have total_chunks"
        
        # Verify metadata was stored
        for key, value in metadata.items():
            assert key in doc_metadata, f"Metadata key '{key}' should be stored"
            assert doc_metadata[key] == value, f"Metadata value for '{key}' should match"
    
    # Verify chunk indices are sequential and start from 0
    chunk_indices = sorted([meta['chunk_index'] for meta in search_engine.document_map.values()])
    expected_indices = list(range(len(chunk_indices)))
    assert chunk_indices == expected_indices, "Chunk indices should be sequential starting from 0"
    
    # Verify all chunks have the same total_chunks value
    total_chunks_values = set(meta['total_chunks'] for meta in search_engine.document_map.values())
    assert len(total_chunks_values) == 1, "All chunks should have the same total_chunks value"
    assert list(total_chunks_values)[0] == len(chunk_indices), "total_chunks should match actual number of chunks"


# Property 35: Semantic Search Functionality
# **Validates: Requirements 16.2, 16.3**
@pytest.mark.property
@settings(max_examples=20, deadline=None)
@given(
    documents=st.lists(
        st.tuples(document_id_strategy(), document_text_strategy()),
        min_size=1,
        max_size=5,
        unique_by=lambda x: x[0]  # Unique document IDs
    ),
    query=search_query_strategy(),
    k=st.integers(min_value=1, max_value=10),
    min_score=st.floats(min_value=0.0, max_value=1.0)
)
def test_semantic_search_functionality(documents, query, k, min_score):
    """
    Property 35: Semantic Search Functionality
    
    For any search query submitted for an application, the system should
    perform semantic search across all indexed documents and return results
    ranked by relevance with highlighted matching sections.
    
    **Validates: Requirements 16.2, 16.3**
    """
    # Skip empty or whitespace-only query
    assume(query.strip() != '')
    
    # Skip documents with empty text
    documents = [(doc_id, text) for doc_id, text in documents if text.strip() != '']
    assume(len(documents) > 0)
    
    # Create search engine with mocked OpenAI client
    search_engine = VectorSearchEngine(dimension=1536)
    search_engine.openai = create_mock_openai_client()
    
    # Index all documents
    import asyncio
    for doc_id, text in documents:
        try:
            asyncio.run(search_engine.index_document(doc_id, text))
        except Exception as e:
            pytest.fail(f"Failed to index document {doc_id}: {e}")
    
    # Verify documents were indexed
    assert search_engine.get_index_size() > 0, "Index should contain vectors after indexing"
    
    # Perform semantic search
    results = None
    try:
        results = asyncio.run(search_engine.search(query, k=k, min_score=min_score))
    except Exception as e:
        pytest.fail(f"Failed to perform search: {e}")
    
    # Verify search returns a list
    assert isinstance(results, list), "Search should return a list of results"
    
    # Verify results are within requested limit
    assert len(results) <= k, f"Number of results should not exceed k={k}"
    
    # Verify results don't exceed total indexed chunks
    total_chunks = search_engine.get_index_size()
    assert len(results) <= total_chunks, "Number of results should not exceed total indexed chunks"
    
    # Verify each result has required fields
    for result in results:
        assert 'doc_id' in result, "Result should have doc_id"
        assert 'chunk' in result, "Result should have chunk (matching section)"
        assert 'chunk_index' in result, "Result should have chunk_index"
        assert 'total_chunks' in result, "Result should have total_chunks"
        assert 'relevance_score' in result, "Result should have relevance_score"
        
        # Verify doc_id is from indexed documents
        indexed_doc_ids = [doc_id for doc_id, _ in documents]
        assert result['doc_id'] in indexed_doc_ids, "Result doc_id should be from indexed documents"
        
        # Verify relevance score is in valid range
        assert 0.0 <= result['relevance_score'] <= 1.0, "Relevance score should be between 0 and 1"
        
        # Verify relevance score meets minimum threshold
        assert result['relevance_score'] >= min_score, f"Relevance score should be >= min_score={min_score}"
        
        # Verify chunk is non-empty
        assert isinstance(result['chunk'], str), "Chunk should be a string"
        assert len(result['chunk']) > 0, "Chunk should not be empty"
    
    # Verify results are ranked by relevance (descending order)
    if len(results) > 1:
        relevance_scores = [result['relevance_score'] for result in results]
        assert relevance_scores == sorted(relevance_scores, reverse=True), \
            "Results should be ranked by relevance score in descending order"


# Additional property test: Empty index search
@pytest.mark.property
@settings(max_examples=20, deadline=None)
@given(query=search_query_strategy())
def test_search_empty_index_returns_empty_list(query):
    """
    Additional property test: Search on empty index should return empty list.
    
    For any search query on an empty index, the system should return an empty
    list without errors.
    
    **Validates: Requirements 16.2**
    """
    # Skip empty or whitespace-only query
    assume(query.strip() != '')
    
    # Create search engine with mocked OpenAI client
    search_engine = VectorSearchEngine(dimension=1536)
    search_engine.openai = create_mock_openai_client()
    
    # Verify index is empty
    assert search_engine.get_index_size() == 0, "Index should be empty initially"
    
    # Perform search on empty index
    import asyncio
    results = None
    try:
        results = asyncio.run(search_engine.search(query, k=5))
    except Exception as e:
        pytest.fail(f"Search on empty index should not raise exception: {e}")
    
    # Verify empty results
    assert results == [], "Search on empty index should return empty list"


# Additional property test: Document removal
@pytest.mark.property
@settings(max_examples=20, deadline=None)
@given(
    documents=st.lists(
        st.tuples(document_id_strategy(), document_text_strategy()),
        min_size=2,
        max_size=5,
        unique_by=lambda x: x[0]  # Unique document IDs
    )
)
def test_document_removal_from_index(documents):
    """
    Additional property test: Document removal should remove all chunks.
    
    For any indexed document, removing it should remove all its chunks from
    the document map.
    
    **Validates: Requirements 16.1**
    """
    # Skip documents with empty text
    documents = [(doc_id, text) for doc_id, text in documents if text.strip() != '']
    assume(len(documents) >= 2)
    
    # Create search engine with mocked OpenAI client
    search_engine = VectorSearchEngine(dimension=1536)
    search_engine.openai = create_mock_openai_client()
    
    # Index all documents
    import asyncio
    for doc_id, text in documents:
        try:
            asyncio.run(search_engine.index_document(doc_id, text))
        except Exception as e:
            pytest.fail(f"Failed to index document {doc_id}: {e}")
    
    # Get initial document map size
    initial_map_size = len(search_engine.document_map)
    assert initial_map_size > 0, "Document map should have entries after indexing"
    
    # Select first document to remove
    doc_to_remove = documents[0][0]
    
    # Count chunks for the document to remove
    chunks_to_remove = sum(
        1 for meta in search_engine.document_map.values()
        if meta['doc_id'] == doc_to_remove
    )
    assert chunks_to_remove > 0, "Document to remove should have chunks"
    
    # Remove the document
    search_engine.remove_document(doc_to_remove)
    
    # Verify document was removed from map
    final_map_size = len(search_engine.document_map)
    assert final_map_size == initial_map_size - chunks_to_remove, \
        "Document map size should decrease by number of removed chunks"
    
    # Verify no chunks remain for removed document
    remaining_doc_ids = set(meta['doc_id'] for meta in search_engine.document_map.values())
    assert doc_to_remove not in remaining_doc_ids, \
        "Removed document ID should not appear in document map"
    
    # Verify other documents remain
    for doc_id, _ in documents[1:]:
        assert doc_id in remaining_doc_ids, \
            f"Other documents should remain in index after removing {doc_to_remove}"


# Additional property test: Index clearing
@pytest.mark.property
@settings(max_examples=20, deadline=None)
@given(
    documents=st.lists(
        st.tuples(document_id_strategy(), document_text_strategy()),
        min_size=1,
        max_size=5,
        unique_by=lambda x: x[0]  # Unique document IDs
    )
)
def test_clear_index_removes_all_data(documents):
    """
    Additional property test: Clearing index should remove all vectors and mappings.
    
    For any indexed documents, clearing the index should reset it to empty state.
    
    **Validates: Requirements 16.1**
    """
    # Skip documents with empty text
    documents = [(doc_id, text) for doc_id, text in documents if text.strip() != '']
    assume(len(documents) > 0)
    
    # Create search engine with mocked OpenAI client
    search_engine = VectorSearchEngine(dimension=1536)
    search_engine.openai = create_mock_openai_client()
    
    # Index all documents
    import asyncio
    for doc_id, text in documents:
        try:
            asyncio.run(search_engine.index_document(doc_id, text))
        except Exception as e:
            pytest.fail(f"Failed to index document {doc_id}: {e}")
    
    # Verify index has data
    assert search_engine.get_index_size() > 0, "Index should have vectors after indexing"
    assert len(search_engine.document_map) > 0, "Document map should have entries after indexing"
    
    # Clear the index
    search_engine.clear_index()
    
    # Verify index is empty
    assert search_engine.get_index_size() == 0, "Index should be empty after clearing"
    assert len(search_engine.document_map) == 0, "Document map should be empty after clearing"


# Additional property test: Minimum score filtering
@pytest.mark.property
@settings(max_examples=20, deadline=None)
@given(
    documents=st.lists(
        st.tuples(document_id_strategy(), document_text_strategy()),
        min_size=1,
        max_size=3,
        unique_by=lambda x: x[0]  # Unique document IDs
    ),
    query=search_query_strategy(),
    min_score=st.floats(min_value=0.0, max_value=1.0)
)
def test_min_score_filtering(documents, query, min_score):
    """
    Additional property test: Minimum score filtering should work correctly.
    
    For any search with a minimum score threshold, all returned results should
    have relevance scores >= min_score.
    
    **Validates: Requirements 16.3**
    """
    # Skip empty or whitespace-only query
    assume(query.strip() != '')
    
    # Skip documents with empty text
    documents = [(doc_id, text) for doc_id, text in documents if text.strip() != '']
    assume(len(documents) > 0)
    
    # Create search engine with mocked OpenAI client
    search_engine = VectorSearchEngine(dimension=1536)
    search_engine.openai = create_mock_openai_client()
    
    # Index all documents
    import asyncio
    for doc_id, text in documents:
        try:
            asyncio.run(search_engine.index_document(doc_id, text))
        except Exception as e:
            pytest.fail(f"Failed to index document {doc_id}: {e}")
    
    # Perform search with minimum score
    results = None
    try:
        results = asyncio.run(search_engine.search(query, k=10, min_score=min_score))
    except Exception as e:
        pytest.fail(f"Failed to perform search: {e}")
    
    # Verify all results meet minimum score threshold
    for result in results:
        assert result['relevance_score'] >= min_score, \
            f"All results should have relevance_score >= {min_score}, got {result['relevance_score']}"
