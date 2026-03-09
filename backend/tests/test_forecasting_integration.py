"""
Integration tests for ForecastingAgent

This module demonstrates the ForecastingAgent working with realistic financial data
and validates the complete forecasting workflow.
"""

import pytest
from app.agents.forecasting_agent import ForecastingAgent


@pytest.fixture
def forecasting_agent():
    """Create a ForecastingAgent instance for testing."""
    return ForecastingAgent()


@pytest.fixture
def realistic_financial_data():
    """Realistic financial data for a growing technology company."""
    return {
        "historical": {
            "revenue": {
                "values": [5000000, 6500000, 8450000, 10985000, 14280500],
                "years": ["2019", "2020", "2021", "2022", "2023"]
            },
            "profit": {
                "values": [500000, 715000, 1014250, 1460000, 2071400],
                "years": ["2019", "2020", "2021", "2022", "2023"]
            },
            "cash_flow": {
                "values": [750000, 975000, 1267500, 1647750, 2142075],
                "years": ["2019", "2020", "2021", "2022", "2023"]
            },
            "debt": {
                "values": [2000000, 1800000, 1500000, 1200000, 900000],
                "years": ["2019", "2020", "2021", "2022", "2023"]
            }
        },
        "company_info": {
            "company_name": "TechGrowth Solutions Inc.",
            "industry": "technology",
            "location": "San Francisco, CA"
        },
        "financial_analysis": {
            "ratios": {
                "current_ratio": {"value": 2.5},
                "debt_to_equity": {"value": 0.3},
                "roe": {"value": 0.18}
            }
        }
    }


@pytest.mark.asyncio
async def test_complete_forecasting_workflow(forecasting_agent, realistic_financial_data):
    """
    Test the complete forecasting workflow with realistic data.
    
    This test validates:
    - Forecast generation for all metrics
    - 3-year projections
    - Confidence intervals
    - Assumption documentation
    - Methodology documentation
    """
    result = await forecasting_agent.predict(realistic_financial_data)
    
    # Validate overall structure
    assert result is not None
    assert "forecasts" in result
    assert "assumptions" in result
    assert "methodology" in result
    assert "confidence_level" in result
    assert "generated_at" in result
    
    # Validate forecasts for all metrics
    forecasts = result["forecasts"]
    assert "revenue" in forecasts
    assert "profit" in forecasts
    assert "cash_flow" in forecasts
    assert "debt" in forecasts
    
    # Validate revenue forecast
    revenue_forecast = forecasts["revenue"]
    assert "projected_values" in revenue_forecast
    assert "confidence_intervals" in revenue_forecast
    assert len(revenue_forecast["projected_values"]) == 3
    
    # Revenue should continue growing (based on strong historical trend)
    last_historical_revenue = 14280500
    first_projected_revenue = revenue_forecast["projected_values"][0]
    assert first_projected_revenue > last_historical_revenue
    
    # Validate profit forecast
    profit_forecast = forecasts["profit"]
    assert len(profit_forecast["projected_values"]) == 3
    
    # Profit should also grow
    last_historical_profit = 2071400
    first_projected_profit = profit_forecast["projected_values"][0]
    assert first_projected_profit > last_historical_profit
    
    # Validate debt forecast
    debt_forecast = forecasts["debt"]
    assert len(debt_forecast["projected_values"]) == 3
    
    # Debt should continue declining (based on historical trend)
    last_historical_debt = 900000
    first_projected_debt = debt_forecast["projected_values"][0]
    # Debt might continue declining or stabilize
    assert first_projected_debt <= last_historical_debt * 1.1  # Allow small increase
    
    # Validate confidence level
    confidence = result["confidence_level"]
    assert 0 <= confidence <= 100
    # With 5 years of consistent data, confidence should be high
    assert confidence > 70
    
    # Validate assumptions
    assumptions = result["assumptions"]
    assert len(assumptions) >= 5
    assert any("historical" in a.lower() for a in assumptions)
    assert any("industry" in a.lower() for a in assumptions)
    
    # Validate methodology
    methodology = result["methodology"]
    assert len(methodology) > 100
    assert "historical" in methodology.lower()
    assert "confidence" in methodology.lower()


