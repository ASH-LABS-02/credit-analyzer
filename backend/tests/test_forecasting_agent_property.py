"""
Property-based tests for ForecastingAgent

Feature: intelli-credit-platform
Property 10: Forecast Completeness
Property 11: Forecast Methodology Validation

Validates: Requirements 5.1, 5.2, 5.3, 5.5
"""

import pytest
from hypothesis import given, strategies as st, assume, settings, HealthCheck
from unittest.mock import AsyncMock, MagicMock, patch
from app.agents.forecasting_agent import ForecastingAgent


# Strategy for generating positive financial values
positive_value = st.floats(min_value=1000.0, max_value=1e10, allow_nan=False, allow_infinity=False)

# Strategy for generating time series length (2-5 years for sufficient historical data)
time_series_length = st.integers(min_value=2, max_value=5)

# Hypothesis settings for property tests
property_test_settings = settings(
    max_examples=20,  # Reduced for faster test execution
    deadline=None,  # Disable deadline for async tests with API calls
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)


def generate_historical_financial_data(
    revenue_values: list,
    profit_values: list,
    cash_flow_values: list,
    debt_values: list,
    industry: str = "default"
):
    """Generate historical financial data structure for testing."""
    years = [str(2020 + i) for i in range(len(revenue_values))]
    
    return {
        "historical": {
            "revenue": {
                "values": revenue_values,
                "years": years
            },
            "profit": {
                "values": profit_values,
                "years": years
            },
            "cash_flow": {
                "values": cash_flow_values,
                "years": years
            },
            "debt": {
                "values": debt_values,
                "years": years
            }
        },
        "company_info": {
            "company_name": "Test Company Inc.",
            "industry": industry
        }
    }


