"""
Tests for ForecastingAgent

This module contains unit tests for the ForecastingAgent class.
"""

import pytest
from app.agents.forecasting_agent import ForecastingAgent


@pytest.fixture
def forecasting_agent():
    """Create a ForecastingAgent instance for testing."""
    return ForecastingAgent()


@pytest.fixture
def sample_financial_data():
    """Sample financial data for testing."""
    return {
        "historical": {
            "revenue": {
                "values": [1000000, 1100000, 1250000, 1400000],
                "years": ["2020", "2021", "2022", "2023"]
            },
            "profit": {
                "values": [100000, 120000, 140000, 160000],
                "years": ["2020", "2021", "2022", "2023"]
            },
            "cash_flow": {
                "values": [150000, 160000, 180000, 200000],
                "years": ["2020", "2021", "2022", "2023"]
            },
            "debt": {
                "values": [500000, 480000, 450000, 420000],
                "years": ["2020", "2021", "2022", "2023"]
            }
        },
        "company_info": {
            "company_name": "Test Company Inc.",
            "industry": "technology"
        }
    }


@pytest.mark.asyncio
async def test_forecasting_agent_initialization(forecasting_agent):
    """Test that ForecastingAgent initializes correctly."""
    assert forecasting_agent is not None
    assert forecasting_agent.openai is not None
    assert forecasting_agent.time_series_analyzer is not None


@pytest.mark.asyncio
async def test_predict_with_valid_data(forecasting_agent, sample_financial_data):
    """Test forecast generation with valid financial data."""
    result = await forecasting_agent.predict(sample_financial_data)
    
    # Verify result structure
    assert "forecasts" in result
    assert "assumptions" in result
    assert "methodology" in result
    assert "confidence_level" in result
    assert "generated_at" in result
    
    # Verify forecasts were generated
    forecasts = result["forecasts"]
    assert "revenue" in forecasts
    assert "profit" in forecasts
    assert "cash_flow" in forecasts
    assert "debt" in forecasts
    
    # Verify each forecast has required fields
    for metric_name, forecast in forecasts.items():
        assert "projected_values" in forecast
        assert "forecast_growth_rate" in forecast
        assert "confidence_intervals" in forecast
        assert len(forecast["projected_values"]) == 3  # 3-year projections
        assert len(forecast["confidence_intervals"]) == 3


@pytest.mark.asyncio
async def test_predict_with_minimal_data(forecasting_agent):
    """Test forecast generation with minimal historical data."""
    minimal_data = {
        "historical": {
            "revenue": {
                "values": [1000000, 1100000],
                "years": ["2022", "2023"]
            }
        },
        "company_info": {
            "company_name": "Minimal Data Co.",
            "industry": "default"
        }
    }
    
    result = await forecasting_agent.predict(minimal_data)
    
    # Should still generate forecasts
    assert "forecasts" in result
    assert "revenue" in result["forecasts"]
    
    # Confidence should be lower with less data
    assert result["confidence_level"] < 80


@pytest.mark.asyncio
async def test_predict_with_no_data(forecasting_agent):
    """Test forecast generation with no financial data."""
    result = await forecasting_agent.predict({})
    
    # Should return empty result with reason
    assert "forecasts" in result
    assert len(result["forecasts"]) == 0
    assert result["confidence_level"] == 0.0


@pytest.mark.asyncio
async def test_confidence_intervals_widen_over_time(forecasting_agent, sample_financial_data):
    """Test that confidence intervals widen with forecast horizon."""
    result = await forecasting_agent.predict(sample_financial_data)
    
    revenue_forecast = result["forecasts"]["revenue"]
    confidence_intervals = revenue_forecast["confidence_intervals"]
    
    # Calculate interval widths
    widths = [
        ci["upper_bound"] - ci["lower_bound"]
        for ci in confidence_intervals
    ]
    
    # Verify widths increase over time
    assert widths[1] > widths[0]
    assert widths[2] > widths[1]


