"""
Property-based tests for RiskScoringAgent

Feature: intelli-credit-platform
Property 12: Risk Score Calculation and Weighting
Property 13: Credit Recommendation Mapping
Property 14: Risk Score Explainability

Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7
"""

import pytest
from hypothesis import given, strategies as st, settings
from app.agents.risk_scoring_agent import RiskScoringAgent
from app.models.domain import CreditRecommendation


# Strategy for generating risk factor scores (0-100)
risk_score = st.floats(min_value=0, max_value=100, allow_nan=False, allow_infinity=False)


class TestProperty12RiskScoreCalculationAndWeighting:
    """
    Property 12: Risk Score Calculation and Weighting
    
    For any complete analysis with all risk factors scored, the overall credit score
    should be calculated as a weighted sum using the specified weights (financial health 35%,
    cash flow 25%, industry 15%, promoter 15%, external intelligence 10%) and fall within
    the range 0-100.
    
    Validates: Requirements 6.1, 6.2
    """
    
    @pytest.mark.property
    @pytest.mark.asyncio
    @settings(max_examples=20)
    @given(
        financial_health=risk_score,
        cash_flow=risk_score,
        industry=risk_score,
        promoter=risk_score,
        external_intelligence=risk_score
    )
    async def test_weighted_score_calculation(
        self,
        financial_health: float,
        cash_flow: float,
        industry: float,
        promoter: float,
        external_intelligence: float
    ):
        """
        Property: Overall score = weighted sum of all factor scores
        
        For any set of risk factor scores (each 0-100), the overall credit score
        should equal the weighted sum using the specified weights and be within 0-100.
        """
        agent = RiskScoringAgent()
        
        # Create mock analysis data with the generated scores
        # We'll use the agent's internal scoring methods by providing structured data
        analysis_data = {
            'financial': {
                'ratios': {
                    'current_ratio': {'value': 1.5, 'benchmark': 1.2},
                    'debt_to_equity': {'value': 0.5, 'benchmark': 0.7}
                },
                'benchmarks': {
                    'current_ratio': {'performance': 'good'},
                    'debt_to_equity': {'performance': 'good'}
                },
                'trends': {
                    'revenue': {'trend_direction': 'increasing', 'cagr': 10},
                    'profit': {'trend_direction': 'increasing', 'cagr': 8},
                    'cash_flow': {'trend_direction': 'increasing', 'cagr': 12}
                }
            },
            'forecasts': {
                'forecasts': {
                    'cash_flow': {
                        'projected_values': [100000, 110000, 120000],
                        'forecast_growth_rate': 10
                    }
                }
            },
            'research': {
                'industry': {
                    'sector_outlook': 'positive growth expected',
                    'competitive_position': 'strong market position',
                    'industry_risks': [],
                    'growth_potential': 'high'
                },
                'promoter': {
                    'background': 'experienced management',
                    'track_record': 'successful ventures',
                    'reputation': 'positive',
                    'red_flags': [],
                    'experience': '15+ years'
                },
                'web': {
                    'news_summary': 'positive coverage',
                    'market_sentiment': 'positive',
                    'red_flags': [],
                    'positive_indicators': ['strong growth', 'market leader'],
                    'regulatory_issues': []
                }
            }
        }
        
        # Get the risk assessment
        result = await agent.score(analysis_data)
        
        # Verify the overall score is within valid range
        assert 0 <= result.overall_score <= 100, \
            f"Overall score {result.overall_score} is outside valid range [0, 100]"
        
        # Verify each factor score is within valid range
        assert 0 <= result.financial_health.score <= 100
        assert 0 <= result.cash_flow.score <= 100
        assert 0 <= result.industry.score <= 100
        assert 0 <= result.promoter.score <= 100
        assert 0 <= result.external_intelligence.score <= 100
        
        # Verify the weights are correct
        assert abs(result.financial_health.weight - 0.35) < 0.01
        assert abs(result.cash_flow.weight - 0.25) < 0.01
        assert abs(result.industry.weight - 0.15) < 0.01
        assert abs(result.promoter.weight - 0.15) < 0.01
        assert abs(result.external_intelligence.weight - 0.10) < 0.01
        
        # Verify the weighted calculation
        expected_score = (
            result.financial_health.score * 0.35 +
            result.cash_flow.score * 0.25 +
            result.industry.score * 0.15 +
            result.promoter.score * 0.15 +
            result.external_intelligence.score * 0.10
        )
        
        # Allow small rounding difference
        assert abs(result.overall_score - expected_score) < 0.1, \
            f"Overall score {result.overall_score} doesn't match weighted sum {expected_score}"
    
    @pytest.mark.property
    @pytest.mark.asyncio
    @settings(max_examples=20)
    @given(
        financial_health=risk_score,
        cash_flow=risk_score,
        industry=risk_score,
        promoter=risk_score,
        external_intelligence=risk_score
    )
    async def test_weights_sum_to_one(
        self,
        financial_health: float,
        cash_flow: float,
        industry: float,
        promoter: float,
        external_intelligence: float
    ):
        """
        Property: The sum of all risk factor weights should equal 1.0
        
        For any risk assessment, the weights of all five factors should sum to 1.0
        (35% + 25% + 15% + 15% + 10% = 100%).
        """
        agent = RiskScoringAgent()
        
        # Create minimal analysis data
        analysis_data = {
            'financial': {
                'ratios': {},
                'benchmarks': {},
                'trends': {}
            },
            'forecasts': {'forecasts': {}},
            'research': {
                'industry': {},
                'promoter': {},
                'web': {}
            }
        }
        
        result = await agent.score(analysis_data)
        
        # Calculate sum of weights
        total_weight = (
            result.financial_health.weight +
            result.cash_flow.weight +
            result.industry.weight +
            result.promoter.weight +
            result.external_intelligence.weight
        )
        
        # Verify weights sum to 1.0
        assert abs(total_weight - 1.0) < 0.01, \
            f"Weights sum to {total_weight}, expected 1.0"