class TestProperty10ForecastCompleteness:
    """
    Property 10: Forecast Completeness
    
    For any application with sufficient historical data, the Forecasting Agent
    should generate 3-year projections for all required metrics (revenue, profit,
    cash flow, debt) with confidence levels and documented assumptions.
    
    Validates: Requirements 5.1, 5.3, 5.5
    """
    
    @pytest.mark.property
    @pytest.mark.asyncio
    @property_test_settings
    @given(
        num_years=time_series_length,
        revenue_base=positive_value,
        profit_base=positive_value,
        cash_flow_base=positive_value,
        debt_base=positive_value,
        revenue_growth=st.floats(min_value=-0.2, max_value=0.5),
        profit_growth=st.floats(min_value=-0.3, max_value=0.6),
        cash_flow_growth=st.floats(min_value=-0.2, max_value=0.4),
        debt_growth=st.floats(min_value=-0.3, max_value=0.2)
    )
    async def test_forecast_generates_all_required_metrics(
        self,
        num_years: int,
        revenue_base: float,
        profit_base: float,
        cash_flow_base: float,
        debt_base: float,
        revenue_growth: float,
        profit_growth: float,
        cash_flow_growth: float,
        debt_growth: float
    ):
        """
        **Validates: Requirements 5.1**
        
        Property: For ANY application with sufficient historical data,
        the system SHALL generate 3-year projections for revenue, profit,
        cash flow, and debt levels.
        
        This test verifies that all required metrics are forecasted.
        """
        # Generate time series with growth patterns
        revenue_values = [revenue_base * ((1 + revenue_growth) ** i) for i in range(num_years)]
        profit_values = [profit_base * ((1 + profit_growth) ** i) for i in range(num_years)]
        cash_flow_values = [cash_flow_base * ((1 + cash_flow_growth) ** i) for i in range(num_years)]
        debt_values = [debt_base * ((1 + debt_growth) ** i) for i in range(num_years)]
        
        # Ensure all values remain positive
        revenue_values = [max(v, 1000.0) for v in revenue_values]
        profit_values = [max(v, 100.0) for v in profit_values]
        cash_flow_values = [max(v, 100.0) for v in cash_flow_values]
        debt_values = [max(v, 1000.0) for v in debt_values]
        
        financial_data = generate_historical_financial_data(
            revenue_values=revenue_values,
            profit_values=profit_values,
            cash_flow_values=cash_flow_values,
            debt_values=debt_values,
            industry="default"
        )
        
        agent = ForecastingAgent()
        result = await agent.predict(financial_data)
        
        # Verify forecasts dictionary exists
        assert "forecasts" in result, \
            "Result must include 'forecasts' dictionary (Requirement 5.1)"
        
        forecasts = result["forecasts"]
        
        # Verify all required metrics are forecasted (Requirement 5.1)
        required_metrics = ["revenue", "profit", "cash_flow", "debt"]
        for metric in required_metrics:
            assert metric in forecasts, \
                f"Forecast must include {metric} projections (Requirement 5.1)"
            
            forecast = forecasts[metric]
            
            # Verify each forecast has projected values
            assert "projected_values" in forecast, \
                f"{metric} forecast must include 'projected_values' (Requirement 5.1)"
            
            projected_values = forecast["projected_values"]
            
            # Verify 3-year projections (Requirement 5.1)
            assert len(projected_values) == 3, \
                f"{metric} must have exactly 3-year projections (Requirement 5.1)"
            
            # Verify all projected values are numeric
            for i, value in enumerate(projected_values):
                assert isinstance(value, (int, float)), \
                    f"{metric} projection year {i+1} must be numeric"
                assert not (value != value), \
                    f"{metric} projection year {i+1} must not be NaN"

    @pytest.mark.property
    @pytest.mark.asyncio
    @property_test_settings
    @given(
        num_years=time_series_length,
        revenue_base=positive_value,
        profit_base=positive_value,
        cash_flow_base=positive_value,
        debt_base=positive_value,
        revenue_growth=st.floats(min_value=-0.2, max_value=0.5),
        profit_growth=st.floats(min_value=-0.3, max_value=0.6),
        cash_flow_growth=st.floats(min_value=-0.2, max_value=0.4),
        debt_growth=st.floats(min_value=-0.3, max_value=0.2)
    )
    async def test_forecast_includes_confidence_intervals(
        self,
        num_years: int,
        revenue_base: float,
        profit_base: float,
        cash_flow_base: float,
        debt_base: float,
        revenue_growth: float,
        profit_growth: float,
        cash_flow_growth: float,
        debt_growth: float
    ):
        """
        **Validates: Requirements 5.3**
        
        Property: For ANY generated forecast, the system SHALL provide
        confidence intervals or uncertainty ranges.
        
        This test verifies that confidence intervals are provided for all forecasts.
        """
        # Generate time series with growth patterns
        revenue_values = [revenue_base * ((1 + revenue_growth) ** i) for i in range(num_years)]
        profit_values = [profit_base * ((1 + profit_growth) ** i) for i in range(num_years)]
        cash_flow_values = [cash_flow_base * ((1 + cash_flow_growth) ** i) for i in range(num_years)]
        debt_values = [debt_base * ((1 + debt_growth) ** i) for i in range(num_years)]
        
        # Ensure all values remain positive
        revenue_values = [max(v, 1000.0) for v in revenue_values]
        profit_values = [max(v, 100.0) for v in profit_values]
        cash_flow_values = [max(v, 100.0) for v in cash_flow_values]
        debt_values = [max(v, 1000.0) for v in debt_values]
        
        financial_data = generate_historical_financial_data(
            revenue_values=revenue_values,
            profit_values=profit_values,
            cash_flow_values=cash_flow_values,
            debt_values=debt_values,
            industry="default"
        )
        
        agent = ForecastingAgent()
        result = await agent.predict(financial_data)
        
        forecasts = result["forecasts"]
        
        # Verify confidence intervals for all metrics (Requirement 5.3)
        for metric_name, forecast in forecasts.items():
            assert "confidence_intervals" in forecast, \
                f"{metric_name} forecast must include 'confidence_intervals' (Requirement 5.3)"
            
            confidence_intervals = forecast["confidence_intervals"]
            
            # Verify 3 confidence intervals (one per year)
            assert len(confidence_intervals) == 3, \
                f"{metric_name} must have 3 confidence intervals (Requirement 5.3)"
            
            # Verify each confidence interval has required fields
            for i, ci in enumerate(confidence_intervals):
                assert "lower_bound" in ci, \
                    f"{metric_name} confidence interval {i+1} must have 'lower_bound' (Requirement 5.3)"
                assert "upper_bound" in ci, \
                    f"{metric_name} confidence interval {i+1} must have 'upper_bound' (Requirement 5.3)"
                assert "confidence_level" in ci, \
                    f"{metric_name} confidence interval {i+1} must have 'confidence_level' (Requirement 5.3)"
                
                # Verify bounds are numeric
                assert isinstance(ci["lower_bound"], (int, float)), \
                    f"{metric_name} lower_bound must be numeric"
                assert isinstance(ci["upper_bound"], (int, float)), \
                    f"{metric_name} upper_bound must be numeric"
                
                # Verify upper bound is greater than lower bound
                assert ci["upper_bound"] > ci["lower_bound"], \
                    f"{metric_name} upper_bound must be greater than lower_bound (Requirement 5.3)"
                
                # Verify confidence level is reasonable (0-100)
                assert 0 <= ci["confidence_level"] <= 100, \
                    f"{metric_name} confidence_level must be between 0 and 100"

    @pytest.mark.property
    @pytest.mark.asyncio
    @property_test_settings
    @given(
        num_years=time_series_length,
        revenue_base=positive_value,
        profit_base=positive_value,
        cash_flow_base=positive_value,
        debt_base=positive_value,
        revenue_growth=st.floats(min_value=-0.2, max_value=0.5),
        profit_growth=st.floats(min_value=-0.3, max_value=0.6),
        cash_flow_growth=st.floats(min_value=-0.2, max_value=0.4),
        debt_growth=st.floats(min_value=-0.3, max_value=0.2)
    )
    async def test_forecast_documents_assumptions(
        self,
        num_years: int,
        revenue_base: float,
        profit_base: float,
        cash_flow_base: float,
        debt_base: float,
        revenue_growth: float,
        profit_growth: float,
        cash_flow_growth: float,
        debt_growth: float
    ):
        """
        **Validates: Requirements 5.5**
        
        Property: For ALL forecasts, the system SHALL document the
        assumptions and methodology used.
        
        This test verifies that assumptions are properly documented.
        """
        # Generate time series with growth patterns
        revenue_values = [revenue_base * ((1 + revenue_growth) ** i) for i in range(num_years)]
        profit_values = [profit_base * ((1 + profit_growth) ** i) for i in range(num_years)]
        cash_flow_values = [cash_flow_base * ((1 + cash_flow_growth) ** i) for i in range(num_years)]
        debt_values = [debt_base * ((1 + debt_growth) ** i) for i in range(num_years)]
        
        # Ensure all values remain positive
        revenue_values = [max(v, 1000.0) for v in revenue_values]
        profit_values = [max(v, 100.0) for v in profit_values]
        cash_flow_values = [max(v, 100.0) for v in cash_flow_values]
        debt_values = [max(v, 1000.0) for v in debt_values]
        
        financial_data = generate_historical_financial_data(
            revenue_values=revenue_values,
            profit_values=profit_values,
            cash_flow_values=cash_flow_values,
            debt_values=debt_values,
            industry="technology"
        )
        
        agent = ForecastingAgent()
        result = await agent.predict(financial_data)
        
        # Verify assumptions are documented (Requirement 5.5)
        assert "assumptions" in result, \
            "Result must include 'assumptions' (Requirement 5.5)"
        
        assumptions = result["assumptions"]
        
        # Verify assumptions is a list
        assert isinstance(assumptions, list), \
            "Assumptions must be a list (Requirement 5.5)"
        
        # Verify assumptions list is not empty
        assert len(assumptions) > 0, \
            "Assumptions list must not be empty (Requirement 5.5)"
        
        # Verify each assumption is a non-empty string
        for i, assumption in enumerate(assumptions):
            assert isinstance(assumption, str), \
                f"Assumption {i+1} must be a string (Requirement 5.5)"
            assert len(assumption) > 0, \
                f"Assumption {i+1} must not be empty (Requirement 5.5)"
        
        # Verify key assumption categories are covered
        assumptions_text = " ".join(assumptions).lower()
        
        # Should mention historical trends
        assert any(keyword in assumptions_text for keyword in ["historical", "trend", "past"]), \
            "Assumptions must mention historical trends (Requirement 5.5)"
        
        # Should mention industry or growth rates
        assert any(keyword in assumptions_text for keyword in ["industry", "growth", "sector"]), \
            "Assumptions must mention industry factors (Requirement 5.5)"

    @pytest.mark.property
    @pytest.mark.asyncio
    @property_test_settings
    @given(
        num_years=time_series_length,
        revenue_base=positive_value,
        profit_base=positive_value,
        cash_flow_base=positive_value,
        debt_base=positive_value,
        revenue_growth=st.floats(min_value=-0.2, max_value=0.5),
        profit_growth=st.floats(min_value=-0.3, max_value=0.6),
        cash_flow_growth=st.floats(min_value=-0.2, max_value=0.4),
        debt_growth=st.floats(min_value=-0.3, max_value=0.2)
    )
    async def test_forecast_includes_overall_confidence_level(
        self,
        num_years: int,
        revenue_base: float,
        profit_base: float,
        cash_flow_base: float,
        debt_base: float,
        revenue_growth: float,
        profit_growth: float,
        cash_flow_growth: float,
        debt_growth: float
    ):
        """
        **Validates: Requirements 5.1, 5.3**
        
        Property: For ANY application with sufficient historical data,
        the system SHALL provide an overall confidence level for forecasts.
        
        This test verifies that an overall confidence level is calculated.
        """
        # Generate time series with growth patterns
        revenue_values = [revenue_base * ((1 + revenue_growth) ** i) for i in range(num_years)]
        profit_values = [profit_base * ((1 + profit_growth) ** i) for i in range(num_years)]
        cash_flow_values = [cash_flow_base * ((1 + cash_flow_growth) ** i) for i in range(num_years)]
        debt_values = [debt_base * ((1 + debt_growth) ** i) for i in range(num_years)]
        
        # Ensure all values remain positive
        revenue_values = [max(v, 1000.0) for v in revenue_values]
        profit_values = [max(v, 100.0) for v in profit_values]
        cash_flow_values = [max(v, 100.0) for v in cash_flow_values]
        debt_values = [max(v, 1000.0) for v in debt_values]
        
        financial_data = generate_historical_financial_data(
            revenue_values=revenue_values,
            profit_values=profit_values,
            cash_flow_values=cash_flow_values,
            debt_values=debt_values,
            industry="default"
        )
        
        agent = ForecastingAgent()
        result = await agent.predict(financial_data)
        
        # Verify confidence level exists (Requirement 5.1, 5.3)
        assert "confidence_level" in result, \
            "Result must include 'confidence_level' (Requirement 5.1, 5.3)"
        
        confidence_level = result["confidence_level"]
        
        # Verify confidence level is numeric
        assert isinstance(confidence_level, (int, float)), \
            "Confidence level must be numeric (Requirement 5.3)"
        
        # Verify confidence level is in valid range (0-100)
        assert 0 <= confidence_level <= 100, \
            "Confidence level must be between 0 and 100 (Requirement 5.3)"