@pytest.mark.asyncio
async def test_forecasting_with_declining_business(forecasting_agent):
    """Test forecasting for a business with declining performance."""
    declining_data = {
        "historical": {
            "revenue": {
                "values": [10000000, 9500000, 8800000, 8000000],
                "years": ["2020", "2021", "2022", "2023"]
            },
            "profit": {
                "values": [1000000, 850000, 650000, 400000],
                "years": ["2020", "2021", "2022", "2023"]
            }
        },
        "company_info": {
            "company_name": "Declining Corp",
            "industry": "retail"
        }
    }
    
    result = await forecasting_agent.predict(declining_data)
    
    # Should still generate forecasts
    assert "forecasts" in result
    assert "revenue" in result["forecasts"]
    
    revenue_forecast = result["forecasts"]["revenue"]
    
    # Projections should reflect declining trend
    # (though industry benchmarks might moderate the decline)
    last_historical = 8000000
    projections = revenue_forecast["projected_values"]
    
    # At least the first projection should show continued decline or modest recovery
    # (blended with industry growth rates)
    assert projections[0] < last_historical * 1.15  # Not unrealistic growth


@pytest.mark.asyncio
async def test_forecasting_with_volatile_data(forecasting_agent):
    """Test forecasting with volatile historical data."""
    volatile_data = {
        "historical": {
            "revenue": {
                "values": [5000000, 7000000, 5500000, 8000000, 6000000],
                "years": ["2019", "2020", "2021", "2022", "2023"]
            }
        },
        "company_info": {
            "company_name": "Volatile Inc",
            "industry": "default"
        }
    }
    
    result = await forecasting_agent.predict(volatile_data)
    
    # Should generate forecasts
    assert "forecasts" in result
    assert "revenue" in result["forecasts"]
    
    # Confidence should be lower due to volatility
    assert result["confidence_level"] < 75
    
    # Confidence intervals should be wider
    revenue_forecast = result["forecasts"]["revenue"]
    confidence_intervals = revenue_forecast["confidence_intervals"]
    
    # Calculate average interval width
    avg_width = sum(
        ci["upper_bound"] - ci["lower_bound"]
        for ci in confidence_intervals
    ) / len(confidence_intervals)
    
    # Width should be substantial (at least 20% of projected value)
    avg_projection = sum(revenue_forecast["projected_values"]) / 3
    assert avg_width > avg_projection * 0.2


@pytest.mark.asyncio
async def test_industry_impact_on_forecasts(forecasting_agent):
    """Test that industry classification impacts forecasts appropriately."""
    base_data = {
        "historical": {
            "revenue": {
                "values": [1000000, 1050000, 1100000],
                "years": ["2021", "2022", "2023"]
            }
        },
        "company_info": {
            "company_name": "Test Company"
        }
    }
    
    # Test with technology industry (high growth)
    tech_data = {**base_data}
    tech_data["company_info"]["industry"] = "technology"
    tech_result = await forecasting_agent.predict(tech_data)
    
    # Test with retail industry (lower growth)
    retail_data = {**base_data}
    retail_data["company_info"]["industry"] = "retail"
    retail_result = await forecasting_agent.predict(retail_data)
    
    # Technology forecast should show higher growth
    tech_revenue = tech_result["forecasts"]["revenue"]["projected_values"][0]
    retail_revenue = retail_result["forecasts"]["revenue"]["projected_values"][0]
    
    assert tech_revenue > retail_revenue


@pytest.mark.asyncio
async def test_forecast_output_format(forecasting_agent, realistic_financial_data):
    """Test that forecast output has the correct format for downstream use."""
    result = await forecasting_agent.predict(realistic_financial_data)
    
    # Validate that each forecast has all required fields for visualization
    for metric_name, forecast in result["forecasts"].items():
        # Required for charting
        assert "historical_values" in forecast
        assert "historical_years" in forecast
        assert "projected_values" in forecast
        assert "projected_years" in forecast
        
        # Required for analysis
        assert "forecast_growth_rate" in forecast
        assert "confidence_intervals" in forecast
        
        # Each confidence interval should have bounds
        for ci in forecast["confidence_intervals"]:
            assert "lower_bound" in ci
            assert "upper_bound" in ci
            assert "confidence_level" in ci
            
            # Bounds should be reasonable
            assert ci["lower_bound"] < ci["upper_bound"]
            assert 0 <= ci["confidence_level"] <= 100


@pytest.mark.asyncio
async def test_assumptions_include_key_factors(forecasting_agent, realistic_financial_data):
    """Test that assumptions cover all key forecasting factors."""
    result = await forecasting_agent.predict(realistic_financial_data)
    
    assumptions = result["assumptions"]
    assumptions_text = " ".join(assumptions).lower()
    
    # Should mention historical trends
    assert "historical" in assumptions_text or "trend" in assumptions_text
    
    # Should mention industry factors
    assert "industry" in assumptions_text
    
    # Should mention economic conditions
    assert "economic" in assumptions_text or "growth" in assumptions_text
    
    # Should mention data quality/confidence
    assert "data" in assumptions_text or "confidence" in assumptions_text
    
    # Should mention methodology
    assert "blend" in assumptions_text or "weight" in assumptions_text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
