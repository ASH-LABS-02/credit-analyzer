"""
Property-based tests for Firestore repository round-trip operations.

These tests validate that data can be stored and retrieved correctly,
maintaining integrity across the persistence layer.

Feature: intelli-credit-platform
Requirements: 1.4, 2.4
"""

import pytest
from hypothesis import given, strategies as st, settings
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from typing import Dict, Any

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


# Custom strategies for generating test data
@st.composite
def application_strategy(draw):
    """Generate valid Application instances."""
    return Application(
        id=draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_'))),
        company_name=draw(st.text(min_size=1, max_size=100)),
        loan_amount=draw(st.floats(min_value=1000, max_value=100000000)),
        loan_purpose=draw(st.text(min_size=1, max_size=200)),
        applicant_email=draw(st.emails()),
        status=draw(st.sampled_from(list(ApplicationStatus))),
        created_at=draw(st.datetimes(min_value=datetime(2020, 1, 1), max_value=datetime(2024, 12, 31))),
        updated_at=draw(st.datetimes(min_value=datetime(2020, 1, 1), max_value=datetime(2024, 12, 31))),
        credit_score=draw(st.none() | st.floats(min_value=0, max_value=100)),
        recommendation=draw(st.none() | st.sampled_from(list(CreditRecommendation))),
    )


@st.composite
def document_strategy(draw):
    """Generate valid Document instances."""
    file_types = ['pdf', 'docx', 'xlsx', 'csv', 'jpg', 'png']
    app_id = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_')))
    doc_id = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_')))
    file_type = draw(st.sampled_from(file_types))
    
    return Document(
        id=doc_id,
        application_id=app_id,
        filename=draw(st.text(min_size=1, max_size=100)) + f'.{file_type}',
        file_type=file_type,
        storage_path=f'documents/{app_id}/{doc_id}.{file_type}',
        upload_date=draw(st.datetimes(min_value=datetime(2020, 1, 1), max_value=datetime(2024, 12, 31))),
        processing_status=draw(st.sampled_from(['pending', 'processing', 'complete', 'failed'])),
        extracted_data=draw(st.none() | st.dictionaries(
            keys=st.text(min_size=1, max_size=20),
            values=st.one_of(
                st.floats(allow_nan=False, allow_infinity=False),
                st.integers(),
                st.text(max_size=100)
            ),
            min_size=0,
            max_size=10
        )),
        source_pages=draw(st.none() | st.dictionaries(
            keys=st.text(min_size=1, max_size=20),
            values=st.integers(min_value=1, max_value=1000),
            min_size=0,
            max_size=10
        )),
    )


@st.composite
def financial_metrics_strategy(draw):
    """Generate valid FinancialMetrics instances."""
    num_years = draw(st.integers(min_value=1, max_value=5))
    
    return FinancialMetrics(
        revenue=draw(st.lists(st.floats(min_value=0, max_value=1e9), min_size=num_years, max_size=num_years)),
        profit=draw(st.lists(st.floats(min_value=-1e8, max_value=1e9), min_size=num_years, max_size=num_years)),
        debt=draw(st.lists(st.floats(min_value=0, max_value=1e9), min_size=num_years, max_size=num_years)),
        cash_flow=draw(st.lists(st.floats(min_value=-1e8, max_value=1e9), min_size=num_years, max_size=num_years)),
        current_assets=draw(st.floats(min_value=0, max_value=1e9)),
        current_liabilities=draw(st.floats(min_value=0, max_value=1e9)),
        total_assets=draw(st.floats(min_value=0, max_value=1e10)),
        total_equity=draw(st.floats(min_value=-1e9, max_value=1e10)),
        total_debt=draw(st.floats(min_value=0, max_value=1e9)),
        current_ratio=draw(st.none() | st.floats(min_value=0, max_value=10)),
        debt_to_equity=draw(st.none() | st.floats(min_value=0, max_value=10)),
        net_profit_margin=draw(st.none() | st.floats(min_value=-1, max_value=1)),
        roe=draw(st.none() | st.floats(min_value=-1, max_value=1)),
        asset_turnover=draw(st.none() | st.floats(min_value=0, max_value=10)),
        revenue_growth=draw(st.none() | st.lists(st.floats(min_value=-1, max_value=10), min_size=0, max_size=num_years-1)),
        profit_growth=draw(st.none() | st.lists(st.floats(min_value=-1, max_value=10), min_size=0, max_size=num_years-1)),
    )