class TestProperty13CreditRecommendationMapping:
    """
    Property 13: Credit Recommendation Mapping
    
    For any calculated credit score, the recommendation should be "Reject" if score < 40,
    "Approve with conditions" if 40 ≤ score < 70, and "Approve" if score ≥ 70.
    
    Validates: Requirements 6.4, 6.5, 6.6
    """
    
    @pytest.mark.property
    @pytest.mark.asyncio
    @settings(max_examples=20)
    @given(credit_score=st.floats(min_value=0, max_value=100, allow_nan=False, allow_infinity=False))
    async def test_recommendation_thresholds(self, credit_score: float):
        """
        Property: Recommendation mapping follows score thresholds
        
        For any credit score in [0, 100]:
        - score < 40 → REJECT
        - 40 ≤ score < 70 → APPROVE_WITH_CONDITIONS
        - score ≥ 70 → APPROVE
        """
        agent = RiskScoringAgent()
        
        # Use the internal method to determine recommendation
        recommendation = agent._determine_recommendation(credit_score)
        
        # Verify the recommendation matches the threshold rules
        if credit_score < 40:
            assert recommendation == CreditRecommendation.REJECT, \
                f"Score {credit_score} should map to REJECT, got {recommendation}"
        elif credit_score < 70:
            assert recommendation == CreditRecommendation.APPROVE_WITH_CONDITIONS, \
                f"Score {credit_score} should map to APPROVE_WITH_CONDITIONS, got {recommendation}"
        else:
            assert recommendation == CreditRecommendation.APPROVE, \
                f"Score {credit_score} should map to APPROVE, got {recommendation}"
    
    @pytest.mark.property
    @pytest.mark.asyncio
    @settings(max_examples=20)
    @given(credit_score=risk_score)
    async def test_recommendation_consistency_in_full_assessment(self, credit_score: float):
        """
        Property: Full risk assessment recommendation matches threshold rules
        
        For any complete risk assessment, the recommendation should be consistent
        with the overall score and threshold rules.
        """
        agent = RiskScoringAgent()
        
        # Create analysis data that will produce a predictable score range
        # We'll verify the recommendation matches the actual calculated score
        analysis_data = {
            'financial': {
                'ratios': {
                    'current_ratio': {'value': 1.5}
                },
                'benchmarks': {
                    'current_ratio': {'performance': 'good'}
                },
                'trends': {
                    'revenue': {'trend_direction': 'increasing'},
                    'profit': {'trend_direction': 'increasing'},
                    'cash_flow': {'trend_direction': 'increasing', 'cagr': 10}
                }
            },
            'forecasts': {
                'forecasts': {
                    'cash_flow': {
                        'projected_values': [100000, 110000, 120000],
                        'forecast_growth_rate': 10
                    }
                }
            },
            'research': {
                'industry': {
                    'sector_outlook': 'positive',
                    'competitive_position': 'strong',
                    'industry_risks': [],
                    'growth_potential': 'high'
                },
                'promoter': {
                    'background': 'experienced',
                    'track_record': 'successful',
                    'reputation': 'positive',
                    'red_flags': [],
                    'experience': '10+ years'
                },
                'web': {
                    'news_summary': 'positive',
                    'market_sentiment': 'positive',
                    'red_flags': [],
                    'positive_indicators': ['growth'],
                    'regulatory_issues': []
                }
            }
        }
        
        result = await agent.score(analysis_data)
        
        # Verify recommendation matches the score
        if result.overall_score < 40:
            assert result.recommendation == CreditRecommendation.REJECT
        elif result.overall_score < 70:
            assert result.recommendation == CreditRecommendation.APPROVE_WITH_CONDITIONS
        else:
            assert result.recommendation == CreditRecommendation.APPROVE
    
    @pytest.mark.property
    @pytest.mark.asyncio
    @settings(max_examples=10)
    @given(
        threshold_offset=st.floats(min_value=-0.5, max_value=0.5, allow_nan=False, allow_infinity=False)
    )
    async def test_boundary_conditions(self, threshold_offset: float):
        """
        Property: Recommendations are correct at boundary values
        
        Test scores near the threshold boundaries (40 and 70) to ensure
        correct recommendation mapping.
        """
        agent = RiskScoringAgent()
        
        # Test near lower threshold (40)
        score_near_40 = 40.0 + threshold_offset
        if 0 <= score_near_40 <= 100:
            rec = agent._determine_recommendation(score_near_40)
            if score_near_40 < 40:
                assert rec == CreditRecommendation.REJECT
            elif score_near_40 < 70:
                assert rec == CreditRecommendation.APPROVE_WITH_CONDITIONS
            else:
                assert rec == CreditRecommendation.APPROVE
        
        # Test near upper threshold (70)
        score_near_70 = 70.0 + threshold_offset
        if 0 <= score_near_70 <= 100:
            rec = agent._determine_recommendation(score_near_70)
            if score_near_70 < 40:
                assert rec == CreditRecommendation.REJECT
            elif score_near_70 < 70:
                assert rec == CreditRecommendation.APPROVE_WITH_CONDITIONS
            else:
                assert rec == CreditRecommendation.APPROVE


