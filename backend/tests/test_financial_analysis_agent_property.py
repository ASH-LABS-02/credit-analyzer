"""
Property-based tests for FinancialAnalysisAgent

Feature: intelli-credit-platform
Property 9: Calculated Metrics Metadata Completeness

Validates: Requirements 4.5
"""

import pytest
from hypothesis import given, strategies as st, assume, settings
from unittest.mock import AsyncMock, MagicMock, patch
from app.agents.financial_analysis_agent import FinancialAnalysisAgent


# Strategy for generating positive financial values
positive_value = st.floats(min_value=1.0, max_value=1e12, allow_nan=False, allow_infinity=False)

# Strategy for generating any financial values (including negative)
any_value = st.floats(min_value=-1e12, max_value=1e12, allow_nan=False, allow_infinity=False)

# Strategy for generating time series data (2-5 years)
time_series_length = st.integers(min_value=2, max_value=5)


def generate_financial_data(
    current_assets: float,
    current_liabilities: float,
    total_assets: float,
    total_equity: float,
    total_debt: float,
    revenue_values: list,
    profit_values: list,
    debt_values: list,
    cash_flow_values: list
):
    """Generate a complete financial data structure for testing."""
    years = [str(2020 + i) for i in range(len(revenue_values))]
    
    return {
        "financial_data": {
            "company_info": {
                "company_name": "Test Company",
                "industry": "default",
                "fiscal_year": years[-1]
            },
            "financial_metrics": {
                "revenue": {
                    "values": revenue_values,
                    "years": years,
                    "currency": "USD",
                    "confidence": "high"
                },
                "profit": {
                    "values": profit_values,
                    "years": years,
                    "currency": "USD",
                    "confidence": "high"
                },
                "debt": {
                    "values": debt_values,
                    "years": years,
                    "currency": "USD",
                    "confidence": "high"
                },
                "cash_flow": {
                    "values": cash_flow_values,
                    "years": years,
                    "currency": "USD",
                    "confidence": "high"
                },
                "current_assets": {
                    "value": current_assets,
                    "year": years[-1],
                    "confidence": "high"
                },
                "current_liabilities": {
                    "value": current_liabilities,
                    "year": years[-1],
                    "confidence": "high"
                },
                "total_assets": {
                    "value": total_assets,
                    "year": years[-1],
                    "confidence": "high"
                },
                "total_equity": {
                    "value": total_equity,
                    "year": years[-1],
                    "confidence": "high"
                },
                "total_debt": {
                    "value": total_debt,
                    "year": years[-1],
                    "confidence": "high"
                }
            }
        },
        "source_tracking": {},
        "ambiguous_flags": []
    }