@st.composite
def analysis_results_strategy(draw):
    """Generate valid AnalysisResults instances."""
    app_id = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_')))
    
    # Generate risk factor scores with correct weights
    financial_health = RiskFactorScore(
        factor_name="financial_health",
        score=draw(st.floats(min_value=0, max_value=100)),
        weight=0.35,
        explanation=draw(st.text(min_size=1, max_size=200)),
        key_findings=draw(st.lists(st.text(min_size=1, max_size=100), min_size=0, max_size=5))
    )
    
    cash_flow = RiskFactorScore(
        factor_name="cash_flow",
        score=draw(st.floats(min_value=0, max_value=100)),
        weight=0.25,
        explanation=draw(st.text(min_size=1, max_size=200)),
        key_findings=draw(st.lists(st.text(min_size=1, max_size=100), min_size=0, max_size=5))
    )
    
    industry = RiskFactorScore(
        factor_name="industry",
        score=draw(st.floats(min_value=0, max_value=100)),
        weight=0.15,
        explanation=draw(st.text(min_size=1, max_size=200)),
        key_findings=draw(st.lists(st.text(min_size=1, max_size=100), min_size=0, max_size=5))
    )
    
    promoter = RiskFactorScore(
        factor_name="promoter",
        score=draw(st.floats(min_value=0, max_value=100)),
        weight=0.15,
        explanation=draw(st.text(min_size=1, max_size=200)),
        key_findings=draw(st.lists(st.text(min_size=1, max_size=100), min_size=0, max_size=5))
    )
    
    external_intelligence = RiskFactorScore(
        factor_name="external_intelligence",
        score=draw(st.floats(min_value=0, max_value=100)),
        weight=0.10,
        explanation=draw(st.text(min_size=1, max_size=200)),
        key_findings=draw(st.lists(st.text(min_size=1, max_size=100), min_size=0, max_size=5))
    )
    
    risk_assessment = RiskAssessment(
        overall_score=draw(st.floats(min_value=0, max_value=100)),
        recommendation=draw(st.sampled_from(list(CreditRecommendation))),
        financial_health=financial_health,
        cash_flow=cash_flow,
        industry=industry,
        promoter=promoter,
        external_intelligence=external_intelligence,
        summary=draw(st.text(min_size=1, max_size=500))
    )
    
    return AnalysisResults(
        application_id=app_id,
        financial_metrics=draw(financial_metrics_strategy()),
        forecasts=draw(st.lists(
            st.builds(
                Forecast,
                metric_name=st.text(min_size=1, max_size=50),
                historical_values=st.lists(st.floats(min_value=0, max_value=1e9), min_size=1, max_size=5),
                projected_values=st.lists(st.floats(min_value=0, max_value=1e9), min_size=3, max_size=3),
                confidence_level=st.floats(min_value=0, max_value=1),
                assumptions=st.lists(st.text(min_size=1, max_size=100), min_size=0, max_size=5)
            ),
            min_size=1,
            max_size=5
        )),
        risk_assessment=risk_assessment,
        research_findings=ResearchFindings(
            web_research=draw(st.text(min_size=1, max_size=500)),
            promoter_analysis=draw(st.text(min_size=1, max_size=500)),
            industry_analysis=draw(st.text(min_size=1, max_size=500)),
            sources=draw(st.lists(st.text(min_size=1, max_size=200), min_size=0, max_size=10)),
            red_flags=draw(st.lists(st.text(min_size=1, max_size=100), min_size=0, max_size=5)),
            positive_indicators=draw(st.lists(st.text(min_size=1, max_size=100), min_size=0, max_size=5))
        ),
        generated_at=draw(st.datetimes(min_value=datetime(2020, 1, 1), max_value=datetime(2024, 12, 31)))
    )


