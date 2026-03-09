"""
Tests for CAMGeneratorAgent

This module tests the CAM generation functionality including:
- CAM document structure generation
- Section generation (executive summary, company overview, financial analysis, risk assessment, recommendation)
- Professional formatting with tables
- Version tracking and timestamps
"""

import pytest
from datetime import datetime
from app.agents.cam_generator_agent import CAMGeneratorAgent
from app.models.domain import CAM, CreditRecommendation


@pytest.mark.asyncio
class TestCAMGeneratorAgent:
    """Test suite for CAMGeneratorAgent"""
    
    @pytest.fixture
    def agent(self):
        """Create a CAMGeneratorAgent instance"""
        return CAMGeneratorAgent()
    
    @pytest.fixture
    def sample_analysis_data(self):
        """Sample analysis data for CAM generation"""
        return {
            'application_id': 'test-app-123',
            'company_name': 'TechCorp Industries',
            'loan_amount': 5000000.0,
            'loan_purpose': 'Working capital and expansion',
            'financial': {
                'ratios': {
                    'current_ratio': {'value': 2.5, 'formatted_value': '2.50'},
                    'debt_to_equity': {'value': 0.4, 'formatted_value': '0.40'},
                    'roe': {'value': 0.18, 'formatted_value': '18.00%'},
                    'net_profit_margin': {'value': 0.12, 'formatted_value': '12.00%'}
                },
                'benchmarks': {
                    'current_ratio': {
                        'value': 2.5,
                        'benchmark_good': 2.0,
                        'performance': 'good'
                    },
                    'debt_to_equity': {
                        'value': 0.4,
                        'benchmark_good': 0.5,
                        'performance': 'good'
                    }
                },
                'trends': {
                    'revenue': {
                        'trend_direction': 'increasing',
                        'cagr': 12.5,
                        'values': [10000000, 11000000, 12500000],
                        'interpretation': 'Strong revenue growth trend'
                    },
                    'profit': {
                        'trend_direction': 'increasing',
                        'cagr': 15.0,
                        'values': [1000000, 1200000, 1500000],
                        'interpretation': 'Improving profitability'
                    }
                },
                'summary': 'Strong financial performance with healthy ratios and positive trends'
            },
            'forecasts': {
                'forecasts': {
                    'revenue': {
                        'projected_values': [14000000, 16000000, 18000000],
                        'confidence_level': 0.75
                    },
                    'profit': {
                        'projected_values': [1800000, 2200000, 2600000],
                        'confidence_level': 0.70
                    },
                    'cash_flow': {
                        'projected_values': [1500000, 1800000, 2100000],
                        'confidence_level': 0.72
                    }
                }
            },
            'risk': {
                'overall_score': 78.5,
                'recommendation': 'approve',
                'summary': 'Strong creditworthiness with favorable risk profile',
                'financial_health': {
                    'score': 82.0,
                    'weight': 0.35,
                    'explanation': 'Strong financial ratios and healthy balance sheet',
                    'key_findings': ['Strong liquidity position', 'Low leverage']
                },
                'cash_flow': {
                    'score': 80.0,
                    'weight': 0.25,
                    'explanation': 'Consistent cash flow generation with positive trends',
                    'key_findings': ['Positive cash flow growth', 'Adequate liquidity']
                },
                'industry': {
                    'score': 75.0,
                    'weight': 0.15,
                    'explanation': 'Favorable industry outlook with growth potential',
                    'key_findings': ['Growing market', 'Strong competitive position']
                },
                'promoter': {
                    'score': 78.0,
                    'weight': 0.15,
                    'explanation': 'Experienced management with proven track record',
                    'key_findings': ['Experienced team', 'Successful track record']
                },
                'external_intelligence': {
                    'score': 72.0,
                    'weight': 0.10,
                    'explanation': 'Positive market sentiment and reputation',
                    'key_findings': ['Positive news coverage', 'Growing customer base']
                }
            },
            'research': {
                'web': {
                    'news_summary': 'Recent positive coverage of product launches and market expansion',
                    'market_sentiment': 'Positive investor confidence'
                },
                'promoter': {
                    'background': 'Experienced management team with 20+ years in industry'
                },
                'industry': {
                    'sector_outlook': 'Positive growth expected in the technology sector'
                }
            },
            'version': 1
        }
    
    async def test_generate_returns_cam_object(self, agent, sample_analysis_data):
        """Test that generate() returns a valid CAM object"""
        result = await agent.generate(sample_analysis_data)
        
        assert isinstance(result, CAM)
        assert result.application_id == 'test-app-123'
        assert result.version == 1
        assert isinstance(result.generated_at, datetime)
        assert len(result.content) > 0
    
    async def test_cam_has_required_sections(self, agent, sample_analysis_data):
        """Test that CAM contains all required sections"""
        result = await agent.generate(sample_analysis_data)
        
        required_sections = [
            'executive_summary',
            'company_overview',
            'financial_analysis',
            'risk_assessment',
            'recommendation'
        ]
        
        for section in required_sections:
            assert section in result.sections
            assert len(result.sections[section]) > 0
    
    async def test_cam_content_includes_company_name(self, agent, sample_analysis_data):
        """Test that CAM content includes company name"""
        result = await agent.generate(sample_analysis_data)
        
        assert 'TechCorp Industries' in result.content
    
    async def test_cam_content_includes_loan_amount(self, agent, sample_analysis_data):
        """Test that CAM content includes loan amount"""
        result = await agent.generate(sample_analysis_data)
        
        assert '5,000,000' in result.content or '$5,000,000' in result.content
    
    async def test_cam_content_includes_version(self, agent, sample_analysis_data):
        """Test that CAM content includes version tracking"""
        result = await agent.generate(sample_analysis_data)
        
        assert 'Version: 1' in result.content or 'version: 1' in result.content.lower()
    
    async def test_cam_content_includes_timestamp(self, agent, sample_analysis_data):
        """Test that CAM content includes generation timestamp"""
        result = await agent.generate(sample_analysis_data)
        
        assert 'Generated:' in result.content or 'generated:' in result.content.lower()
    
    async def test_financial_analysis_includes_tables(self, agent, sample_analysis_data):
        """Test that financial analysis section includes formatted tables"""
        result = await agent.generate(sample_analysis_data)
        
        financial_section = result.sections['financial_analysis']
        
        # Check for table markers
        assert '|' in financial_section  # Markdown table delimiter
        assert 'Ratio' in financial_section or 'ratio' in financial_section.lower()
    
    async def test_risk_assessment_includes_scores(self, agent, sample_analysis_data):
        """Test that risk assessment section includes risk scores"""
        result = await agent.generate(sample_analysis_data)
        
        risk_section = result.sections['risk_assessment']
        
        # Check for score information
        assert '78.5' in risk_section or '78' in risk_section  # Overall score
        assert 'Financial Health' in risk_section or 'financial health' in risk_section.lower()
    
    async def test_recommendation_section_includes_decision(self, agent, sample_analysis_data):
        """Test that recommendation section includes credit decision"""
        result = await agent.generate(sample_analysis_data)
        
        recommendation_section = result.sections['recommendation']
        
        # Check for recommendation
        assert 'approve' in recommendation_section.lower() or 'approval' in recommendation_section.lower()
    
    async def test_cam_with_conditional_approval(self, agent, sample_analysis_data):
        """Test CAM generation with conditional approval recommendation"""
        # Modify to conditional approval
        sample_analysis_data['risk']['overall_score'] = 55.0
        sample_analysis_data['risk']['recommendation'] = 'approve_with_conditions'
        
        result = await agent.generate(sample_analysis_data)
        
        assert isinstance(result, CAM)
        recommendation_section = result.sections['recommendation']
        assert 'condition' in recommendation_section.lower()
    
    async def test_cam_with_rejection(self, agent, sample_analysis_data):
        """Test CAM generation with rejection recommendation"""
        # Modify to rejection
        sample_analysis_data['risk']['overall_score'] = 35.0
        sample_analysis_data['risk']['recommendation'] = 'reject'
        
        result = await agent.generate(sample_analysis_data)
        
        assert isinstance(result, CAM)
        recommendation_section = result.sections['recommendation']
        assert 'reject' in recommendation_section.lower() or 'decline' in recommendation_section.lower()
    
    async def test_cam_with_minimal_data(self, agent):
        """Test CAM generation with minimal data"""
        minimal_data = {
            'application_id': 'test-minimal',
            'company_name': 'Minimal Corp',
            'loan_amount': 1000000.0,
            'loan_purpose': 'Working capital',
            'financial': {'ratios': {}, 'trends': {}, 'benchmarks': {}},
            'forecasts': {'forecasts': {}},
            'risk': {
                'overall_score': 50.0,
                'recommendation': 'approve_with_conditions',
                'summary': 'Moderate risk profile',
                'financial_health': {'score': 50.0, 'weight': 0.35, 'explanation': 'Moderate', 'key_findings': []},
                'cash_flow': {'score': 50.0, 'weight': 0.25, 'explanation': 'Moderate', 'key_findings': []},
                'industry': {'score': 50.0, 'weight': 0.15, 'explanation': 'Moderate', 'key_findings': []},
                'promoter': {'score': 50.0, 'weight': 0.15, 'explanation': 'Moderate', 'key_findings': []},
                'external_intelligence': {'score': 50.0, 'weight': 0.10, 'explanation': 'Moderate', 'key_findings': []}
            },
            'research': {'web': {}, 'promoter': {}, 'industry': {}},
            'version': 1
        }
        
        result = await agent.generate(minimal_data)
        
        assert isinstance(result, CAM)
        assert result.application_id == 'test-minimal'
        assert len(result.sections) == 5  # All required sections
    
    async def test_cam_version_tracking(self, agent, sample_analysis_data):
        """Test that CAM properly tracks version numbers"""
        # Generate version 1
        result_v1 = await agent.generate(sample_analysis_data)
        assert result_v1.version == 1
        
        # Generate version 2
        sample_analysis_data['version'] = 2
        result_v2 = await agent.generate(sample_analysis_data)
        assert result_v2.version == 2
        
        # Ensure timestamps are different (or at least present)
        assert isinstance(result_v1.generated_at, datetime)
        assert isinstance(result_v2.generated_at, datetime)

    async def test_export_to_pdf_returns_bytes(self, agent, sample_analysis_data):
        """Test that export_to_pdf() returns valid PDF bytes"""
        cam = await agent.generate(sample_analysis_data)
        pdf_bytes = await agent.export_to_pdf(cam)
        
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        # Check PDF magic number
        assert pdf_bytes[:4] == b'%PDF'
    
    async def test_export_to_word_returns_bytes(self, agent, sample_analysis_data):
        """Test that export_to_word() returns valid Word document bytes"""
        cam = await agent.generate(sample_analysis_data)
        word_bytes = await agent.export_to_word(cam)
        
        assert isinstance(word_bytes, bytes)
        assert len(word_bytes) > 0
        # Check for DOCX magic number (PK zip header)
        assert word_bytes[:2] == b'PK'
    
    async def test_export_to_pdf_with_minimal_cam(self, agent):
        """Test PDF export with minimal CAM data"""
        minimal_data = {
            'application_id': 'test-minimal',
            'company_name': 'Minimal Corp',
            'loan_amount': 1000000.0,
            'loan_purpose': 'Working capital',
            'financial': {'ratios': {}, 'trends': {}, 'benchmarks': {}},
            'forecasts': {'forecasts': {}},
            'risk': {
                'overall_score': 50.0,
                'recommendation': 'approve_with_conditions',
                'summary': 'Moderate risk profile',
                'financial_health': {'score': 50.0, 'weight': 0.35, 'explanation': 'Moderate', 'key_findings': []},
                'cash_flow': {'score': 50.0, 'weight': 0.25, 'explanation': 'Moderate', 'key_findings': []},
                'industry': {'score': 50.0, 'weight': 0.15, 'explanation': 'Moderate', 'key_findings': []},
                'promoter': {'score': 50.0, 'weight': 0.15, 'explanation': 'Moderate', 'key_findings': []},
                'external_intelligence': {'score': 50.0, 'weight': 0.10, 'explanation': 'Moderate', 'key_findings': []}
            },
            'research': {'web': {}, 'promoter': {}, 'industry': {}},
            'version': 1
        }
        
        cam = await agent.generate(minimal_data)
        pdf_bytes = await agent.export_to_pdf(cam)
        
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        assert pdf_bytes[:4] == b'%PDF'
    
    async def test_export_to_word_with_minimal_cam(self, agent):
        """Test Word export with minimal CAM data"""
        minimal_data = {
            'application_id': 'test-minimal',
            'company_name': 'Minimal Corp',
            'loan_amount': 1000000.0,
            'loan_purpose': 'Working capital',
            'financial': {'ratios': {}, 'trends': {}, 'benchmarks': {}},
            'forecasts': {'forecasts': {}},
            'risk': {
                'overall_score': 50.0,
                'recommendation': 'approve_with_conditions',
                'summary': 'Moderate risk profile',
                'financial_health': {'score': 50.0, 'weight': 0.35, 'explanation': 'Moderate', 'key_findings': []},
                'cash_flow': {'score': 50.0, 'weight': 0.25, 'explanation': 'Moderate', 'key_findings': []},
                'industry': {'score': 50.0, 'weight': 0.15, 'explanation': 'Moderate', 'key_findings': []},
                'promoter': {'score': 50.0, 'weight': 0.15, 'explanation': 'Moderate', 'key_findings': []},
                'external_intelligence': {'score': 50.0, 'weight': 0.10, 'explanation': 'Moderate', 'key_findings': []}
            },
            'research': {'web': {}, 'promoter': {}, 'industry': {}},
            'version': 1
        }
        
        cam = await agent.generate(minimal_data)
        word_bytes = await agent.export_to_word(cam)
        
        assert isinstance(word_bytes, bytes)
        assert len(word_bytes) > 0
        assert word_bytes[:2] == b'PK'
    
    def test_validate_export_format_pdf(self, agent):
        """Test format validation for PDF"""
        assert agent.validate_export_format('pdf') is True
        assert agent.validate_export_format('PDF') is True
    
    def test_validate_export_format_word(self, agent):
        """Test format validation for Word"""
        assert agent.validate_export_format('word') is True
        assert agent.validate_export_format('WORD') is True
        assert agent.validate_export_format('docx') is True
        assert agent.validate_export_format('DOCX') is True
    
    def test_validate_export_format_invalid(self, agent):
        """Test format validation for invalid formats"""
        assert agent.validate_export_format('txt') is False
        assert agent.validate_export_format('html') is False
        assert agent.validate_export_format('json') is False
        assert agent.validate_export_format('') is False
    
    async def test_export_to_pdf_error_handling(self, agent):
        """Test error handling in PDF export"""
        # Create a CAM with empty content that will cause markdown conversion issues
        from app.models.domain import CAM
        invalid_cam = CAM(
            application_id='test',
            content='',  # Empty content
            version=1,
            generated_at=datetime.utcnow(),
            sections={
                'executive_summary': '',
                'company_overview': '',
                'financial_analysis': '',
                'risk_assessment': '',
                'recommendation': ''
            }
        )
        
        # This should still work with empty content, so let's test with truly invalid HTML
        # We'll mock the markdown conversion to return invalid HTML
        import unittest.mock as mock
        with mock.patch('app.agents.cam_generator_agent.markdown2.markdown', side_effect=Exception("Markdown conversion failed")):
            with pytest.raises(ValueError, match="Failed to export CAM to PDF"):
                await agent.export_to_pdf(invalid_cam)
    
    async def test_export_to_word_error_handling(self, agent):
        """Test error handling in Word export"""
        # Create a CAM with empty content
        from app.models.domain import CAM
        invalid_cam = CAM(
            application_id='test',
            content='',  # Empty content
            version=1,
            generated_at=datetime.utcnow(),
            sections={
                'executive_summary': '',
                'company_overview': '',
                'financial_analysis': '',
                'risk_assessment': '',
                'recommendation': ''
            }
        )
        
        # Mock Document to raise an exception
        import unittest.mock as mock
        with mock.patch('app.agents.cam_generator_agent.Document', side_effect=Exception("Document creation failed")):
            with pytest.raises(ValueError, match="Failed to export CAM to Word"):
                await agent.export_to_word(invalid_cam)
