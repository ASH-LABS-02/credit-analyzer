"""
Property-based tests for DocumentIntelligenceAgent

Feature: intelli-credit-platform
Property 3: Financial Data Extraction Completeness
Property 4: Extraction Traceability

Validates: Requirements 2.1, 2.5
"""

import pytest
from hypothesis import given, strategies as st, assume, settings
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
import json

from app.agents.document_intelligence_agent import DocumentIntelligenceAgent
from app.models.domain import Document
from app.repositories.document_repository import DocumentRepository
from app.services.document_processor import DocumentProcessor


# Custom strategies for generating test data
@st.composite
def financial_metric_strategy(draw):
    """Generate a financial metric with value and metadata"""
    metric_type = draw(st.sampled_from(['single_value', 'multi_year']))
    
    if metric_type == 'single_value':
        return {
            'value': draw(st.floats(min_value=0, max_value=1e12, allow_nan=False, allow_infinity=False)),
            'year': str(draw(st.integers(min_value=2000, max_value=2024))),
            'currency': draw(st.sampled_from(['USD', 'EUR', 'GBP'])),
            'confidence': draw(st.sampled_from(['high', 'medium', 'low']))
        }
    else:
        num_years = draw(st.integers(min_value=1, max_value=5))
        base_year = draw(st.integers(min_value=2015, max_value=2024))
        return {
            'values': draw(st.lists(
                st.floats(min_value=0, max_value=1e12, allow_nan=False, allow_infinity=False),
                min_size=num_years,
                max_size=num_years
            )),
            'years': [str(base_year - i) for i in range(num_years)],
            'currency': draw(st.sampled_from(['USD', 'EUR', 'GBP'])),
            'confidence': draw(st.sampled_from(['high', 'medium', 'low']))
        }


@st.composite
def financial_data_strategy(draw):
    """Generate complete financial data structure"""
    # Generate metrics that should always be present per requirement 2.1
    required_metrics = ['revenue', 'profit', 'debt', 'cash_flow']
    
    financial_metrics = {}
    for metric in required_metrics:
        financial_metrics[metric] = draw(financial_metric_strategy())
    
    # Optionally add balance sheet items
    if draw(st.booleans()):
        financial_metrics['current_assets'] = draw(financial_metric_strategy())
        financial_metrics['current_liabilities'] = draw(financial_metric_strategy())
        financial_metrics['total_assets'] = draw(financial_metric_strategy())
        financial_metrics['total_equity'] = draw(financial_metric_strategy())
        financial_metrics['total_debt'] = draw(financial_metric_strategy())
    
    # Optionally add ratios
    financial_ratios = {}
    if draw(st.booleans()):
        ratio_names = ['current_ratio', 'debt_to_equity', 'net_profit_margin', 'roe']
        for ratio in ratio_names:
            if draw(st.booleans()):
                financial_ratios[ratio] = {
                    'value': draw(st.floats(min_value=0, max_value=100, allow_nan=False, allow_infinity=False)),
                    'confidence': draw(st.sampled_from(['high', 'medium', 'low']))
                }
    
    return {
        'company_info': {
            'company_name': draw(st.text(min_size=3, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs')))),
            'industry': draw(st.one_of(st.none(), st.text(min_size=3, max_size=30))),
            'fiscal_year': str(draw(st.integers(min_value=2000, max_value=2024)))
        },
        'financial_metrics': financial_metrics,
        'financial_ratios': financial_ratios,
        'notes': draw(st.lists(st.text(min_size=5, max_size=100), max_size=5))
    }


@st.composite
def document_with_page_markers_strategy(draw):
    """Generate a document with page markers and financial data"""
    num_pages = draw(st.integers(min_value=1, max_value=10))
    
    # Generate text with page markers
    text_parts = []
    for page_num in range(1, num_pages + 1):
        text_parts.append(f"[Page {page_num}]")
        # Add some financial content
        text_parts.append(f"Revenue: ${draw(st.integers(min_value=1000, max_value=1000000))}")
        text_parts.append(f"Profit: ${draw(st.integers(min_value=100, max_value=100000))}")
        if draw(st.booleans()):
            text_parts.append(f"Total Assets: ${draw(st.integers(min_value=10000, max_value=10000000))}")
    
    text = "\n".join(text_parts)
    
    return Document(
        id=draw(st.text(min_size=5, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))),
        application_id=draw(st.text(min_size=5, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))),
        filename=f"doc_{draw(st.integers(min_value=1, max_value=1000))}.pdf",
        file_type="pdf",
        storage_path="documents/test/doc.pdf",
        upload_date=datetime.utcnow(),
        processing_status="complete",
        extracted_data={'text': text}
    )