# Property 1: Document Upload Round-Trip Integrity
# **Validates: Requirements 1.4, 2.4**
@pytest.mark.property
@settings(max_examples=5)
@given(document=document_strategy())
def test_document_round_trip_integrity(document):
    """
    Property 1: Document Upload Round-Trip Integrity
    
    For any valid document (PDF, DOCX, Excel, CSV, or image format) uploaded to an application,
    the document should be stored in Firestore and retrievable with the same content and
    associated with the correct application identifier.
    
    **Validates: Requirements 1.4, 2.4**
    """
    with patch('app.repositories.document_repository.get_firestore_client') as mock_firestore:
        # Setup mock Firestore client
        mock_client = Mock()
        mock_firestore.return_value = mock_client
        
        # Mock document reference for create operation
        mock_doc_ref = Mock()
        mock_doc_ref.get.return_value.exists = False  # Document doesn't exist yet
        mock_client.collection.return_value.document.return_value = mock_doc_ref
        
        # Create repository and store document
        repository = DocumentRepository()
        
        # Store the document
        created_doc = None
        try:
            import asyncio
            created_doc = asyncio.run(repository.create(document))
        except Exception as e:
            pytest.fail(f"Failed to create document: {e}")
        
        # Verify document was created
        assert created_doc is not None
        assert created_doc.id == document.id
        assert created_doc.application_id == document.application_id
        assert created_doc.filename == document.filename
        assert created_doc.file_type == document.file_type
        assert created_doc.storage_path == document.storage_path
        
        # Mock document reference for get operation
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = document.model_dump()
        mock_doc_ref.get.return_value = mock_doc
        
        # Retrieve the document
        retrieved_doc = None
        try:
            retrieved_doc = asyncio.run(repository.get_by_id(document.id))
        except Exception as e:
            pytest.fail(f"Failed to retrieve document: {e}")
        
        # Verify round-trip integrity
        assert retrieved_doc is not None, "Document should be retrievable after creation"
        assert retrieved_doc.id == document.id, "Document ID should match"
        assert retrieved_doc.application_id == document.application_id, "Application ID should match"
        assert retrieved_doc.filename == document.filename, "Filename should match"
        assert retrieved_doc.file_type == document.file_type, "File type should match"
        assert retrieved_doc.storage_path == document.storage_path, "Storage path should match"
        assert retrieved_doc.processing_status == document.processing_status, "Processing status should match"
        
        # Verify extracted data if present
        if document.extracted_data is not None:
            assert retrieved_doc.extracted_data == document.extracted_data, "Extracted data should match"
        
        # Verify source pages if present
        if document.source_pages is not None:
            assert retrieved_doc.source_pages == document.source_pages, "Source pages should match"