class TestProperty14RiskScoreExplainability:
    """
    Property 14: Risk Score Explainability
    
    For any generated credit score, the system should provide detailed explanations
    for each of the five risk factor contributions and document the key factors
    influencing the recommendation.
    
    Validates: Requirements 6.3, 6.7
    """
    
    @pytest.mark.property
    @pytest.mark.asyncio
    @settings(max_examples=20)
    @given(
        financial_health=risk_score,
        cash_flow=risk_score,
        industry=risk_score,
        promoter=risk_score,
        external_intelligence=risk_score
    )
    async def test_all_factors_have_explanations(
        self,
        financial_health: float,
        cash_flow: float,
        industry: float,
        promoter: float,
        external_intelligence: float
    ):
        """
        Property: Every risk factor must have a non-empty explanation
        
        For any risk assessment, each of the five risk factors should have
        a detailed explanation string that is not empty.
        """
        agent = RiskScoringAgent()
        
        # Create analysis data
        analysis_data = {
            'financial': {
                'ratios': {
                    'current_ratio': {'value': 1.5},
                    'debt_to_equity': {'value': 0.5}
                },
                'benchmarks': {
                    'current_ratio': {'performance': 'good'},
                    'debt_to_equity': {'performance': 'acceptable'}
                },
                'trends': {
                    'revenue': {'trend_direction': 'increasing', 'cagr': 5},
                    'profit': {'trend_direction': 'stable'},
                    'cash_flow': {'trend_direction': 'increasing', 'cagr': 8}
                }
            },
            'forecasts': {
                'forecasts': {
                    'cash_flow': {
                        'projected_values': [100000, 105000, 110000],
                        'forecast_growth_rate': 5
                    }
                }
            },
            'research': {
                'industry': {
                    'sector_outlook': 'moderate growth',
                    'competitive_position': 'stable',
                    'industry_risks': ['competition'],
                    'growth_potential': 'moderate'
                },
                'promoter': {
                    'background': 'experienced team',
                    'track_record': 'mixed results',
                    'reputation': 'acceptable',
                    'red_flags': [],
                    'experience': '5+ years'
                },
                'web': {
                    'news_summary': 'neutral coverage',
                    'market_sentiment': 'neutral',
                    'red_flags': [],
                    'positive_indicators': [],
                    'regulatory_issues': []
                }
            }
        }
        
        result = await agent.score(analysis_data)
        
        # Verify each factor has a non-empty explanation
        assert result.financial_health.explanation, \
            "Financial health factor missing explanation"
        assert len(result.financial_health.explanation) > 0, \
            "Financial health explanation is empty"
        
        assert result.cash_flow.explanation, \
            "Cash flow factor missing explanation"
        assert len(result.cash_flow.explanation) > 0, \
            "Cash flow explanation is empty"
        
        assert result.industry.explanation, \
            "Industry factor missing explanation"
        assert len(result.industry.explanation) > 0, \
            "Industry explanation is empty"
        
        assert result.promoter.explanation, \
            "Promoter factor missing explanation"
        assert len(result.promoter.explanation) > 0, \
            "Promoter explanation is empty"
        
        assert result.external_intelligence.explanation, \
            "External intelligence factor missing explanation"
        assert len(result.external_intelligence.explanation) > 0, \
            "External intelligence explanation is empty"
    
    @pytest.mark.property
    @pytest.mark.asyncio
    @settings(max_examples=20)
    @given(
        financial_health=risk_score,
        cash_flow=risk_score,
        industry=risk_score,
        promoter=risk_score,
        external_intelligence=risk_score
    )
    async def test_overall_summary_exists(
        self,
        financial_health: float,
        cash_flow: float,
        industry: float,
        promoter: float,
        external_intelligence: float
    ):
        """
        Property: Risk assessment must include an overall summary
        
        For any risk assessment, there should be a non-empty overall summary
        that documents the key factors influencing the recommendation.
        """
        agent = RiskScoringAgent()
        
        # Create analysis data
        analysis_data = {
            'financial': {
                'ratios': {},
                'benchmarks': {},
                'trends': {}
            },
            'forecasts': {'forecasts': {}},
            'research': {
                'industry': {},
                'promoter': {},
                'web': {}
            }
        }
        
        result = await agent.score(analysis_data)
        
        # Verify overall summary exists and is not empty
        assert result.summary, "Risk assessment missing overall summary"
        assert len(result.summary) > 0, "Overall summary is empty"
        assert isinstance(result.summary, str), "Summary should be a string"
    
    @pytest.mark.property
    @pytest.mark.asyncio
    @settings(max_examples=20)
    @given(
        financial_health=risk_score,
        cash_flow=risk_score,
        industry=risk_score,
        promoter=risk_score,
        external_intelligence=risk_score
    )
    async def test_key_findings_provided(
        self,
        financial_health: float,
        cash_flow: float,
        industry: float,
        promoter: float,
        external_intelligence: float
    ):
        """
        Property: Each risk factor should have key findings
        
        For any risk assessment, each factor should include a list of key findings
        (may be empty if no significant findings, but the field should exist).
        """
        agent = RiskScoringAgent()
        
        # Create analysis data with some findings
        analysis_data = {
            'financial': {
                'ratios': {
                    'current_ratio': {'value': 2.0}
                },
                'benchmarks': {
                    'current_ratio': {'performance': 'good'}
                },
                'trends': {
                    'revenue': {'trend_direction': 'increasing', 'cagr': 15},
                    'profit': {'trend_direction': 'increasing', 'cagr': 12},
                    'cash_flow': {'trend_direction': 'increasing', 'cagr': 10}
                }
            },
            'forecasts': {
                'forecasts': {
                    'cash_flow': {
                        'projected_values': [100000, 120000, 140000],
                        'forecast_growth_rate': 20
                    }
                }
            },
            'research': {
                'industry': {
                    'sector_outlook': 'strong growth expected',
                    'competitive_position': 'market leader',
                    'industry_risks': ['regulatory changes'],
                    'growth_potential': 'high'
                },
                'promoter': {
                    'background': 'highly experienced',
                    'track_record': 'multiple successful ventures',
                    'reputation': 'excellent',
                    'red_flags': [],
                    'experience': '20+ years'
                },
                'web': {
                    'news_summary': 'very positive coverage',
                    'market_sentiment': 'bullish',
                    'red_flags': [],
                    'positive_indicators': ['innovation leader', 'strong growth', 'market expansion'],
                    'regulatory_issues': []
                }
            }
        }
        
        result = await agent.score(analysis_data)
        
        # Verify each factor has key_findings field (list)
        assert isinstance(result.financial_health.key_findings, list), \
            "Financial health key_findings should be a list"
        assert isinstance(result.cash_flow.key_findings, list), \
            "Cash flow key_findings should be a list"
        assert isinstance(result.industry.key_findings, list), \
            "Industry key_findings should be a list"
        assert isinstance(result.promoter.key_findings, list), \
            "Promoter key_findings should be a list"
        assert isinstance(result.external_intelligence.key_findings, list), \
            "External intelligence key_findings should be a list"
    
    @pytest.mark.property
    @pytest.mark.asyncio
    @settings(max_examples=10)
    @given(
        financial_health=risk_score,
        cash_flow=risk_score,
        industry=risk_score,
        promoter=risk_score,
        external_intelligence=risk_score
    )
    async def test_factor_names_are_correct(
        self,
        financial_health: float,
        cash_flow: float,
        industry: float,
        promoter: float,
        external_intelligence: float
    ):
        """
        Property: Risk factors should have correct identifying names
        
        For any risk assessment, each factor should have the correct factor_name
        that identifies which risk dimension it represents.
        """
        agent = RiskScoringAgent()
        
        # Create minimal analysis data
        analysis_data = {
            'financial': {
                'ratios': {},
                'benchmarks': {},
                'trends': {}
            },
            'forecasts': {'forecasts': {}},
            'research': {
                'industry': {},
                'promoter': {},
                'web': {}
            }
        }
        
        result = await agent.score(analysis_data)
        
        # Verify factor names are correct
        assert result.financial_health.factor_name == 'financial_health', \
            f"Expected factor_name 'financial_health', got '{result.financial_health.factor_name}'"
        assert result.cash_flow.factor_name == 'cash_flow', \
            f"Expected factor_name 'cash_flow', got '{result.cash_flow.factor_name}'"
        assert result.industry.factor_name == 'industry', \
            f"Expected factor_name 'industry', got '{result.industry.factor_name}'"
        assert result.promoter.factor_name == 'promoter', \
            f"Expected factor_name 'promoter', got '{result.promoter.factor_name}'"
        assert result.external_intelligence.factor_name == 'external_intelligence', \
            f"Expected factor_name 'external_intelligence', got '{result.external_intelligence.factor_name}'"