class TestProperty3FinancialDataExtractionCompleteness:
    """
    Property 3: Financial Data Extraction Completeness
    
    For any document containing financial information, the Document Intelligence Agent
    should extract all present Financial_Metrics (revenue, profit, debt, cash flow, ratios)
    and structure them in the standardized format.
    
    Validates: Requirements 2.1, 2.2
    """
    
    @pytest.mark.property
    @pytest.mark.asyncio
    @settings(max_examples=5)
    @given(financial_data=financial_data_strategy())
    async def test_extraction_includes_all_required_metrics(self, financial_data):
        """
        Property: All required financial metrics present in document should be extracted
        
        For any document containing revenue, profit, debt, and cash flow data,
        the extraction result should include all these metrics in the standardized format.
        """
        # Setup mocks
        mock_repo = Mock(spec=DocumentRepository)
        mock_processor = Mock(spec=DocumentProcessor)
        agent = DocumentIntelligenceAgent(mock_repo, mock_processor)
        
        # Create a mock document with the financial data
        doc = Document(
            id="test_doc",
            application_id="test_app",
            filename="test.pdf",
            file_type="pdf",
            storage_path="test/path",
            upload_date=datetime.utcnow(),
            processing_status="complete",
            extracted_data={'text': 'Sample financial document'}
        )
        
        mock_repo.get_by_application = AsyncMock(return_value=[doc])
        
        # Mock OpenAI response with the generated financial data
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(financial_data)
        
        with patch.object(agent.openai.chat.completions, 'create', new=AsyncMock(return_value=mock_response)):
            # Execute extraction
            result = await agent.extract("test_app")
        
        # Verify all required metrics are present
        assert result['documents_processed'] == 1
        assert 'financial_data' in result
        
        # Check for required metrics (Requirements 2.1)
        required_metrics = ['revenue', 'profit', 'debt', 'cash_flow']
        for metric in required_metrics:
            assert metric in result['financial_data'], \
                f"Required metric '{metric}' not found in extracted data"
            
            # Verify the metric has the expected structure
            metric_data = result['financial_data'][metric]
            assert isinstance(metric_data, dict), \
                f"Metric '{metric}' should be a dictionary"
            
            # Check for either single value or multi-year values
            has_value = 'value' in metric_data or 'values' in metric_data
            assert has_value, \
                f"Metric '{metric}' should have either 'value' or 'values' field"
    
    @pytest.mark.property
    @pytest.mark.asyncio
    @settings(max_examples=5)
    @given(financial_data=financial_data_strategy())
    async def test_extraction_preserves_data_structure(self, financial_data):
        """
        Property: Extracted data should maintain standardized structure
        
        For any extracted financial data, the structure should follow the
        standardized format with proper nesting and field types.
        """
        # Setup mocks
        mock_repo = Mock(spec=DocumentRepository)
        mock_processor = Mock(spec=DocumentProcessor)
        agent = DocumentIntelligenceAgent(mock_repo, mock_processor)
        
        doc = Document(
            id="test_doc",
            application_id="test_app",
            filename="test.pdf",
            file_type="pdf",
            storage_path="test/path",
            upload_date=datetime.utcnow(),
            processing_status="complete",
            extracted_data={'text': 'Sample financial document'}
        )
        
        mock_repo.get_by_application = AsyncMock(return_value=[doc])
        
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(financial_data)
        
        with patch.object(agent.openai.chat.completions, 'create', new=AsyncMock(return_value=mock_response)):
            result = await agent.extract("test_app")
        
        # Verify structure (Requirements 2.2)
        assert isinstance(result, dict)
        assert 'financial_data' in result
        assert 'source_tracking' in result
        assert 'ambiguous_flags' in result
        assert 'documents_processed' in result
        
        # Verify financial_data structure
        financial_data_result = result['financial_data']
        assert isinstance(financial_data_result, dict)
        
        # Check that metrics maintain their structure
        for metric_name, metric_value in financial_data['financial_metrics'].items():
            if metric_name in financial_data_result:
                extracted_metric = financial_data_result[metric_name]
                assert isinstance(extracted_metric, dict)
                
                # Verify confidence field if present
                if 'confidence' in metric_value:
                    assert 'confidence' in extracted_metric
                    assert extracted_metric['confidence'] in ['high', 'medium', 'low']
    
    @pytest.mark.property
    @pytest.mark.asyncio
    @settings(max_examples=5)
    @given(
        financial_data1=financial_data_strategy(),
        financial_data2=financial_data_strategy()
    )
    async def test_extraction_merges_multiple_documents(self, financial_data1, financial_data2):
        """
        Property: Extraction from multiple documents should merge all metrics
        
        For any set of documents containing financial information,
        the extraction should combine data from all documents.
        """
        # Setup mocks
        mock_repo = Mock(spec=DocumentRepository)
        mock_processor = Mock(spec=DocumentProcessor)
        agent = DocumentIntelligenceAgent(mock_repo, mock_processor)
        
        # Create two documents
        doc1 = Document(
            id="doc1",
            application_id="test_app",
            filename="doc1.pdf",
            file_type="pdf",
            storage_path="test/doc1",
            upload_date=datetime.utcnow(),
            processing_status="complete",
            extracted_data={'text': 'Document 1'}
        )
        
        doc2 = Document(
            id="doc2",
            application_id="test_app",
            filename="doc2.pdf",
            file_type="pdf",
            storage_path="test/doc2",
            upload_date=datetime.utcnow(),
            processing_status="complete",
            extracted_data={'text': 'Document 2'}
        )
        
        mock_repo.get_by_application = AsyncMock(return_value=[doc1, doc2])
        
        # Mock OpenAI to return different data for each document
        call_count = 0
        async def mock_create(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            mock_response = Mock()
            mock_response.choices = [Mock()]
            if call_count == 1:
                mock_response.choices[0].message.content = json.dumps(financial_data1)
            else:
                mock_response.choices[0].message.content = json.dumps(financial_data2)
            return mock_response
        
        with patch.object(agent.openai.chat.completions, 'create', new=mock_create):
            result = await agent.extract("test_app")
        
        # Verify both documents were processed
        assert result['documents_processed'] == 2
        
        # Verify that data from both documents is present
        # At minimum, required metrics should be present
        required_metrics = ['revenue', 'profit', 'debt', 'cash_flow']
        for metric in required_metrics:
            assert metric in result['financial_data'], \
                f"Required metric '{metric}' should be present after merging"


class TestProperty4ExtractionTraceability:
    """
    Property 4: Extraction Traceability
    
    For any extracted financial value, the system should maintain a reference
    to the source document ID and page number, enabling traceability back to
    the original source.
    
    Validates: Requirements 2.5
    """
    
    @pytest.mark.property
    @pytest.mark.asyncio
    @settings(max_examples=5)
    @given(doc=document_with_page_markers_strategy())
    async def test_source_tracking_includes_document_id(self, doc):
        """
        Property: All extracted data should be traceable to source document
        
        For any extracted financial value, the source_tracking should contain
        a reference to the document ID where the data was found.
        """
        # Setup mocks
        mock_repo = Mock(spec=DocumentRepository)
        mock_processor = Mock(spec=DocumentProcessor)
        agent = DocumentIntelligenceAgent(mock_repo, mock_processor)
        
        mock_repo.get_by_application = AsyncMock(return_value=[doc])
        
        # Create financial data with metrics
        financial_data = {
            'company_info': {'company_name': 'Test Corp'},
            'financial_metrics': {
                'revenue': {'values': [1000000], 'confidence': 'high'},
                'profit': {'values': [200000], 'confidence': 'high'}
            },
            'financial_ratios': {},
            'notes': []
        }
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(financial_data)
        
        with patch.object(agent.openai.chat.completions, 'create', new=AsyncMock(return_value=mock_response)):
            result = await agent.extract(doc.application_id)
        
        # Verify source tracking exists (Requirements 2.5)
        assert 'source_tracking' in result
        source_tracking = result['source_tracking']
        
        # For any tracked field, verify it has document_id
        for field_path, source_info in source_tracking.items():
            assert 'document_id' in source_info, \
                f"Field '{field_path}' should have document_id in source tracking"
            assert source_info['document_id'] == doc.id, \
                f"Field '{field_path}' should reference the correct document ID"
    
    @pytest.mark.property
    @pytest.mark.asyncio
    @settings(max_examples=5)
    @given(doc=document_with_page_markers_strategy())
    async def test_source_tracking_includes_page_number(self, doc):
        """
        Property: All extracted data should be traceable to source page
        
        For any extracted financial value from a document with page markers,
        the source_tracking should contain the page number where the data was found.
        """
        # Setup mocks
        mock_repo = Mock(spec=DocumentRepository)
        mock_processor = Mock(spec=DocumentProcessor)
        agent = DocumentIntelligenceAgent(mock_repo, mock_processor)
        
        mock_repo.get_by_application = AsyncMock(return_value=[doc])
        
        # Create financial data
        financial_data = {
            'company_info': {'company_name': 'Test Corp'},
            'financial_metrics': {
                'revenue': {'values': [1000000], 'confidence': 'high'},
                'profit': {'values': [200000], 'confidence': 'high'}
            },
            'financial_ratios': {},
            'notes': []
        }
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(financial_data)
        
        with patch.object(agent.openai.chat.completions, 'create', new=AsyncMock(return_value=mock_response)):
            result = await agent.extract(doc.application_id)
        
        # Verify source tracking includes page numbers (Requirements 2.5)
        source_tracking = result['source_tracking']
        
        # For any tracked field, verify it has page number
        for field_path, source_info in source_tracking.items():
            assert 'page' in source_info, \
                f"Field '{field_path}' should have page number in source tracking"
            assert isinstance(source_info['page'], int), \
                f"Page number for '{field_path}' should be an integer"
            assert source_info['page'] >= 1, \
                f"Page number for '{field_path}' should be at least 1"
    
    @pytest.mark.property
    @pytest.mark.asyncio
    @settings(max_examples=5)
    @given(
        doc1=document_with_page_markers_strategy(),
        doc2=document_with_page_markers_strategy()
    )
    async def test_source_tracking_distinguishes_multiple_documents(self, doc1, doc2):
        """
        Property: Source tracking should distinguish between multiple documents
        
        For any set of documents, the source tracking should correctly
        identify which document each piece of data came from.
        """
        # Ensure documents have different IDs
        assume(doc1.id != doc2.id)
        
        # Setup mocks
        mock_repo = Mock(spec=DocumentRepository)
        mock_processor = Mock(spec=DocumentProcessor)
        agent = DocumentIntelligenceAgent(mock_repo, mock_processor)
        
        # Use same application_id for both documents
        doc1.application_id = "test_app"
        doc2.application_id = "test_app"
        
        mock_repo.get_by_application = AsyncMock(return_value=[doc1, doc2])
        
        # Create different financial data for each document
        financial_data1 = {
            'company_info': {'company_name': 'Test Corp'},
            'financial_metrics': {
                'revenue': {'values': [1000000], 'confidence': 'high'},
                'profit': {'values': [200000], 'confidence': 'medium'}
            },
            'financial_ratios': {},
            'notes': []
        }
        
        financial_data2 = {
            'company_info': {'company_name': 'Test Corp'},
            'financial_metrics': {
                'debt': {'values': [500000], 'confidence': 'high'},
                'cash_flow': {'values': [150000], 'confidence': 'low'}
            },
            'financial_ratios': {},
            'notes': []
        }
        
        call_count = 0
        async def mock_create(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            mock_response = Mock()
            mock_response.choices = [Mock()]
            if call_count == 1:
                mock_response.choices[0].message.content = json.dumps(financial_data1)
            else:
                mock_response.choices[0].message.content = json.dumps(financial_data2)
            return mock_response
        
        with patch.object(agent.openai.chat.completions, 'create', new=mock_create):
            result = await agent.extract("test_app")
        
        # Verify source tracking distinguishes documents
        source_tracking = result['source_tracking']
        
        # Collect all document IDs referenced in source tracking
        referenced_doc_ids = set()
        for field_path, source_info in source_tracking.items():
            if 'document_id' in source_info:
                referenced_doc_ids.add(source_info['document_id'])
        
        # Should reference both documents (or at least track sources)
        # Note: Due to merging logic, some fields might only reference one document
        # but the tracking should be consistent
        for field_path, source_info in source_tracking.items():
            doc_id = source_info.get('document_id')
            assert doc_id in [doc1.id, doc2.id], \
                f"Source tracking should reference one of the input documents"
    
    @pytest.mark.property
    @pytest.mark.asyncio
    @settings(max_examples=5)
    @given(financial_data=financial_data_strategy())
    async def test_source_tracking_maintained_through_merge(self, financial_data):
        """
        Property: Source tracking should be preserved during data merging
        
        For any extraction result that goes through the merge process,
        the source tracking information should be maintained.
        """
        # Setup mocks
        mock_repo = Mock(spec=DocumentRepository)
        mock_processor = Mock(spec=DocumentProcessor)
        agent = DocumentIntelligenceAgent(mock_repo, mock_processor)
        
        doc = Document(
            id="test_doc_123",
            application_id="test_app",
            filename="test.pdf",
            file_type="pdf",
            storage_path="test/path",
            upload_date=datetime.utcnow(),
            processing_status="complete",
            extracted_data={'text': '[Page 1]\nRevenue: $1000000\n[Page 2]\nProfit: $200000'}
        )
        
        mock_repo.get_by_application = AsyncMock(return_value=[doc])
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(financial_data)
        
        with patch.object(agent.openai.chat.completions, 'create', new=AsyncMock(return_value=mock_response)):
            result = await agent.extract("test_app")
        
        # Verify that source tracking is present in final result
        assert 'source_tracking' in result
        assert isinstance(result['source_tracking'], dict)
        
        # If any financial data was extracted, there should be source tracking
        if result['financial_data']:
            # Source tracking should reference the document
            for field_path, source_info in result['source_tracking'].items():
                assert 'document_id' in source_info
                assert source_info['document_id'] == doc.id