class TestProperty11ForecastMethodologyValidation:
    """
    Property 11: Forecast Methodology Validation
    
    For any generated forecast, the system should incorporate historical trends,
    industry growth rates, and economic indicators as inputs to the forecasting model.
    
    Validates: Requirements 5.2
    """
    
    @pytest.mark.property
    @pytest.mark.asyncio
    @property_test_settings
    @given(
        num_years=time_series_length,
        revenue_base=positive_value,
        profit_base=positive_value,
        cash_flow_base=positive_value,
        debt_base=positive_value,
        revenue_growth=st.floats(min_value=-0.2, max_value=0.5),
        profit_growth=st.floats(min_value=-0.3, max_value=0.6),
        cash_flow_growth=st.floats(min_value=-0.2, max_value=0.4),
        debt_growth=st.floats(min_value=-0.3, max_value=0.2),
        industry=st.sampled_from(["technology", "manufacturing", "retail", "financial_services", "default"])
    )
    async def test_forecast_incorporates_historical_trends(
        self,
        num_years: int,
        revenue_base: float,
        profit_base: float,
        cash_flow_base: float,
        debt_base: float,
        revenue_growth: float,
        profit_growth: float,
        cash_flow_growth: float,
        debt_growth: float,
        industry: str
    ):
        """
        **Validates: Requirements 5.2**
        
        Property: For ANY generated forecast, the system SHALL incorporate
        historical trends as inputs to the forecasting model.
        
        This test verifies that historical data is analyzed and used in forecasting.
        """
        # Generate time series with growth patterns
        revenue_values = [revenue_base * ((1 + revenue_growth) ** i) for i in range(num_years)]
        profit_values = [profit_base * ((1 + profit_growth) ** i) for i in range(num_years)]
        cash_flow_values = [cash_flow_base * ((1 + cash_flow_growth) ** i) for i in range(num_years)]
        debt_values = [debt_base * ((1 + debt_growth) ** i) for i in range(num_years)]
        
        # Ensure all values remain positive
        revenue_values = [max(v, 1000.0) for v in revenue_values]
        profit_values = [max(v, 100.0) for v in profit_values]
        cash_flow_values = [max(v, 100.0) for v in cash_flow_values]
        debt_values = [max(v, 1000.0) for v in debt_values]
        
        financial_data = generate_historical_financial_data(
            revenue_values=revenue_values,
            profit_values=profit_values,
            cash_flow_values=cash_flow_values,
            debt_values=debt_values,
            industry=industry
        )
        
        agent = ForecastingAgent()
        result = await agent.predict(financial_data)
        
        forecasts = result["forecasts"]
        
        # Verify each forecast includes historical data reference (Requirement 5.2)
        for metric_name, forecast in forecasts.items():
            assert "historical_values" in forecast, \
                f"{metric_name} forecast must include 'historical_values' (Requirement 5.2)"
            
            historical_values = forecast["historical_values"]
            
            # Verify historical values match input data
            assert len(historical_values) > 0, \
                f"{metric_name} must have historical values (Requirement 5.2)"
            
            # Verify forecast growth rate is calculated
            assert "forecast_growth_rate" in forecast, \
                f"{metric_name} forecast must include 'forecast_growth_rate' (Requirement 5.2)"
            
            # Verify methodology mentions historical trends
            assert "methodology" in forecast, \
                f"{metric_name} forecast must include 'methodology' (Requirement 5.2)"
            
            methodology = forecast["methodology"].lower()
            assert any(keyword in methodology for keyword in ["historical", "trend", "growth"]), \
                f"{metric_name} methodology must mention historical trends (Requirement 5.2)"

    @pytest.mark.property
    @pytest.mark.asyncio
    @property_test_settings
    @given(
        num_years=time_series_length,
        revenue_base=positive_value,
        profit_base=positive_value,
        cash_flow_base=positive_value,
        debt_base=positive_value,
        revenue_growth=st.floats(min_value=-0.2, max_value=0.5),
        profit_growth=st.floats(min_value=-0.3, max_value=0.6),
        cash_flow_growth=st.floats(min_value=-0.2, max_value=0.4),
        debt_growth=st.floats(min_value=-0.3, max_value=0.2),
        industry=st.sampled_from(["technology", "manufacturing", "retail", "financial_services", "default"])
    )
    async def test_forecast_incorporates_industry_growth_rates(
        self,
        num_years: int,
        revenue_base: float,
        profit_base: float,
        cash_flow_base: float,
        debt_base: float,
        revenue_growth: float,
        profit_growth: float,
        cash_flow_growth: float,
        debt_growth: float,
        industry: str
    ):
        """
        **Validates: Requirements 5.2**
        
        Property: For ANY generated forecast, the system SHALL incorporate
        industry growth rates as inputs to the forecasting model.
        
        This test verifies that industry-specific growth rates are used.
        """
        # Generate time series with growth patterns
        revenue_values = [revenue_base * ((1 + revenue_growth) ** i) for i in range(num_years)]
        profit_values = [profit_base * ((1 + profit_growth) ** i) for i in range(num_years)]
        cash_flow_values = [cash_flow_base * ((1 + cash_flow_growth) ** i) for i in range(num_years)]
        debt_values = [debt_base * ((1 + debt_growth) ** i) for i in range(num_years)]
        
        # Ensure all values remain positive
        revenue_values = [max(v, 1000.0) for v in revenue_values]
        profit_values = [max(v, 100.0) for v in profit_values]
        cash_flow_values = [max(v, 100.0) for v in cash_flow_values]
        debt_values = [max(v, 1000.0) for v in debt_values]
        
        financial_data = generate_historical_financial_data(
            revenue_values=revenue_values,
            profit_values=profit_values,
            cash_flow_values=cash_flow_values,
            debt_values=debt_values,
            industry=industry
        )
        
        agent = ForecastingAgent()
        result = await agent.predict(financial_data)
        
        # Verify industry growth rates are included (Requirement 5.2)
        assert "industry_growth_rates" in result, \
            "Result must include 'industry_growth_rates' (Requirement 5.2)"
        
        industry_growth_rates = result["industry_growth_rates"]
        
        # Verify industry growth rates structure
        assert isinstance(industry_growth_rates, dict), \
            "Industry growth rates must be a dictionary (Requirement 5.2)"
        
        # Verify key growth rate fields exist
        assert "revenue_growth" in industry_growth_rates, \
            "Industry growth rates must include 'revenue_growth' (Requirement 5.2)"
        assert "profit_growth" in industry_growth_rates, \
            "Industry growth rates must include 'profit_growth' (Requirement 5.2)"
        
        # Verify growth rates are numeric
        assert isinstance(industry_growth_rates["revenue_growth"], (int, float)), \
            "Revenue growth rate must be numeric (Requirement 5.2)"
        assert isinstance(industry_growth_rates["profit_growth"], (int, float)), \
            "Profit growth rate must be numeric (Requirement 5.2)"
        
        # Verify industry is documented
        assert "industry" in result, \
            "Result must include 'industry' (Requirement 5.2)"
        
        # Verify assumptions mention industry growth rates
        assumptions = result.get("assumptions", [])
        assumptions_text = " ".join(assumptions).lower()
        assert "industry" in assumptions_text, \
            "Assumptions must mention industry growth rates (Requirement 5.2)"

    @pytest.mark.property
    @pytest.mark.asyncio
    @property_test_settings
    @given(
        num_years=time_series_length,
        revenue_base=positive_value,
        profit_base=positive_value,
        cash_flow_base=positive_value,
        debt_base=positive_value,
        revenue_growth=st.floats(min_value=-0.2, max_value=0.5),
        profit_growth=st.floats(min_value=-0.3, max_value=0.6),
        cash_flow_growth=st.floats(min_value=-0.2, max_value=0.4),
        debt_growth=st.floats(min_value=-0.3, max_value=0.2),
        industry=st.sampled_from(["technology", "manufacturing", "retail", "financial_services", "default"])
    )
    async def test_forecast_incorporates_economic_indicators(
        self,
        num_years: int,
        revenue_base: float,
        profit_base: float,
        cash_flow_base: float,
        debt_base: float,
        revenue_growth: float,
        profit_growth: float,
        cash_flow_growth: float,
        debt_growth: float,
        industry: str
    ):
        """
        **Validates: Requirements 5.2**
        
        Property: For ANY generated forecast, the system SHALL incorporate
        economic indicators as inputs to the forecasting model.
        
        This test verifies that economic indicators are considered.
        """
        # Generate time series with growth patterns
        revenue_values = [revenue_base * ((1 + revenue_growth) ** i) for i in range(num_years)]
        profit_values = [profit_base * ((1 + profit_growth) ** i) for i in range(num_years)]
        cash_flow_values = [cash_flow_base * ((1 + cash_flow_growth) ** i) for i in range(num_years)]
        debt_values = [debt_base * ((1 + debt_growth) ** i) for i in range(num_years)]
        
        # Ensure all values remain positive
        revenue_values = [max(v, 1000.0) for v in revenue_values]
        profit_values = [max(v, 100.0) for v in profit_values]
        cash_flow_values = [max(v, 100.0) for v in cash_flow_values]
        debt_values = [max(v, 1000.0) for v in debt_values]
        
        financial_data = generate_historical_financial_data(
            revenue_values=revenue_values,
            profit_values=profit_values,
            cash_flow_values=cash_flow_values,
            debt_values=debt_values,
            industry=industry
        )
        
        agent = ForecastingAgent()
        result = await agent.predict(financial_data)
        
        # Verify economic indicators are included (Requirement 5.2)
        industry_growth_rates = result.get("industry_growth_rates", {})
        
        # Economic growth rate should be included
        assert "economic_growth" in industry_growth_rates, \
            "Industry growth rates must include 'economic_growth' indicator (Requirement 5.2)"
        
        economic_growth = industry_growth_rates["economic_growth"]
        
        # Verify economic growth is numeric
        assert isinstance(economic_growth, (int, float)), \
            "Economic growth indicator must be numeric (Requirement 5.2)"
        
        # Verify assumptions mention economic indicators
        assumptions = result.get("assumptions", [])
        assumptions_text = " ".join(assumptions).lower()
        assert any(keyword in assumptions_text for keyword in ["economic", "gdp", "economy"]), \
            "Assumptions must mention economic indicators (Requirement 5.2)"
    
    @pytest.mark.property
    @pytest.mark.asyncio
    @property_test_settings
    @given(
        num_years=time_series_length,
        revenue_base=positive_value,
        profit_base=positive_value,
        cash_flow_base=positive_value,
        debt_base=positive_value,
        revenue_growth=st.floats(min_value=-0.2, max_value=0.5),
        profit_growth=st.floats(min_value=-0.3, max_value=0.6),
        cash_flow_growth=st.floats(min_value=-0.2, max_value=0.4),
        debt_growth=st.floats(min_value=-0.3, max_value=0.2)
    )
    async def test_forecast_methodology_documented(
        self,
        num_years: int,
        revenue_base: float,
        profit_base: float,
        cash_flow_base: float,
        debt_base: float,
        revenue_growth: float,
        profit_growth: float,
        cash_flow_growth: float,
        debt_growth: float
    ):
        """
        **Validates: Requirements 5.5**
        
        Property: For ALL forecasts, the system SHALL document the methodology used.
        
        This test verifies that the forecasting methodology is properly documented.
        """
        # Generate time series with growth patterns
        revenue_values = [revenue_base * ((1 + revenue_growth) ** i) for i in range(num_years)]
        profit_values = [profit_base * ((1 + profit_growth) ** i) for i in range(num_years)]
        cash_flow_values = [cash_flow_base * ((1 + cash_flow_growth) ** i) for i in range(num_years)]
        debt_values = [debt_base * ((1 + debt_growth) ** i) for i in range(num_years)]
        
        # Ensure all values remain positive
        revenue_values = [max(v, 1000.0) for v in revenue_values]
        profit_values = [max(v, 100.0) for v in profit_values]
        cash_flow_values = [max(v, 100.0) for v in cash_flow_values]
        debt_values = [max(v, 1000.0) for v in debt_values]
        
        financial_data = generate_historical_financial_data(
            revenue_values=revenue_values,
            profit_values=profit_values,
            cash_flow_values=cash_flow_values,
            debt_values=debt_values,
            industry="default"
        )
        
        agent = ForecastingAgent()
        result = await agent.predict(financial_data)
        
        # Verify methodology is documented (Requirement 5.5)
        assert "methodology" in result, \
            "Result must include 'methodology' (Requirement 5.5)"
        
        methodology = result["methodology"]
        
        # Verify methodology is a non-empty string
        assert isinstance(methodology, str), \
            "Methodology must be a string (Requirement 5.5)"
        assert len(methodology) > 0, \
            "Methodology must not be empty (Requirement 5.5)"
        
        # Verify methodology is substantial (at least 100 characters)
        assert len(methodology) >= 100, \
            "Methodology must be detailed (Requirement 5.5)"
        
        # Verify methodology mentions key components
        methodology_lower = methodology.lower()
        
        # Should mention historical analysis
        assert any(keyword in methodology_lower for keyword in ["historical", "trend", "past"]), \
            "Methodology must mention historical analysis (Requirement 5.5)"
        
        # Should mention industry benchmarking
        assert any(keyword in methodology_lower for keyword in ["industry", "benchmark", "sector"]), \
            "Methodology must mention industry benchmarking (Requirement 5.5)"
        
        # Should mention confidence or uncertainty
        assert any(keyword in methodology_lower for keyword in ["confidence", "uncertainty", "interval"]), \
            "Methodology must mention confidence/uncertainty (Requirement 5.5)"
