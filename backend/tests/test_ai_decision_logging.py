"""
Unit tests for AI decision logging integration across all agents.

This test file verifies that all AI agents properly log their decisions
to the audit trail when an audit logger is provided.

Requirements: 17.2
Property 36: AI Decision Logging
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.agents.document_intelligence_agent import DocumentIntelligenceAgent
from app.agents.financial_analysis_agent import FinancialAnalysisAgent
from app.agents.web_research_agent import WebResearchAgent
from app.agents.promoter_intelligence_agent import PromoterIntelligenceAgent
from app.agents.industry_intelligence_agent import IndustryIntelligenceAgent
from app.agents.forecasting_agent import ForecastingAgent
from app.agents.risk_scoring_agent import RiskScoringAgent
from app.agents.cam_generator_agent import CAMGeneratorAgent
from app.core.audit_logger import AuditLogger
from app.models.domain import (
    Document, ApplicationStatus, CreditRecommendation,
    RiskFactorScore, RiskAssessment, CAM
)


@pytest.mark.asyncio
async def test_document_intelligence_agent_logs_decision():
    """Test that DocumentIntelligenceAgent logs AI decisions."""
    # Setup
    mock_audit_logger = AsyncMock(spec=AuditLogger)
    mock_doc_repo = AsyncMock()
    mock_doc_processor = MagicMock()
    
    # Create mock documents
    mock_doc = Document(
        id='doc123',
        application_id='app123',
        filename='test.pdf',
        file_type='pdf',
        storage_path='/path/to/doc',
        upload_date=datetime.utcnow(),
        processing_status='complete',
        extracted_data={'text': 'Sample financial data'}
    )
    mock_doc_repo.get_by_application.return_value = [mock_doc]
    
    agent = DocumentIntelligenceAgent(
        mock_doc_repo,
        mock_doc_processor,
        mock_audit_logger
    )
    
    # Execute
    result = await agent.extract('app123')
    
    # Verify
    assert mock_audit_logger.log_ai_decision.called
    call_args = mock_audit_logger.log_ai_decision.call_args
    assert call_args[1]['agent_name'] == 'DocumentIntelligenceAgent'
    assert call_args[1]['application_id'] == 'app123'
    assert 'decision' in call_args[1]
    assert 'reasoning' in call_args[1]
    assert 'data_sources' in call_args[1]


@pytest.mark.asyncio
async def test_financial_analysis_agent_logs_decision():
    """Test that FinancialAnalysisAgent logs AI decisions."""
    # Setup
    mock_audit_logger = AsyncMock(spec=AuditLogger)
    agent = FinancialAnalysisAgent(mock_audit_logger)
    
    # Mock extracted data
    extracted_data = {
        'application_id': 'app123',
        'financial_data': {
            'financial_metrics': {
                'revenue': {'values': [1000000, 1200000], 'years': ['2022', '2023']},
                'profit': {'values': [100000, 120000], 'years': ['2022', '2023']},
                'current_assets': {'value': 500000},
                'current_liabilities': {'value': 300000},
                'total_assets': {'value': 2000000},
                'total_equity': {'value': 1000000},
                'total_debt': {'value': 500000}
            }
        }
    }
    
    # Execute
    result = await agent.analyze(extracted_data)
    
    # Verify
    assert mock_audit_logger.log_ai_decision.called
    call_args = mock_audit_logger.log_ai_decision.call_args
    assert call_args[1]['agent_name'] == 'FinancialAnalysisAgent'
    assert call_args[1]['application_id'] == 'app123'
    assert 'ratios_calculated' in call_args[1]['additional_details']


@pytest.mark.asyncio
async def test_web_research_agent_logs_decision():
    """Test that WebResearchAgent logs AI decisions."""
    # Setup
    mock_audit_logger = AsyncMock(spec=AuditLogger)
    agent = WebResearchAgent(mock_audit_logger)
    
    # Execute
    with patch.object(agent, '_gather_news', return_value=[]):
        with patch.object(agent, '_identify_red_flags', return_value=[]):
            with patch.object(agent, '_identify_positive_indicators', return_value=[]):
                with patch.object(agent, '_generate_research_summary', return_value='Test summary'):
                    result = await agent.research(
                        'Test Company',
                        {'application_id': 'app123'}
                    )
    
    # Verify
    assert mock_audit_logger.log_ai_decision.called
    call_args = mock_audit_logger.log_ai_decision.call_args
    assert call_args[1]['agent_name'] == 'WebResearchAgent'
    assert call_args[1]['application_id'] == 'app123'


@pytest.mark.asyncio
async def test_risk_scoring_agent_logs_decision():
    """Test that RiskScoringAgent logs AI decisions."""
    # Setup
    mock_audit_logger = AsyncMock(spec=AuditLogger)
    agent = RiskScoringAgent(mock_audit_logger)
    
    # Mock analysis data
    analysis_data = {
        'application_id': 'app123',
        'financial': {
            'ratios': {'current_ratio': {'value': 2.0}},
            'benchmarks': {},
            'trends': {}
        },
        'forecasts': {},
        'research': {
            'web': {},
            'promoter': {},
            'industry': {}
        }
    }
    
    # Execute
    result = await agent.score(analysis_data)
    
    # Verify
    assert mock_audit_logger.log_ai_decision.called
    call_args = mock_audit_logger.log_ai_decision.call_args
    assert call_args[1]['agent_name'] == 'RiskScoringAgent'
    assert call_args[1]['application_id'] == 'app123'
    assert 'overall_score' in call_args[1]['additional_details']
    assert 'recommendation' in call_args[1]['additional_details']


@pytest.mark.asyncio
async def test_forecasting_agent_logs_decision():
    """Test that ForecastingAgent logs AI decisions."""
    # Setup
    mock_audit_logger = AsyncMock(spec=AuditLogger)
    agent = ForecastingAgent(mock_audit_logger)
    
    # Mock financial data
    financial_data = {
        'application_id': 'app123',
        'historical': {
            'revenue': {'values': [1000000, 1200000, 1400000], 'years': ['2021', '2022', '2023']},
            'profit': {'values': [100000, 120000, 140000], 'years': ['2021', '2022', '2023']}
        }
    }
    
    # Execute
    result = await agent.predict(financial_data)
    
    # Verify
    assert mock_audit_logger.log_ai_decision.called
    call_args = mock_audit_logger.log_ai_decision.call_args
    assert call_args[1]['agent_name'] == 'ForecastingAgent'
    assert call_args[1]['application_id'] == 'app123'
    assert 'forecasted_metrics' in call_args[1]['additional_details']


@pytest.mark.asyncio
async def test_cam_generator_agent_logs_decision():
    """Test that CAMGeneratorAgent logs AI decisions."""
    # Setup
    mock_audit_logger = AsyncMock(spec=AuditLogger)
    agent = CAMGeneratorAgent(mock_audit_logger)
    
    # Mock analysis data
    analysis_data = {
        'application_id': 'app123',
        'company_name': 'Test Company',
        'loan_amount': 1000000,
        'loan_purpose': 'Working capital',
        'financial': {'summary': 'Good financial health'},
        'forecasts': {},
        'risk': {
            'overall_score': 75,
            'recommendation': CreditRecommendation.APPROVE,
            'summary': 'Strong credit profile'
        },
        'research': {},
        'version': 1
    }
    
    # Execute
    result = await agent.generate(analysis_data)
    
    # Verify
    assert mock_audit_logger.log_ai_decision.called
    call_args = mock_audit_logger.log_ai_decision.call_args
    assert call_args[1]['agent_name'] == 'CAMGeneratorAgent'
    assert call_args[1]['application_id'] == 'app123'
    assert 'version' in call_args[1]['additional_details']
    assert 'sections' in call_args[1]['additional_details']


@pytest.mark.asyncio
async def test_agents_work_without_audit_logger():
    """Test that agents work correctly when audit_logger is None."""
    # Setup agents without audit logger
    mock_doc_repo = AsyncMock()
    mock_doc_processor = MagicMock()
    mock_doc_repo.get_by_application.return_value = []
    
    doc_agent = DocumentIntelligenceAgent(mock_doc_repo, mock_doc_processor, None)
    financial_agent = FinancialAnalysisAgent(None)
    web_agent = WebResearchAgent(None)
    risk_agent = RiskScoringAgent(None)
    
    # Execute - should not raise errors
    doc_result = await doc_agent.extract('app123')
    assert doc_result is not None
    
    financial_result = await financial_agent.analyze({'financial_data': {}})
    assert financial_result is not None
    
    # These should work without errors even without audit logger
    assert doc_agent.audit_logger is None
    assert financial_agent.audit_logger is None
    assert web_agent.audit_logger is None
    assert risk_agent.audit_logger is None


@pytest.mark.asyncio
async def test_audit_logging_includes_required_fields():
    """Test that all AI decision logs include required fields."""
    # Setup
    mock_audit_logger = AsyncMock(spec=AuditLogger)
    agent = FinancialAnalysisAgent(mock_audit_logger)
    
    # Execute
    extracted_data = {
        'application_id': 'app123',
        'financial_data': {
            'financial_metrics': {
                'current_assets': {'value': 500000},
                'current_liabilities': {'value': 300000}
            }
        }
    }
    await agent.analyze(extracted_data)
    
    # Verify required fields
    call_args = mock_audit_logger.log_ai_decision.call_args[1]
    
    # Check all required fields are present
    assert 'agent_name' in call_args
    assert 'application_id' in call_args
    assert 'decision' in call_args
    assert 'reasoning' in call_args
    assert 'data_sources' in call_args
    
    # Check types
    assert isinstance(call_args['agent_name'], str)
    assert isinstance(call_args['application_id'], str)
    assert isinstance(call_args['decision'], str)
    assert isinstance(call_args['reasoning'], str)
    assert isinstance(call_args['data_sources'], list)
    
    # Check additional_details is a dict
    if 'additional_details' in call_args:
        assert isinstance(call_args['additional_details'], dict)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