# Property 5: Extracted Data Persistence
# **Validates: Requirements 2.4**
@pytest.mark.property
@settings(max_examples=5)
@given(
    document=document_strategy(),
    extracted_data=st.dictionaries(
        keys=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'), whitelist_characters='_')),
        values=st.one_of(
            st.floats(min_value=-1e9, max_value=1e9, allow_nan=False, allow_infinity=False),
            st.integers(min_value=-1000000, max_value=1000000),
            st.text(min_size=0, max_size=100)
        ),
        min_size=1,
        max_size=20
    ),
    source_pages=st.dictionaries(
        keys=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'), whitelist_characters='_')),
        values=st.integers(min_value=1, max_value=1000),
        min_size=1,
        max_size=20
    )
)
def test_extracted_data_persistence(document, extracted_data, source_pages):
    """
    Property 5: Extracted Data Persistence
    
    For any completed extraction, the structured data should be persisted to Firestore
    with the correct document reference, and retrieving the data should return the
    same structured values.
    
    **Validates: Requirements 2.4**
    """
    with patch('app.repositories.document_repository.get_firestore_client') as mock_firestore:
        # Setup mock Firestore client
        mock_client = Mock()
        mock_firestore.return_value = mock_client
        
        # Mock document reference
        mock_doc_ref = Mock()
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc_ref.get.return_value = mock_doc
        mock_client.collection.return_value.document.return_value = mock_doc_ref
        
        # Create repository
        repository = DocumentRepository()
        
        # Update document with extracted data
        updated_doc = None
        try:
            import asyncio
            
            # First, mock the document to exist
            mock_doc.to_dict.return_value = document.model_dump()
            
            # Update with extracted data
            updated_doc = asyncio.run(
                repository.update_extracted_data(document.id, extracted_data, source_pages)
            )
        except Exception as e:
            pytest.fail(f"Failed to update extracted data: {e}")
        
        # Verify update was called
        assert mock_doc_ref.update.called, "Update should be called on Firestore"
        
        # Mock the retrieval to return updated document
        updated_doc_dict = document.model_dump()
        updated_doc_dict['extracted_data'] = extracted_data
        updated_doc_dict['source_pages'] = source_pages
        updated_doc_dict['processing_status'] = 'complete'
        mock_doc.to_dict.return_value = updated_doc_dict
        
        # Retrieve the document
        retrieved_doc = None
        try:
            import asyncio
            retrieved_doc = asyncio.run(repository.get_by_id(document.id))
        except Exception as e:
            pytest.fail(f"Failed to retrieve document after extraction: {e}")
        
        # Verify extracted data persistence
        assert retrieved_doc is not None, "Document should be retrievable after extraction"
        assert retrieved_doc.extracted_data is not None, "Extracted data should be present"
        assert retrieved_doc.extracted_data == extracted_data, "Extracted data should match exactly"
        
        # Verify source pages persistence
        assert retrieved_doc.source_pages is not None, "Source pages should be present"
        assert retrieved_doc.source_pages == source_pages, "Source pages should match exactly"
        
        # Verify processing status was updated
        assert retrieved_doc.processing_status == 'complete', "Processing status should be 'complete'"
        
        # Verify document reference is maintained
        assert retrieved_doc.id == document.id, "Document ID should be preserved"
        assert retrieved_doc.application_id == document.application_id, "Application ID should be preserved"


# Additional property test: Application round-trip integrity
@pytest.mark.property
@settings(max_examples=5)
@given(application=application_strategy())
def test_application_round_trip_integrity(application):
    """
    Additional property test for Application round-trip integrity.
    
    For any valid application, it should be stored and retrievable with the same data.
    
    **Validates: Requirements 1.4, 2.4**
    """
    with patch('app.repositories.application_repository.get_firestore_client') as mock_firestore:
        # Setup mock Firestore client
        mock_client = Mock()
        mock_firestore.return_value = mock_client
        
        # Mock document reference for create operation
        mock_doc_ref = Mock()
        mock_doc_ref.get.return_value.exists = False
        mock_client.collection.return_value.document.return_value = mock_doc_ref
        
        # Create repository and store application
        repository = ApplicationRepository()
        
        created_app = None
        try:
            import asyncio
            created_app = asyncio.run(repository.create(application))
        except Exception as e:
            pytest.fail(f"Failed to create application: {e}")
        
        # Verify application was created
        assert created_app is not None
        assert created_app.id == application.id
        
        # Mock document reference for get operation
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = application.model_dump()
        mock_doc_ref.get.return_value = mock_doc
        
        # Retrieve the application
        retrieved_app = None
        try:
            retrieved_app = asyncio.run(repository.get_by_id(application.id))
        except Exception as e:
            pytest.fail(f"Failed to retrieve application: {e}")
        
        # Verify round-trip integrity
        assert retrieved_app is not None, "Application should be retrievable"
        assert retrieved_app.id == application.id, "Application ID should match"
        assert retrieved_app.company_name == application.company_name, "Company name should match"
        assert retrieved_app.loan_amount == application.loan_amount, "Loan amount should match"
        assert retrieved_app.loan_purpose == application.loan_purpose, "Loan purpose should match"
        assert retrieved_app.applicant_email == application.applicant_email, "Email should match"
        assert retrieved_app.status == application.status, "Status should match"
        
        # Verify optional fields
        if application.credit_score is not None:
            assert retrieved_app.credit_score == application.credit_score, "Credit score should match"
        if application.recommendation is not None:
            assert retrieved_app.recommendation == application.recommendation, "Recommendation should match"


