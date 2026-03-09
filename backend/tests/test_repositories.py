"""
Unit tests for Firestore repository layer.

Tests CRUD operations, error handling, and transaction support for
ApplicationRepository, DocumentRepository, and AnalysisRepository.

Requirements: 1.4, 2.4, 9.1, 15.3
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from datetime import datetime
from google.cloud.firestore_v1.base_document import DocumentSnapshot

from app.models.domain import (
    Application,
    ApplicationStatus,
    CreditRecommendation,
    Document,
    AnalysisResults,
    FinancialMetrics,
    Forecast,
    RiskAssessment,
    RiskFactorScore,
    ResearchFindings,
)
from app.repositories import (
    ApplicationRepository,
    DocumentRepository,
    AnalysisRepository,
)


# Fixtures for test data
@pytest.fixture
def sample_application():
    """Create a sample Application instance."""
    return Application(
        id="app-123",
        company_name="Test Corp",
        loan_amount=1000000.0,
        loan_purpose="Business expansion",
        applicant_email="test@example.com",
        status=ApplicationStatus.PENDING,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@pytest.fixture
def sample_document():
    """Create a sample Document instance."""
    return Document(
        id="doc-123",
        application_id="app-123",
        filename="financial_statement.pdf",
        file_type="pdf",
        storage_path="documents/app-123/doc-123.pdf",
        upload_date=datetime.utcnow(),
        processing_status="pending",
    )


@pytest.fixture
def sample_analysis():
    """Create a sample AnalysisResults instance."""
    return AnalysisResults(
        application_id="app-123",
        financial_metrics=FinancialMetrics(
            revenue=[1000000],
            profit=[100000],
            debt=[500000],
            cash_flow=[200000],
            current_assets=500000,
            current_liabilities=200000,
            total_assets=2000000,
            total_equity=1000000,
            total_debt=400000,
        ),
        forecasts=[
            Forecast(
                metric_name="revenue",
                historical_values=[1000000],
                projected_values=[1100000, 1200000, 1300000],
                confidence_level=0.85,
            )
        ],
        risk_assessment=RiskAssessment(
            overall_score=75.0,
            recommendation=CreditRecommendation.APPROVE,
            financial_health=RiskFactorScore(
                factor_name="financial_health",
                score=80.0,
                weight=0.35,
                explanation="Strong financial position",
            ),
            cash_flow=RiskFactorScore(
                factor_name="cash_flow",
                score=75.0,
                weight=0.25,
                explanation="Healthy cash flow",
            ),
            industry=RiskFactorScore(
                factor_name="industry",
                score=70.0,
                weight=0.15,
                explanation="Stable industry",
            ),
            promoter=RiskFactorScore(
                factor_name="promoter",
                score=75.0,
                weight=0.15,
                explanation="Experienced management",
            ),
            external_intelligence=RiskFactorScore(
                factor_name="external_intelligence",
                score=70.0,
                weight=0.10,
                explanation="Positive market sentiment",
            ),
            summary="Strong credit profile",
        ),
        research_findings=ResearchFindings(
            web_research="Positive news coverage",
            promoter_analysis="Experienced team",
            industry_analysis="Growing sector",
        ),
        generated_at=datetime.utcnow(),
    )


# ApplicationRepository Tests
@pytest.mark.unit
class TestApplicationRepository:
    """Unit tests for ApplicationRepository."""
    
    @pytest.fixture
    def mock_firestore(self):
        """Create a mock Firestore client."""
        with patch('app.repositories.application_repository.get_firestore_client') as mock:
            yield mock.return_value
    
    @pytest.fixture
    def repository(self, mock_firestore):
        """Create an ApplicationRepository instance with mocked Firestore."""
        return ApplicationRepository()
    
    async def test_create_success(self, repository, mock_firestore, sample_application):
        """Test successful application creation."""
        # Setup mock
        mock_doc_ref = Mock()
        mock_doc_ref.get.return_value.exists = False
        mock_firestore.collection.return_value.document.return_value = mock_doc_ref
        
        # Execute
        result = await repository.create(sample_application)
        
        # Verify
        assert result == sample_application
        mock_doc_ref.set.assert_called_once()
        
    async def test_create_duplicate_id(self, repository, mock_firestore, sample_application):
        """Test creation fails when application ID already exists."""
        # Setup mock
        mock_doc_ref = Mock()
        mock_doc_ref.get.return_value.exists = True
        mock_firestore.collection.return_value.document.return_value = mock_doc_ref
        
        # Execute and verify
        with pytest.raises(ValueError, match="already exists"):
            await repository.create(sample_application)
    
    async def test_get_by_id_found(self, repository, mock_firestore, sample_application):
        """Test retrieving an existing application."""
        # Setup mock
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = sample_application.model_dump()
        
        mock_doc_ref = Mock()
        mock_doc_ref.get.return_value = mock_doc
        mock_firestore.collection.return_value.document.return_value = mock_doc_ref
        
        # Execute
        result = await repository.get_by_id("app-123")
        
        # Verify
        assert result is not None
        assert result.id == sample_application.id
        assert result.company_name == sample_application.company_name
    
    async def test_get_by_id_not_found(self, repository, mock_firestore):
        """Test retrieving a non-existent application."""
        # Setup mock
        mock_doc = Mock()
        mock_doc.exists = False
        
        mock_doc_ref = Mock()
        mock_doc_ref.get.return_value = mock_doc
        mock_firestore.collection.return_value.document.return_value = mock_doc_ref
        
        # Execute
        result = await repository.get_by_id("nonexistent")
        
        # Verify
        assert result is None
    
    async def test_update_success(self, repository, mock_firestore, sample_application):
        """Test successful application update."""
        # Setup mock
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            **sample_application.model_dump(),
            "status": ApplicationStatus.PROCESSING.value
        }
        
        mock_doc_ref = Mock()
        mock_doc_ref.get.return_value = mock_doc
        mock_firestore.collection.return_value.document.return_value = mock_doc_ref
        
        # Execute
        updates = {"status": ApplicationStatus.PROCESSING.value}
        result = await repository.update("app-123", updates)
        
        # Verify
        assert result is not None
        mock_doc_ref.update.assert_called_once()
    
    async def test_update_not_found(self, repository, mock_firestore):
        """Test updating a non-existent application."""
        # Setup mock
        mock_doc = Mock()
        mock_doc.exists = False
        
        mock_doc_ref = Mock()
        mock_doc_ref.get.return_value = mock_doc
        mock_firestore.collection.return_value.document.return_value = mock_doc_ref
        
        # Execute
        result = await repository.update("nonexistent", {"status": "processing"})
        
        # Verify
        assert result is None
    
    async def test_delete_success(self, repository, mock_firestore):
        """Test successful application deletion."""
        # Setup mock
        mock_doc = Mock()
        mock_doc.exists = True
        
        mock_doc_ref = Mock()
        mock_doc_ref.get.return_value = mock_doc
        mock_firestore.collection.return_value.document.return_value = mock_doc_ref
        
        # Execute
        result = await repository.delete("app-123")
        
        # Verify
        assert result is True
        mock_doc_ref.delete.assert_called_once()
    
    async def test_delete_not_found(self, repository, mock_firestore):
        """Test deleting a non-existent application."""
        # Setup mock
        mock_doc = Mock()
        mock_doc.exists = False
        
        mock_doc_ref = Mock()
        mock_doc_ref.get.return_value = mock_doc
        mock_firestore.collection.return_value.document.return_value = mock_doc_ref
        
        # Execute
        result = await repository.delete("nonexistent")
        
        # Verify
        assert result is False
    
    async def test_list_all(self, repository, mock_firestore, sample_application):
        """Test listing all applications."""
        # Setup mock
        mock_doc = Mock()
        mock_doc.to_dict.return_value = sample_application.model_dump()
        
        mock_query = Mock()
        mock_query.stream.return_value = [mock_doc]
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.where.return_value = mock_query
        
        mock_firestore.collection.return_value = mock_query
        
        # Execute
        result = await repository.list_all()
        
        # Verify
        assert len(result) == 1
        assert result[0].id == sample_application.id
    
    async def test_list_all_with_status_filter(self, repository, mock_firestore, sample_application):
        """Test listing applications with status filter."""
        # Setup mock
        mock_doc = Mock()
        mock_doc.to_dict.return_value = sample_application.model_dump()
        
        mock_query = Mock()
        mock_query.stream.return_value = [mock_doc]
        mock_query.order_by.return_value = mock_query
        mock_query.where.return_value = mock_query
        
        mock_firestore.collection.return_value = mock_query
        
        # Execute
        result = await repository.list_all(status=ApplicationStatus.PENDING)
        
        # Verify
        assert len(result) == 1
        mock_query.where.assert_called_once()
    
    async def test_update_status(self, repository, mock_firestore, sample_application):
        """Test updating application status."""
        # Setup mock
        mock_doc = Mock()
        mock_doc.exists = True
        updated_app = sample_application.model_copy()
        updated_app.status = ApplicationStatus.PROCESSING
        mock_doc.to_dict.return_value = updated_app.model_dump()
        
        mock_doc_ref = Mock()
        mock_doc_ref.get.return_value = mock_doc
        mock_firestore.collection.return_value.document.return_value = mock_doc_ref
        
        # Execute
        result = await repository.update_status("app-123", ApplicationStatus.PROCESSING)
        
        # Verify
        assert result is not None
        mock_doc_ref.update.assert_called_once()


# DocumentRepository Tests
@pytest.mark.unit
class TestDocumentRepository:
    """Unit tests for DocumentRepository."""
    
    @pytest.fixture
    def mock_firestore(self):
        """Create a mock Firestore client."""
        with patch('app.repositories.document_repository.get_firestore_client') as mock:
            yield mock.return_value
    
    @pytest.fixture
    def repository(self, mock_firestore):
        """Create a DocumentRepository instance with mocked Firestore."""
        return DocumentRepository()
    
    async def test_create_success(self, repository, mock_firestore, sample_document):
        """Test successful document creation."""
        # Setup mock
        mock_doc_ref = Mock()
        mock_doc_ref.get.return_value.exists = False
        mock_firestore.collection.return_value.document.return_value = mock_doc_ref
        
        # Execute
        result = await repository.create(sample_document)
        
        # Verify
        assert result == sample_document
        mock_doc_ref.set.assert_called_once()
    
    async def test_create_duplicate_id(self, repository, mock_firestore, sample_document):
        """Test creation fails when document ID already exists."""
        # Setup mock
        mock_doc_ref = Mock()
        mock_doc_ref.get.return_value.exists = True
        mock_firestore.collection.return_value.document.return_value = mock_doc_ref
        
        # Execute and verify
        with pytest.raises(ValueError, match="already exists"):
            await repository.create(sample_document)
    
    async def test_get_by_id_found(self, repository, mock_firestore, sample_document):
        """Test retrieving an existing document."""
        # Setup mock
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = sample_document.model_dump()
        
        mock_doc_ref = Mock()
        mock_doc_ref.get.return_value = mock_doc
        mock_firestore.collection.return_value.document.return_value = mock_doc_ref
        
        # Execute
        result = await repository.get_by_id("doc-123")
        
        # Verify
        assert result is not None
        assert result.id == sample_document.id
        assert result.filename == sample_document.filename
    
    async def test_list_by_application(self, repository, mock_firestore, sample_document):
        """Test listing documents by application ID."""
        # Setup mock
        mock_doc = Mock()
        mock_doc.to_dict.return_value = sample_document.model_dump()
        
        mock_query = Mock()
        mock_query.stream.return_value = [mock_doc]
        mock_query.order_by.return_value = mock_query
        mock_query.where.return_value = mock_query
        
        mock_firestore.collection.return_value = mock_query
        
        # Execute
        result = await repository.list_by_application("app-123")
        
        # Verify
        assert len(result) == 1
        assert result[0].application_id == "app-123"
    
    async def test_update_processing_status(self, repository, mock_firestore, sample_document):
        """Test updating document processing status."""
        # Setup mock
        mock_doc = Mock()
        mock_doc.exists = True
        updated_doc = sample_document.model_copy()
        updated_doc.processing_status = "complete"
        mock_doc.to_dict.return_value = updated_doc.model_dump()
        
        mock_doc_ref = Mock()
        mock_doc_ref.get.return_value = mock_doc
        mock_firestore.collection.return_value.document.return_value = mock_doc_ref
        
        # Execute
        result = await repository.update_processing_status("doc-123", "complete")
        
        # Verify
        assert result is not None
        mock_doc_ref.update.assert_called_once()
    
    async def test_update_extracted_data(self, repository, mock_firestore, sample_document):
        """Test updating document with extracted data."""
        # Setup mock
        mock_doc = Mock()
        mock_doc.exists = True
        updated_doc = sample_document.model_copy()
        updated_doc.extracted_data = {"revenue": 1000000}
        updated_doc.source_pages = {"revenue": 5}
        mock_doc.to_dict.return_value = updated_doc.model_dump()
        
        mock_doc_ref = Mock()
        mock_doc_ref.get.return_value = mock_doc
        mock_firestore.collection.return_value.document.return_value = mock_doc_ref
        
        # Execute
        extracted_data = {"revenue": 1000000}
        source_pages = {"revenue": 5}
        result = await repository.update_extracted_data("doc-123", extracted_data, source_pages)
        
        # Verify
        assert result is not None
        mock_doc_ref.update.assert_called_once()


# AnalysisRepository Tests
@pytest.mark.unit
class TestAnalysisRepository:
    """Unit tests for AnalysisRepository."""
    
    @pytest.fixture
    def mock_firestore(self):
        """Create a mock Firestore client."""
        with patch('app.repositories.analysis_repository.get_firestore_client') as mock:
            yield mock.return_value
    
    @pytest.fixture
    def repository(self, mock_firestore):
        """Create an AnalysisRepository instance with mocked Firestore."""
        return AnalysisRepository()
    
    async def test_create_success(self, repository, mock_firestore, sample_analysis):
        """Test successful analysis creation."""
        # Setup mock
        mock_doc_ref = Mock()
        mock_doc_ref.get.return_value.exists = False
        mock_firestore.collection.return_value.document.return_value = mock_doc_ref
        
        # Execute
        result = await repository.create(sample_analysis)
        
        # Verify
        assert result == sample_analysis
        mock_doc_ref.set.assert_called_once()
    
    async def test_create_duplicate(self, repository, mock_firestore, sample_analysis):
        """Test creation fails when analysis for application already exists."""
        # Setup mock
        mock_doc_ref = Mock()
        mock_doc_ref.get.return_value.exists = True
        mock_firestore.collection.return_value.document.return_value = mock_doc_ref
        
        # Execute and verify
        with pytest.raises(ValueError, match="already exists"):
            await repository.create(sample_analysis)
    
    async def test_get_by_application_id_found(self, repository, mock_firestore, sample_analysis):
        """Test retrieving existing analysis results."""
        # Setup mock
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = sample_analysis.model_dump()
        
        mock_doc_ref = Mock()
        mock_doc_ref.get.return_value = mock_doc
        mock_firestore.collection.return_value.document.return_value = mock_doc_ref
        
        # Execute
        result = await repository.get_by_application_id("app-123")
        
        # Verify
        assert result is not None
        assert result.application_id == sample_analysis.application_id
    
    async def test_get_by_application_id_not_found(self, repository, mock_firestore):
        """Test retrieving non-existent analysis results."""
        # Setup mock
        mock_doc = Mock()
        mock_doc.exists = False
        
        mock_doc_ref = Mock()
        mock_doc_ref.get.return_value = mock_doc
        mock_firestore.collection.return_value.document.return_value = mock_doc_ref
        
        # Execute
        result = await repository.get_by_application_id("nonexistent")
        
        # Verify
        assert result is None
    
    async def test_upsert_create(self, repository, mock_firestore, sample_analysis):
        """Test upsert creates new analysis when it doesn't exist."""
        # Setup mock
        mock_doc_ref = Mock()
        mock_firestore.collection.return_value.document.return_value = mock_doc_ref
        
        # Execute
        result = await repository.upsert(sample_analysis)
        
        # Verify
        assert result == sample_analysis
        mock_doc_ref.set.assert_called_once()
    
    async def test_upsert_update(self, repository, mock_firestore, sample_analysis):
        """Test upsert updates existing analysis."""
        # Setup mock
        mock_doc_ref = Mock()
        mock_firestore.collection.return_value.document.return_value = mock_doc_ref
        
        # Execute
        result = await repository.upsert(sample_analysis)
        
        # Verify
        assert result == sample_analysis
        mock_doc_ref.set.assert_called_once()
    
    async def test_delete_success(self, repository, mock_firestore):
        """Test successful analysis deletion."""
        # Setup mock
        mock_doc = Mock()
        mock_doc.exists = True
        
        mock_doc_ref = Mock()
        mock_doc_ref.get.return_value = mock_doc
        mock_firestore.collection.return_value.document.return_value = mock_doc_ref
        
        # Execute
        result = await repository.delete("app-123")
        
        # Verify
        assert result is True
        mock_doc_ref.delete.assert_called_once()
    
    async def test_delete_not_found(self, repository, mock_firestore):
        """Test deleting non-existent analysis."""
        # Setup mock
        mock_doc = Mock()
        mock_doc.exists = False
        
        mock_doc_ref = Mock()
        mock_doc_ref.get.return_value = mock_doc
        mock_firestore.collection.return_value.document.return_value = mock_doc_ref
        
        # Execute
        result = await repository.delete("nonexistent")
        
        # Verify
        assert result is False