class TestProperty9CalculatedMetricsMetadataCompleteness:
    """
    Property 9: Calculated Metrics Metadata Completeness
    
    For any calculated financial metric or ratio, the system should provide
    a definition and industry benchmark comparison data.
    
    Validates: Requirements 4.5
    """
    
    @pytest.mark.property
    @pytest.mark.asyncio
    @settings(max_examples=20)
    @given(
        current_assets=positive_value,
        current_liabilities=positive_value,
        total_assets=positive_value,
        total_equity=positive_value,
        total_debt=positive_value,
        num_years=time_series_length,
        revenue_base=positive_value,
        profit_base=any_value,
        debt_base=positive_value,
        cash_flow_base=any_value
    )
    async def test_all_calculated_ratios_have_definitions(
        self,
        current_assets: float,
        current_liabilities: float,
        total_assets: float,
        total_equity: float,
        total_debt: float,
        num_years: int,
        revenue_base: float,
        profit_base: float,
        debt_base: float,
        cash_flow_base: float
    ):
        """
        **Validates: Requirements 4.5**
        
        Property: For ALL calculated metrics, the system SHALL provide definitions
        
        For any set of financial data that results in calculated ratios,
        each ratio must have a complete definition including:
        - name
        - formula
        - description
        - interpretation (optional but recommended)
        """
        # Ensure realistic constraints
        assume(total_debt <= total_assets * 2)
        assume(current_assets <= total_assets)
        assume(current_liabilities <= total_assets)
        
        # Generate time series with some variation
        revenue_values = [revenue_base * (1 + i * 0.1) for i in range(num_years)]
        profit_values = [profit_base * (1 + i * 0.1) for i in range(num_years)]
        debt_values = [debt_base * (1 - i * 0.05) for i in range(num_years)]
        cash_flow_values = [cash_flow_base * (1 + i * 0.15) for i in range(num_years)]
        
        # Ensure all values are positive where needed
        revenue_values = [max(v, 1.0) for v in revenue_values]
        debt_values = [max(v, 1.0) for v in debt_values]
        
        financial_data = generate_financial_data(
            current_assets=current_assets,
            current_liabilities=current_liabilities,
            total_assets=total_assets,
            total_equity=total_equity,
            total_debt=total_debt,
            revenue_values=revenue_values,
            profit_values=profit_values,
            debt_values=debt_values,
            cash_flow_values=cash_flow_values
        )
        
        # Mock OpenAI response for summary generation
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Financial analysis summary."
        
        agent = FinancialAnalysisAgent()
        
        with patch.object(agent.openai.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response
            
            result = await agent.analyze(financial_data)
            
            # Verify that ratios were calculated
            assert "ratios" in result
            ratios = result["ratios"]
            
            # For each calculated ratio, verify it has complete metadata
            for ratio_name, ratio_data in ratios.items():
                assert isinstance(ratio_data, dict), \
                    f"Ratio {ratio_name} should be a dictionary with metadata"
                
                # Verify value is present
                assert "value" in ratio_data, \
                    f"Ratio {ratio_name} must have a 'value' field"
                assert isinstance(ratio_data["value"], (int, float)), \
                    f"Ratio {ratio_name} value must be numeric"
                
                # Verify formatted value is present
                assert "formatted_value" in ratio_data, \
                    f"Ratio {ratio_name} must have a 'formatted_value' field"
                assert isinstance(ratio_data["formatted_value"], str), \
                    f"Ratio {ratio_name} formatted_value must be a string"
                
                # Verify definition is present (Requirement 4.5)
                assert "definition" in ratio_data, \
                    f"Ratio {ratio_name} must have a 'definition' field (Requirement 4.5)"
                assert isinstance(ratio_data["definition"], str), \
                    f"Ratio {ratio_name} definition must be a string"
                
                # Verify formula is present (Requirement 4.5)
                assert "formula" in ratio_data, \
                    f"Ratio {ratio_name} must have a 'formula' field (Requirement 4.5)"
                assert isinstance(ratio_data["formula"], str), \
                    f"Ratio {ratio_name} formula must be a string"
            
            # Verify definitions dictionary is provided
            assert "definitions" in result, \
                "Result must include a 'definitions' dictionary (Requirement 4.5)"
            definitions = result["definitions"]
            
            # For each calculated ratio, verify it has a definition in the definitions dict
            for ratio_name in ratios.keys():
                assert ratio_name in definitions, \
                    f"Ratio {ratio_name} must have an entry in definitions dictionary (Requirement 4.5)"
                
                definition = definitions[ratio_name]
                assert isinstance(definition, dict), \
                    f"Definition for {ratio_name} must be a dictionary"
                
                # Verify definition structure
                assert "name" in definition, \
                    f"Definition for {ratio_name} must include 'name'"
                assert "formula" in definition, \
                    f"Definition for {ratio_name} must include 'formula'"
                assert "description" in definition, \
                    f"Definition for {ratio_name} must include 'description'"
                
                # Verify all fields are non-empty strings
                assert len(definition["name"]) > 0, \
                    f"Definition name for {ratio_name} must not be empty"
                assert len(definition["formula"]) > 0, \
                    f"Definition formula for {ratio_name} must not be empty"
                assert len(definition["description"]) > 0, \
                    f"Definition description for {ratio_name} must not be empty"
    
    @pytest.mark.property
    @pytest.mark.asyncio
    @settings(max_examples=20)
    @given(
        current_assets=positive_value,
        current_liabilities=positive_value,
        total_assets=positive_value,
        total_equity=positive_value,
        total_debt=positive_value,
        num_years=time_series_length,
        revenue_base=positive_value,
        profit_base=any_value,
        debt_base=positive_value,
        cash_flow_base=any_value
    )
    async def test_all_calculated_ratios_have_benchmark_comparisons(
        self,
        current_assets: float,
        current_liabilities: float,
        total_assets: float,
        total_equity: float,
        total_debt: float,
        num_years: int,
        revenue_base: float,
        profit_base: float,
        debt_base: float,
        cash_flow_base: float
    ):
        """
        **Validates: Requirements 4.5**
        
        Property: For ALL calculated metrics, the system SHALL provide
        industry benchmark comparisons
        
        For any set of financial data that results in calculated ratios,
        each ratio must have industry benchmark comparison data including:
        - benchmark_good: threshold for good performance
        - benchmark_acceptable: threshold for acceptable performance
        - benchmark_poor: threshold for poor performance
        - performance: assessment against benchmarks
        - comparison: human-readable comparison text
        """
        # Ensure realistic constraints
        assume(total_debt <= total_assets * 2)
        assume(current_assets <= total_assets)
        assume(current_liabilities <= total_assets)
        
        # Generate time series with some variation
        revenue_values = [revenue_base * (1 + i * 0.1) for i in range(num_years)]
        profit_values = [profit_base * (1 + i * 0.1) for i in range(num_years)]
        debt_values = [debt_base * (1 - i * 0.05) for i in range(num_years)]
        cash_flow_values = [cash_flow_base * (1 + i * 0.15) for i in range(num_years)]
        
        # Ensure all values are positive where needed
        revenue_values = [max(v, 1.0) for v in revenue_values]
        debt_values = [max(v, 1.0) for v in debt_values]
        
        financial_data = generate_financial_data(
            current_assets=current_assets,
            current_liabilities=current_liabilities,
            total_assets=total_assets,
            total_equity=total_equity,
            total_debt=total_debt,
            revenue_values=revenue_values,
            profit_values=profit_values,
            debt_values=debt_values,
            cash_flow_values=cash_flow_values
        )
        
        # Mock OpenAI response for summary generation
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Financial analysis summary."
        
        agent = FinancialAnalysisAgent()
        
        with patch.object(agent.openai.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response
            
            result = await agent.analyze(financial_data)
            
            # Verify that benchmarks were calculated
            assert "benchmarks" in result, \
                "Result must include 'benchmarks' (Requirement 4.5)"
            benchmarks = result["benchmarks"]
            
            # Verify that ratios were calculated
            assert "ratios" in result
            ratios = result["ratios"]
            
            # For each calculated ratio that has benchmark data, verify completeness
            # Note: Not all ratios may have benchmarks defined in INDUSTRY_BENCHMARKS
            for ratio_name, benchmark_data in benchmarks.items():
                assert isinstance(benchmark_data, dict), \
                    f"Benchmark for {ratio_name} should be a dictionary"
                
                # Verify value is present
                assert "value" in benchmark_data, \
                    f"Benchmark for {ratio_name} must include 'value'"
                
                # Verify benchmark thresholds are present (Requirement 4.5)
                assert "benchmark_good" in benchmark_data, \
                    f"Benchmark for {ratio_name} must include 'benchmark_good' (Requirement 4.5)"
                assert "benchmark_acceptable" in benchmark_data, \
                    f"Benchmark for {ratio_name} must include 'benchmark_acceptable' (Requirement 4.5)"
                assert "benchmark_poor" in benchmark_data, \
                    f"Benchmark for {ratio_name} must include 'benchmark_poor' (Requirement 4.5)"
                
                # Verify all benchmark thresholds are numeric
                assert isinstance(benchmark_data["benchmark_good"], (int, float)), \
                    f"Benchmark 'good' threshold for {ratio_name} must be numeric"
                assert isinstance(benchmark_data["benchmark_acceptable"], (int, float)), \
                    f"Benchmark 'acceptable' threshold for {ratio_name} must be numeric"
                assert isinstance(benchmark_data["benchmark_poor"], (int, float)), \
                    f"Benchmark 'poor' threshold for {ratio_name} must be numeric"
                
                # Verify performance assessment is present (Requirement 4.5)
                assert "performance" in benchmark_data, \
                    f"Benchmark for {ratio_name} must include 'performance' assessment (Requirement 4.5)"
                assert benchmark_data["performance"] in ["good", "acceptable", "poor"], \
                    f"Performance for {ratio_name} must be 'good', 'acceptable', or 'poor'"
                
                # Verify comparison text is present (Requirement 4.5)
                assert "comparison" in benchmark_data, \
                    f"Benchmark for {ratio_name} must include 'comparison' text (Requirement 4.5)"
                assert isinstance(benchmark_data["comparison"], str), \
                    f"Comparison for {ratio_name} must be a string"
                assert len(benchmark_data["comparison"]) > 0, \
                    f"Comparison text for {ratio_name} must not be empty"
    
    @pytest.mark.property
    @pytest.mark.asyncio
    @settings(max_examples=20)
    @given(
        current_assets=positive_value,
        current_liabilities=positive_value,
        total_assets=positive_value,
        total_equity=positive_value,
        total_debt=positive_value,
        num_years=time_series_length,
        revenue_base=positive_value,
        profit_base=any_value,
        debt_base=positive_value,
        cash_flow_base=any_value
    )
    async def test_all_trend_metrics_have_definitions(
        self,
        current_assets: float,
        current_liabilities: float,
        total_assets: float,
        total_equity: float,
        total_debt: float,
        num_years: int,
        revenue_base: float,
        profit_base: float,
        debt_base: float,
        cash_flow_base: float
    ):
        """
        **Validates: Requirements 4.5**
        
        Property: For ALL calculated trend metrics, the system SHALL provide definitions
        
        For any time-series financial data that results in trend analysis,
        each trend metric must have definitions in the definitions dictionary.
        """
        # Ensure realistic constraints
        assume(total_debt <= total_assets * 2)
        assume(current_assets <= total_assets)
        assume(current_liabilities <= total_assets)
        
        # Generate time series with some variation
        revenue_values = [revenue_base * (1 + i * 0.1) for i in range(num_years)]
        profit_values = [profit_base * (1 + i * 0.1) for i in range(num_years)]
        debt_values = [debt_base * (1 - i * 0.05) for i in range(num_years)]
        cash_flow_values = [cash_flow_base * (1 + i * 0.15) for i in range(num_years)]
        
        # Ensure all values are positive where needed
        revenue_values = [max(v, 1.0) for v in revenue_values]
        debt_values = [max(v, 1.0) for v in debt_values]
        
        financial_data = generate_financial_data(
            current_assets=current_assets,
            current_liabilities=current_liabilities,
            total_assets=total_assets,
            total_equity=total_equity,
            total_debt=total_debt,
            revenue_values=revenue_values,
            profit_values=profit_values,
            debt_values=debt_values,
            cash_flow_values=cash_flow_values
        )
        
        # Mock OpenAI response for summary generation
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Financial analysis summary."
        
        agent = FinancialAnalysisAgent()
        
        with patch.object(agent.openai.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response
            
            result = await agent.analyze(financial_data)
            
            # Verify that trends were calculated
            assert "trends" in result
            trends = result["trends"]
            
            # Verify definitions dictionary is provided
            assert "definitions" in result
            definitions = result["definitions"]
            
            # For each trend metric, verify it has definitions
            for metric_name in trends.keys():
                # Check for trend definition
                trend_key = f"{metric_name}_trend"
                assert trend_key in definitions, \
                    f"Trend metric {metric_name} must have a '{trend_key}' definition (Requirement 4.5)"
                
                trend_def = definitions[trend_key]
                assert "name" in trend_def, \
                    f"Trend definition for {metric_name} must include 'name'"
                assert "description" in trend_def, \
                    f"Trend definition for {metric_name} must include 'description'"
                
                # Check for growth rate definition
                growth_key = f"{metric_name}_growth"
                assert growth_key in definitions, \
                    f"Trend metric {metric_name} must have a '{growth_key}' definition (Requirement 4.5)"
                
                growth_def = definitions[growth_key]
                assert "name" in growth_def, \
                    f"Growth definition for {metric_name} must include 'name'"
                assert "description" in growth_def, \
                    f"Growth definition for {metric_name} must include 'description'"