@pytest.mark.asyncio
async def test_assumptions_documented(forecasting_agent, sample_financial_data):
    """Test that assumptions are properly documented."""
    result = await forecasting_agent.predict(sample_financial_data)
    
    assumptions = result["assumptions"]
    
    # Should have multiple assumptions
    assert len(assumptions) >= 5
    
    # Should mention key assumption categories
    assumptions_text = " ".join(assumptions).lower()
    assert "historical" in assumptions_text or "trend" in assumptions_text
    assert "industry" in assumptions_text or "growth" in assumptions_text


@pytest.mark.asyncio
async def test_methodology_documented(forecasting_agent, sample_financial_data):
    """Test that methodology is properly documented."""
    result = await forecasting_agent.predict(sample_financial_data)
    
    methodology = result["methodology"]
    
    # Should be non-empty
    assert len(methodology) > 100
    
    # Should mention key methodology components
    methodology_lower = methodology.lower()
    assert "historical" in methodology_lower
    assert "industry" in methodology_lower or "benchmark" in methodology_lower
    assert "confidence" in methodology_lower


@pytest.mark.asyncio
async def test_industry_specific_growth_rates(forecasting_agent):
    """Test that industry-specific growth rates are applied."""
    tech_data = {
        "historical": {
            "revenue": {
                "values": [1000000, 1100000, 1200000],
                "years": ["2021", "2022", "2023"]
            }
        },
        "company_info": {
            "industry": "technology"
        }
    }
    
    retail_data = {
        "historical": {
            "revenue": {
                "values": [1000000, 1100000, 1200000],
                "years": ["2021", "2022", "2023"]
            }
        },
        "company_info": {
            "industry": "retail"
        }
    }
    
    tech_result = await forecasting_agent.predict(tech_data)
    retail_result = await forecasting_agent.predict(retail_data)
    
    # Technology should have higher growth rates than retail
    tech_growth = tech_result["industry_growth_rates"]["revenue_growth"]
    retail_growth = retail_result["industry_growth_rates"]["revenue_growth"]
    
    assert tech_growth > retail_growth


@pytest.mark.asyncio
async def test_forecast_uses_historical_trends(forecasting_agent):
    """Test that forecasts incorporate historical trends."""
    # Data with strong growth trend
    growth_data = {
        "historical": {
            "revenue": {
                "values": [1000000, 1500000, 2250000, 3375000],  # 50% CAGR
                "years": ["2020", "2021", "2022", "2023"]
            }
        },
        "company_info": {
            "industry": "default"
        }
    }
    
    result = await forecasting_agent.predict(growth_data)
    
    revenue_forecast = result["forecasts"]["revenue"]
    projected_values = revenue_forecast["projected_values"]
    
    # First projection should be significantly higher than last historical value
    # due to strong historical growth
    last_historical = 3375000
    first_projection = projected_values[0]
    
    growth_rate = ((first_projection - last_historical) / last_historical) * 100
    
    # Should show substantial growth (at least 20% given the strong historical trend)
    assert growth_rate > 20


def test_extract_industry(forecasting_agent):
    """Test industry extraction from financial data."""
    # Test with valid industry
    data1 = {"company_info": {"industry": "Technology"}}
    assert forecasting_agent._extract_industry(data1) == "technology"
    
    # Test with missing industry
    data2 = {"company_info": {}}
    assert forecasting_agent._extract_industry(data2) == "default"
    
    # Test with no company_info
    data3 = {}
    assert forecasting_agent._extract_industry(data3) == "default"


def test_get_industry_growth_rates(forecasting_agent):
    """Test retrieval of industry-specific growth rates."""
    # Test known industry
    tech_rates = forecasting_agent._get_industry_growth_rates("technology")
    assert tech_rates["revenue_growth"] == 15.0
    
    # Test default industry
    default_rates = forecasting_agent._get_industry_growth_rates("unknown_industry")
    assert default_rates["revenue_growth"] == 5.0


@pytest.mark.asyncio
async def test_confidence_level_calculation(forecasting_agent, sample_financial_data):
    """Test that confidence level is calculated appropriately."""
    result = await forecasting_agent.predict(sample_financial_data)
    
    confidence = result["confidence_level"]
    
    # Confidence should be between 0 and 100
    assert 0 <= confidence <= 100
    
    # With 4 years of data and consistent trends, confidence should be reasonably high
    assert confidence > 60


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
