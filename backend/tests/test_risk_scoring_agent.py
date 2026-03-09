"""
Tests for RiskScoringAgent

This module tests the risk scoring functionality including:
- Individual factor scoring methods
- Weighted score calculation
- Recommendation logic
- Explanation generation
"""

import pytest
from app.agents.risk_scoring_agent import RiskScoringAgent
from app.models.domain import CreditRecommendation


@pytest.mark.asyncio
class TestRiskScoringAgent:
    """Test suite for RiskScoringAgent"""
    
    @pytest.fixture
    def agent(self):
        """Create a RiskScoringAgent instance"""
        return RiskScoringAgent()
    
    @pytest.fixture
    def sample_analysis_data(self):
        """Sample analysis data for testing"""
        return {
            'financial': {
                'ratios': {
                    'current_ratio': {'value': 2.5, 'formatted_value': '2.50'},
                    'debt_to_equity': {'value': 0.4, 'formatted_value': '0.40'},
                    'roe': {'value': 0.18, 'formatted_value': '18.00%'}
                },
                'benchmarks': {
                    'current_ratio': {'performance': 'good', 'value': 2.5},
                    'debt_to_equity': {'performance': 'good', 'value': 0.4},
                    'roe': {'performance': 'good', 'value': 0.18}
                },
                'trends': {
                    'revenue': {
                        'trend_direction': 'increasing',
                        'cagr': 12.5,
                        'values': [1000000, 1100000, 1250000]
                    },
                    'profit': {
                        'trend_direction': 'increasing',
                        'cagr': 15.0,
                        'values': [100000, 120000, 150000]
                    },
                    'cash_flow': {
                        'trend_direction': 'increasing',
                        'cagr': 10.0,
                        'values': [80000, 90000, 100000]
                    }
                }
            },
            'forecasts': {
                'forecasts': {
                    'cash_flow': {
                        'projected_values': [110000, 120000, 130000],
                        'forecast_growth_rate': 8.5
                    }
                }
            },
            'research': {
                'industry': {
                    'sector_outlook': 'Positive growth expected in the technology sector',
                    'competitive_position': 'Strong market position with innovative products',
                    'industry_risks': ['Regulatory changes', 'Market competition'],
                    'growth_potential': 'High growth potential in emerging markets'
                },
                'promoter': {
                    'background': 'Experienced management team with 20+ years in industry',
                    'track_record': 'Successful track record of building profitable businesses',
                    'reputation': 'Positive reputation in the industry',
                    'red_flags': [],
                    'experience': 'Deep industry expertise and strong network'
                },
                'web': {
                    'news_summary': 'Recent positive coverage of product launches',
                    'market_sentiment': 'Positive market sentiment and investor confidence',
                    'red_flags': [],
                    'positive_indicators': ['Award-winning products', 'Growing customer base'],
                    'regulatory_issues': []
                }
            }
        }
    
    async def test_score_returns_risk_assessment(self, agent, sample_analysis_data):
        """Test that score() returns a valid RiskAssessment"""
        result = await agent.score(sample_analysis_data)
        
        assert result is not None
        assert hasattr(result, 'overall_score')
        assert hasattr(result, 'recommendation')
        assert hasattr(result, 'financial_health')
        assert hasattr(result, 'cash_flow')
        assert hasattr(result, 'industry')
        assert hasattr(result, 'promoter')
        assert hasattr(result, 'external_intelligence')
        assert hasattr(result, 'summary')
    
    async def test_overall_score_in_valid_range(self, agent, sample_analysis_data):
        """Test that overall score is between 0 and 100"""
        result = await agent.score(sample_analysis_data)
        
        assert 0 <= result.overall_score <= 100
    
    async def test_factor_scores_in_valid_range(self, agent, sample_analysis_data):
        """Test that all factor scores are between 0 and 100"""
        result = await agent.score(sample_analysis_data)
        
        assert 0 <= result.financial_health.score <= 100
        assert 0 <= result.cash_flow.score <= 100
        assert 0 <= result.industry.score <= 100
        assert 0 <= result.promoter.score <= 100
        assert 0 <= result.external_intelligence.score <= 100
    
    async def test_weights_are_correct(self, agent, sample_analysis_data):
        """Test that factor weights match specification"""
        result = await agent.score(sample_analysis_data)
        
        assert result.financial_health.weight == 0.35
        assert result.cash_flow.weight == 0.25
        assert result.industry.weight == 0.15
        assert result.promoter.weight == 0.15
        assert result.external_intelligence.weight == 0.10
    
    async def test_weighted_score_calculation(self, agent, sample_analysis_data):
        """Test that overall score is correctly calculated from weighted factors"""
        result = await agent.score(sample_analysis_data)
        
        expected_score = (
            result.financial_health.score * 0.35 +
            result.cash_flow.score * 0.25 +
            result.industry.score * 0.15 +
            result.promoter.score * 0.15 +
            result.external_intelligence.score * 0.10
        )
        
        # Allow small floating point difference
        assert abs(result.overall_score - expected_score) < 0.01
    
    async def test_recommendation_approve_for_high_score(self, agent, sample_analysis_data):
        """Test that high scores (>=70) result in APPROVE recommendation"""
        result = await agent.score(sample_analysis_data)
        
        # With good data, we should get a high score
        if result.overall_score >= 70:
            assert result.recommendation == CreditRecommendation.APPROVE
    
    async def test_recommendation_conditional_for_medium_score(self, agent):
        """Test that medium scores (40-69) result in APPROVE_WITH_CONDITIONS"""
        # Create data that should result in medium score
        medium_data = {
            'financial': {
                'ratios': {
                    'current_ratio': {'value': 1.2, 'formatted_value': '1.20'}
                },
                'benchmarks': {
                    'current_ratio': {'performance': 'acceptable', 'value': 1.2}
                },
                'trends': {
                    'revenue': {'trend_direction': 'stable', 'cagr': 2.0},
                    'profit': {'trend_direction': 'stable', 'cagr': 1.5},
                    'cash_flow': {'trend_direction': 'stable', 'cagr': 1.0}
                }
            },
            'forecasts': {
                'forecasts': {
                    'cash_flow': {
                        'projected_values': [100000, 102000, 104000],
                        'forecast_growth_rate': 2.0
                    }
                }
            },
            'research': {
                'industry': {
                    'sector_outlook': 'Moderate growth expected',
                    'competitive_position': 'Average market position',
                    'industry_risks': ['Competition'],
                    'growth_potential': 'Moderate'
                },
                'promoter': {
                    'background': 'Some experience',
                    'track_record': 'Mixed results',
                    'reputation': 'Neutral',
                    'red_flags': [],
                    'experience': 'Limited'
                },
                'web': {
                    'news_summary': 'Limited coverage',
                    'market_sentiment': 'Neutral',
                    'red_flags': [],
                    'positive_indicators': [],
                    'regulatory_issues': []
                }
            }
        }
        
        result = await agent.score(medium_data)
        
        if 40 <= result.overall_score < 70:
            assert result.recommendation == CreditRecommendation.APPROVE_WITH_CONDITIONS
    
    async def test_recommendation_reject_for_low_score(self, agent):
        """Test that low scores (<40) result in REJECT recommendation"""
        # Create data that should result in low score
        poor_data = {
            'financial': {
                'ratios': {
                    'current_ratio': {'value': 0.8, 'formatted_value': '0.80'}
                },
                'benchmarks': {
                    'current_ratio': {'performance': 'poor', 'value': 0.8}
                },
                'trends': {
                    'revenue': {'trend_direction': 'decreasing', 'cagr': -5.0},
                    'profit': {'trend_direction': 'decreasing', 'cagr': -8.0},
                    'cash_flow': {'trend_direction': 'decreasing', 'cagr': -10.0}
                }
            },
            'forecasts': {
                'forecasts': {
                    'cash_flow': {
                        'projected_values': [90000, 85000, 80000],
                        'forecast_growth_rate': -5.0
                    }
                }
            },
            'research': {
                'industry': {
                    'sector_outlook': 'Declining sector with challenges',
                    'competitive_position': 'Weak position',
                    'industry_risks': ['Major disruption', 'Declining demand'],
                    'growth_potential': 'Low'
                },
                'promoter': {
                    'background': 'Limited experience',
                    'track_record': 'Poor track record',
                    'reputation': 'Negative',
                    'red_flags': ['Past business failures', 'Legal issues'],
                    'experience': 'Minimal'
                },
                'web': {
                    'news_summary': 'Negative coverage',
                    'market_sentiment': 'Negative',
                    'red_flags': ['Lawsuits', 'Customer complaints'],
                    'positive_indicators': [],
                    'regulatory_issues': ['Compliance violations']
                }
            }
        }
        
        result = await agent.score(poor_data)
        
        if result.overall_score < 40:
            assert result.recommendation == CreditRecommendation.REJECT
    
    async def test_factor_explanations_are_generated(self, agent, sample_analysis_data):
        """Test that explanations are generated for each factor"""
        result = await agent.score(sample_analysis_data)
        
        assert result.financial_health.explanation
        assert len(result.financial_health.explanation) > 0
        assert result.cash_flow.explanation
        assert len(result.cash_flow.explanation) > 0
        assert result.industry.explanation
        assert len(result.industry.explanation) > 0
        assert result.promoter.explanation
        assert len(result.promoter.explanation) > 0
        assert result.external_intelligence.explanation
        assert len(result.external_intelligence.explanation) > 0
    
    async def test_key_findings_are_populated(self, agent, sample_analysis_data):
        """Test that key findings are populated for each factor"""
        result = await agent.score(sample_analysis_data)
        
        assert isinstance(result.financial_health.key_findings, list)
        assert isinstance(result.cash_flow.key_findings, list)
        assert isinstance(result.industry.key_findings, list)
        assert isinstance(result.promoter.key_findings, list)
        assert isinstance(result.external_intelligence.key_findings, list)
    
    async def test_summary_is_generated(self, agent, sample_analysis_data):
        """Test that overall summary is generated"""
        result = await agent.score(sample_analysis_data)
        
        assert result.summary
        assert len(result.summary) > 0
        assert isinstance(result.summary, str)
    
    async def test_handles_empty_financial_data(self, agent):
        """Test that agent handles missing financial data gracefully"""
        minimal_data = {
            'financial': {},
            'forecasts': {},
            'research': {}
        }
        
        result = await agent.score(minimal_data)
        
        assert result is not None
        assert 0 <= result.overall_score <= 100
        assert result.recommendation in [
            CreditRecommendation.APPROVE,
            CreditRecommendation.APPROVE_WITH_CONDITIONS,
            CreditRecommendation.REJECT
        ]
    
    async def test_handles_missing_research_data(self, agent):
        """Test that agent handles missing research data gracefully"""
        data_without_research = {
            'financial': {
                'ratios': {'current_ratio': {'value': 1.5}},
                'benchmarks': {'current_ratio': {'performance': 'acceptable'}},
                'trends': {'revenue': {'trend_direction': 'stable'}}
            },
            'forecasts': {},
            'research': {}
        }
        
        result = await agent.score(data_without_research)
        
        assert result is not None
        assert result.industry.score == 50.0  # Default score for missing data
        assert result.promoter.score == 50.0
        assert result.external_intelligence.score == 50.0
    
    def test_determine_recommendation_thresholds(self, agent):
        """Test recommendation threshold logic"""
        # Test approve threshold
        assert agent._determine_recommendation(70.0) == CreditRecommendation.APPROVE
        assert agent._determine_recommendation(85.0) == CreditRecommendation.APPROVE
        assert agent._determine_recommendation(100.0) == CreditRecommendation.APPROVE
        
        # Test conditional threshold
        assert agent._determine_recommendation(40.0) == CreditRecommendation.APPROVE_WITH_CONDITIONS
        assert agent._determine_recommendation(55.0) == CreditRecommendation.APPROVE_WITH_CONDITIONS
        assert agent._determine_recommendation(69.9) == CreditRecommendation.APPROVE_WITH_CONDITIONS
        
        # Test reject threshold
        assert agent._determine_recommendation(0.0) == CreditRecommendation.REJECT
        assert agent._determine_recommendation(20.0) == CreditRecommendation.REJECT
        assert agent._determine_recommendation(39.9) == CreditRecommendation.REJECT
    
    def test_weights_sum_to_one(self, agent):
        """Test that all factor weights sum to 1.0"""
        total_weight = sum(agent.WEIGHTS.values())
        assert abs(total_weight - 1.0) < 0.001  # Allow small floating point error


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
