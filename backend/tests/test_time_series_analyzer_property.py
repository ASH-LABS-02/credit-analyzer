"""
Property-based tests for TimeSeriesAnalyzer

Feature: intelli-credit-platform
Property 8: Growth Rate Calculation Correctness

Validates: Requirements 4.2
"""

import pytest
from hypothesis import given, strategies as st, assume, settings, HealthCheck
from app.services.financial_calculator import TimeSeriesAnalyzer, TrendDirection


# Strategy for generating non-zero financial values
nonzero_financial = st.floats(
    min_value=-1e12,
    max_value=1e12,
    allow_nan=False,
    allow_infinity=False
).filter(lambda x: abs(x) > 1e-6)  # Exclude values very close to zero

# Strategy for generating positive financial values
positive_financial = st.floats(
    min_value=1e-6,
    max_value=1e12,
    allow_nan=False,
    allow_infinity=False
)

# Strategy for generating time series
time_series_strategy = st.lists(
    st.floats(min_value=-1e12, max_value=1e12, allow_nan=False, allow_infinity=False),
    min_size=2,
    max_size=20
)


class TestProperty8GrowthRateCalculationCorrectness:
    """
    Property 8: Growth Rate Calculation Correctness
    
    For any multi-year time series of financial data, the calculated year-over-year
    growth rates should correctly represent the percentage change between consecutive periods.
    
    Validates: Requirements 4.2
    """
    
    @pytest.mark.property
    @settings(max_examples=5)
    @given(
        current_value=st.floats(min_value=-1e12, max_value=1e12, allow_nan=False, allow_infinity=False),
        previous_value=nonzero_financial
    )
    def test_growth_rate_formula_correctness(
        self,
        current_value: float,
        previous_value: float
    ):
        """
        Property: Growth Rate = ((current - previous) / previous) * 100
        
        For any current and non-zero previous value, the calculated growth rate
        should match the standard formula.
        """
        result = TimeSeriesAnalyzer.calculate_growth_rate(current_value, previous_value)
        
        expected = ((current_value - previous_value) / previous_value) * 100
        
        assert result is not None
        assert abs(result - expected) < 1e-6, \
            f"Growth rate mismatch: got {result}, expected {expected}"
    
    @pytest.mark.property
    @settings(max_examples=5)
    @given(value=st.floats(min_value=-1e12, max_value=1e12, allow_nan=False, allow_infinity=False))
    def test_growth_rate_zero_previous_returns_none(self, value: float):
        """
        Property: Growth rate with zero previous value should return None
        
        For any current value and zero previous value, the growth rate
        calculation should return None (division by zero).
        """
        result = TimeSeriesAnalyzer.calculate_growth_rate(value, 0.0)
        assert result is None
    
    @pytest.mark.property
    @settings(max_examples=5)
    @given(value=nonzero_financial)
    def test_growth_rate_no_change_is_zero(self, value: float):
        """
        Property: Growth rate with no change should be zero
        
        For any non-zero value, if current equals previous, growth rate should be 0%.
        """
        result = TimeSeriesAnalyzer.calculate_growth_rate(value, value)
        assert result is not None
        assert abs(result) < 1e-9
    
    @pytest.mark.property
    @settings(max_examples=5)
    @given(
        previous_value=positive_financial,
        growth_pct=st.floats(min_value=-99, max_value=1000, allow_nan=False, allow_infinity=False)
    )
    def test_growth_rate_inverse_relationship(
        self,
        previous_value: float,
        growth_pct: float
    ):
        """
        Property: Growth rate calculation is invertible
        
        For any previous value and growth percentage, if we calculate the current value
        from the growth rate, then calculate the growth rate back, we should get
        the original growth percentage.
        """
        # Calculate current value from growth rate
        current_value = previous_value * (1 + growth_pct / 100)
        
        # Calculate growth rate back
        calculated_growth = TimeSeriesAnalyzer.calculate_growth_rate(
            current_value,
            previous_value
        )
        
        assert calculated_growth is not None
        assert abs(calculated_growth - growth_pct) < 1e-6
    
    @pytest.mark.property
    @settings(max_examples=5)
    @given(time_series=time_series_strategy)
    def test_growth_rates_list_length(self, time_series: list):
        """
        Property: Growth rates list has same length as time series
        
        For any time series with n values, the growth rates list should have n elements,
        with the first element being None (no prior period).
        """
        growth_rates = TimeSeriesAnalyzer.calculate_growth_rates(time_series)
        
        assert len(growth_rates) == len(time_series)
        assert growth_rates[0] is None
    
    @pytest.mark.property
    @settings(max_examples=5, suppress_health_check=[HealthCheck.filter_too_much])
    @given(time_series=time_series_strategy)
    def test_growth_rates_match_pairwise_calculations(self, time_series: list):
        """
        Property: Each growth rate in the list matches pairwise calculation
        
        For any time series, each growth rate at position i should match
        the growth rate calculated from time_series[i] and time_series[i-1].
        """
        growth_rates = TimeSeriesAnalyzer.calculate_growth_rates(time_series)
        
        for i in range(1, len(time_series)):
            expected = TimeSeriesAnalyzer.calculate_growth_rate(
                time_series[i],
                time_series[i - 1]
            )
            assert growth_rates[i] == expected
    
    @pytest.mark.property
    @settings(max_examples=5)
    @given(
        initial_value=positive_financial,
        final_value=positive_financial,
        num_periods=st.integers(min_value=1, max_value=50)
    )
    def test_cagr_bounds(
        self,
        initial_value: float,
        final_value: float,
        num_periods: int
    ):
        """
        Property: CAGR should be bounded by simple growth rate
        
        For any positive initial and final values, the CAGR should produce
        a value that, when compounded over the periods, equals the final value.
        """
        cagr = TimeSeriesAnalyzer.calculate_cagr(initial_value, final_value, num_periods)
        
        assert cagr is not None
        
        # Verify CAGR formula: final = initial * (1 + cagr/100)^periods
        calculated_final = initial_value * pow(1 + cagr / 100, num_periods)
        
        # Allow small floating point error - use relative tolerance
        relative_error = abs(calculated_final - final_value) / max(abs(final_value), abs(initial_value))
        assert relative_error < 1e-5
    
    @pytest.mark.property
    @settings(max_examples=5)
    @given(
        value=positive_financial,
        num_periods=st.integers(min_value=1, max_value=50)
    )
    def test_cagr_no_growth_is_zero(self, value: float, num_periods: int):
        """
        Property: CAGR with no growth should be zero
        
        For any positive value, if initial equals final, CAGR should be 0%.
        """
        cagr = TimeSeriesAnalyzer.calculate_cagr(value, value, num_periods)
        assert cagr is not None
        assert abs(cagr) < 1e-9
    
    @pytest.mark.property
    @settings(max_examples=5)
    @given(time_series=time_series_strategy)
    def test_trend_classification_is_valid(self, time_series: list):
        """
        Property: Trend analysis always returns a valid TrendDirection
        
        For any time series, the trend analysis should return one of the
        valid TrendDirection enum values.
        """
        trend = TimeSeriesAnalyzer.analyze_trend(time_series)
        
        assert isinstance(trend, TrendDirection)
        assert trend in [
            TrendDirection.INCREASING,
            TrendDirection.DECREASING,
            TrendDirection.STABLE,
            TrendDirection.VOLATILE,
            TrendDirection.INSUFFICIENT_DATA
        ]
    
    @pytest.mark.property
    @settings(max_examples=5)
    @given(
        base_value=positive_financial,
        num_periods=st.integers(min_value=3, max_value=10),
        growth_rate=st.floats(min_value=5, max_value=50)
    )
    def test_trend_increasing_for_consistent_growth(
        self,
        base_value: float,
        num_periods: int,
        growth_rate: float
    ):
        """
        Property: Consistently growing series should be classified as INCREASING
        
        For any series where each value is consistently higher than the previous
        by a significant margin, the trend should be INCREASING.
        """
        # Generate consistently increasing series
        time_series = [base_value]
        for _ in range(num_periods - 1):
            time_series.append(time_series[-1] * (1 + growth_rate / 100))
        
        trend = TimeSeriesAnalyzer.analyze_trend(time_series)
        
        assert trend == TrendDirection.INCREASING
    
    @pytest.mark.property
    @settings(max_examples=5)
    @given(
        base_value=positive_financial,
        num_periods=st.integers(min_value=3, max_value=10),
        decline_rate=st.floats(min_value=10, max_value=50)  # Use higher decline rate to ensure it's classified as decreasing
    )
    def test_trend_decreasing_for_consistent_decline(
        self,
        base_value: float,
        num_periods: int,
        decline_rate: float
    ):
        """
        Property: Consistently declining series should be classified as DECREASING
        
        For any series where each value is consistently lower than the previous
        by a significant margin, the trend should be DECREASING.
        """
        # Generate consistently decreasing series
        time_series = [base_value]
        for _ in range(num_periods - 1):
            next_value = time_series[-1] * (1 - decline_rate / 100)
            # Ensure we don't go negative
            if next_value > 0:
                time_series.append(next_value)
        
        # Only test if we have enough periods
        assume(len(time_series) >= 3)
        
        trend = TimeSeriesAnalyzer.analyze_trend(time_series)
        
        assert trend == TrendDirection.DECREASING
    
    @pytest.mark.property
    @settings(max_examples=20)
    @given(time_series=time_series_strategy)
    def test_multi_year_comparison_completeness(self, time_series: list):
        """
        Property: Multi-year comparison returns all required fields
        
        For any time series, the comparison should return a dictionary with
        all expected keys and appropriate values.
        """
        result = TimeSeriesAnalyzer.compare_multi_year(time_series)
        
        # Check all required keys are present
        required_keys = [
            'values', 'labels', 'growth_rates', 'cagr', 'trend',
            'min_value', 'max_value', 'avg_value', 'total_change', 'total_change_pct'
        ]
        for key in required_keys:
            assert key in result
        
        # Check values match input
        assert result['values'] == time_series
        
        # Check growth rates length
        assert len(result['growth_rates']) == len(time_series)
        
        # Check statistics are correct
        assert result['min_value'] == min(time_series)
        assert result['max_value'] == max(time_series)
        assert abs(result['avg_value'] - sum(time_series) / len(time_series)) < 1e-9
        assert result['total_change'] == time_series[-1] - time_series[0]
    
    @pytest.mark.property
    @settings(max_examples=20)
    @given(
        time_series=st.lists(
            positive_financial,
            min_size=3,
            max_size=10
        ),
        window_size=st.integers(min_value=2, max_value=5)
    )
    def test_moving_average_smoothing(
        self,
        time_series: list,
        window_size: int
    ):
        """
        Property: Moving average should smooth out fluctuations
        
        For any time series, the moving average values should be within
        the range of the original values in the window.
        """
        assume(window_size <= len(time_series))
        
        moving_avg = TimeSeriesAnalyzer.calculate_moving_average(time_series, window_size)
        
        assert len(moving_avg) == len(time_series)
        
        # Check that each moving average is within the range of its window
        for i in range(window_size - 1, len(time_series)):
            if moving_avg[i] is not None:
                window = time_series[i - window_size + 1:i + 1]
                assert min(window) <= moving_avg[i] <= max(window)
    
    @pytest.mark.property
    @settings(max_examples=20)
    @given(
        time_series=st.lists(
            positive_financial,
            min_size=3,
            max_size=10
        ),
        window_size=st.integers(min_value=2, max_value=5)
    )
    def test_moving_average_calculation_correctness(
        self,
        time_series: list,
        window_size: int
    ):
        """
        Property: Moving average should equal the mean of the window
        
        For any time series and window size, each moving average value
        should equal the arithmetic mean of the values in that window.
        """
        assume(window_size <= len(time_series))
        
        moving_avg = TimeSeriesAnalyzer.calculate_moving_average(time_series, window_size)
        
        # Check each moving average calculation
        for i in range(window_size - 1, len(time_series)):
            if moving_avg[i] is not None:
                window = time_series[i - window_size + 1:i + 1]
                expected_avg = sum(window) / len(window)
                assert abs(moving_avg[i] - expected_avg) < 1e-9