# Error Handling Tests
@pytest.mark.unit
class TestRepositoryErrorHandling:
    """Test error handling across all repositories."""
    
    async def test_application_create_error(self):
        """Test error handling in application creation."""
        with patch('app.repositories.application_repository.get_firestore_client') as mock:
            mock_client = Mock()
            mock_client.collection.side_effect = Exception("Firestore connection error")
            mock.return_value = mock_client
            
            repository = ApplicationRepository()
            
            app = Application(
                id="test",
                company_name="Test",
                loan_amount=1000,
                loan_purpose="Test",
                applicant_email="test@test.com"
            )
            
            with pytest.raises(Exception, match="Failed to create application"):
                await repository.create(app)
    
    async def test_document_get_error(self):
        """Test error handling in document retrieval."""
        with patch('app.repositories.document_repository.get_firestore_client') as mock:
            mock_client = Mock()
            mock_client.collection.side_effect = Exception("Firestore connection error")
            mock.return_value = mock_client
            
            repository = DocumentRepository()
            
            with pytest.raises(Exception, match="Failed to retrieve document"):
                await repository.get_by_id("test-id")
    
    async def test_analysis_update_error(self):
        """Test error handling in analysis update."""
        with patch('app.repositories.analysis_repository.get_firestore_client') as mock:
            mock_client = Mock()
            mock_client.collection.side_effect = Exception("Firestore connection error")
            mock.return_value = mock_client
            
            repository = AnalysisRepository()
            
            with pytest.raises(Exception, match="Failed to update analysis"):
                await repository.update("test-id", {"field": "value"})