# Additional property test: Analysis results round-trip integrity
@pytest.mark.property
@settings(max_examples=5)
@given(analysis=analysis_results_strategy())
def test_analysis_results_round_trip_integrity(analysis):
    """
    Additional property test for AnalysisResults round-trip integrity.
    
    For any valid analysis results, they should be stored and retrievable with the same data.
    
    **Validates: Requirements 2.4**
    """
    with patch('app.repositories.analysis_repository.get_firestore_client') as mock_firestore:
        # Setup mock Firestore client
        mock_client = Mock()
        mock_firestore.return_value = mock_client
        
        # Mock document reference for create operation
        mock_doc_ref = Mock()
        mock_doc_ref.get.return_value.exists = False
        mock_client.collection.return_value.document.return_value = mock_doc_ref
        
        # Create repository and store analysis
        repository = AnalysisRepository()
        
        created_analysis = None
        try:
            import asyncio
            created_analysis = asyncio.run(repository.create(analysis))
        except Exception as e:
            pytest.fail(f"Failed to create analysis: {e}")
        
        # Verify analysis was created
        assert created_analysis is not None
        assert created_analysis.application_id == analysis.application_id
        
        # Mock document reference for get operation
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = analysis.model_dump()
        mock_doc_ref.get.return_value = mock_doc
        
        # Retrieve the analysis
        retrieved_analysis = None
        try:
            retrieved_analysis = asyncio.run(repository.get_by_application_id(analysis.application_id))
        except Exception as e:
            pytest.fail(f"Failed to retrieve analysis: {e}")
        
        # Verify round-trip integrity
        assert retrieved_analysis is not None, "Analysis should be retrievable"
        assert retrieved_analysis.application_id == analysis.application_id, "Application ID should match"
        
        # Verify financial metrics
        assert retrieved_analysis.financial_metrics.revenue == analysis.financial_metrics.revenue, "Revenue should match"
        assert retrieved_analysis.financial_metrics.profit == analysis.financial_metrics.profit, "Profit should match"
        assert retrieved_analysis.financial_metrics.debt == analysis.financial_metrics.debt, "Debt should match"
        assert retrieved_analysis.financial_metrics.cash_flow == analysis.financial_metrics.cash_flow, "Cash flow should match"
        
        # Verify risk assessment
        assert retrieved_analysis.risk_assessment.overall_score == analysis.risk_assessment.overall_score, "Overall score should match"
        assert retrieved_analysis.risk_assessment.recommendation == analysis.risk_assessment.recommendation, "Recommendation should match"
        
        # Verify forecasts
        assert len(retrieved_analysis.forecasts) == len(analysis.forecasts), "Number of forecasts should match"
        
        # Verify research findings
        assert retrieved_analysis.research_findings.web_research == analysis.research_findings.web_research, "Web research should match"
        assert retrieved_analysis.research_findings.promoter_analysis == analysis.research_findings.promoter_analysis, "Promoter analysis should match"
        assert retrieved_analysis.research_findings.industry_analysis == analysis.research_findings.industry_analysis, "Industry analysis should match"
