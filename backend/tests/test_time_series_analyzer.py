"""
Unit tests for TimeSeriesAnalyzer

Tests specific examples and edge cases for time-series analysis functions.
"""

import pytest
from app.services.financial_calculator import TimeSeriesAnalyzer, TrendDirection


class TestGrowthRateCalculation:
    """Test growth rate calculation functions."""
    
    def test_calculate_growth_rate_positive_growth(self):
        """Test growth rate calculation with positive growth."""
        result = TimeSeriesAnalyzer.calculate_growth_rate(120, 100)
        assert result == 20.0
    
    def test_calculate_growth_rate_negative_growth(self):
        """Test growth rate calculation with negative growth."""
        result = TimeSeriesAnalyzer.calculate_growth_rate(80, 100)
        assert result == -20.0
    
    def test_calculate_growth_rate_no_change(self):
        """Test growth rate calculation with no change."""
        result = TimeSeriesAnalyzer.calculate_growth_rate(100, 100)
        assert result == 0.0
    
    def test_calculate_growth_rate_zero_previous(self):
        """Test growth rate calculation with zero previous value."""
        result = TimeSeriesAnalyzer.calculate_growth_rate(100, 0)
        assert result is None
    
    def test_calculate_growth_rate_from_negative(self):
        """Test growth rate calculation from negative to positive."""
        result = TimeSeriesAnalyzer.calculate_growth_rate(50, -100)
        # (50 - (-100)) / (-100) * 100 = 150 / -100 * 100 = -150
        assert result == -150.0
    
    def test_calculate_growth_rates_multi_year(self):
        """Test growth rates calculation for multiple years."""
        time_series = [100, 120, 150, 135]
        growth_rates = TimeSeriesAnalyzer.calculate_growth_rates(time_series)
        
        assert len(growth_rates) == 4
        assert growth_rates[0] is None  # No prior period
        assert growth_rates[1] == 20.0  # (120-100)/100 * 100
        assert growth_rates[2] == 25.0  # (150-120)/120 * 100
        assert growth_rates[3] == -10.0  # (135-150)/150 * 100
    
    def test_calculate_growth_rates_empty_list(self):
        """Test growth rates calculation with empty list."""
        growth_rates = TimeSeriesAnalyzer.calculate_growth_rates([])
        assert growth_rates == []
    
    def test_calculate_growth_rates_single_value(self):
        """Test growth rates calculation with single value."""
        growth_rates = TimeSeriesAnalyzer.calculate_growth_rates([100])
        assert growth_rates == []
    
    def test_calculate_growth_rates_with_zero(self):
        """Test growth rates calculation with zero in series."""
        time_series = [100, 0, 50]
        growth_rates = TimeSeriesAnalyzer.calculate_growth_rates(time_series)
        
        assert len(growth_rates) == 3
        assert growth_rates[0] is None
        assert growth_rates[1] == -100.0  # (0-100)/100 * 100
        assert growth_rates[2] is None  # Cannot calculate from zero


class TestCAGRCalculation:
    """Test Compound Annual Growth Rate calculation."""
    
    def test_calculate_cagr_positive_growth(self):
        """Test CAGR with positive growth."""
        # 100 to 121 over 2 years = 10% CAGR
        result = TimeSeriesAnalyzer.calculate_cagr(100, 121, 2)
        assert abs(result - 10.0) < 0.01
    
    def test_calculate_cagr_negative_growth(self):
        """Test CAGR with negative growth."""
        result = TimeSeriesAnalyzer.calculate_cagr(100, 81, 2)
        assert result < 0
        assert abs(result - (-10.0)) < 0.01
    
    def test_calculate_cagr_no_growth(self):
        """Test CAGR with no growth."""
        result = TimeSeriesAnalyzer.calculate_cagr(100, 100, 3)
        assert abs(result) < 0.01
    
    def test_calculate_cagr_zero_initial_value(self):
        """Test CAGR with zero initial value."""
        result = TimeSeriesAnalyzer.calculate_cagr(0, 100, 2)
        assert result is None
    
    def test_calculate_cagr_negative_initial_value(self):
        """Test CAGR with negative initial value."""
        result = TimeSeriesAnalyzer.calculate_cagr(-100, 100, 2)
        assert result is None
    
    def test_calculate_cagr_zero_periods(self):
        """Test CAGR with zero periods."""
        result = TimeSeriesAnalyzer.calculate_cagr(100, 121, 0)
        assert result is None


class TestTrendAnalysis:
    """Test trend analysis functions."""
    
    def test_analyze_trend_increasing(self):
        """Test trend analysis with increasing values."""
        time_series = [100, 110, 125, 140]
        trend = TimeSeriesAnalyzer.analyze_trend(time_series)
        assert trend == TrendDirection.INCREASING
    
    def test_analyze_trend_decreasing(self):
        """Test trend analysis with decreasing values."""
        time_series = [140, 125, 110, 100]
        trend = TimeSeriesAnalyzer.analyze_trend(time_series)
        assert trend == TrendDirection.DECREASING
    
    def test_analyze_trend_stable(self):
        """Test trend analysis with stable values."""
        time_series = [100, 102, 101, 103, 100]
        trend = TimeSeriesAnalyzer.analyze_trend(time_series)
        assert trend == TrendDirection.STABLE
    
    def test_analyze_trend_volatile(self):
        """Test trend analysis with volatile values."""
        time_series = [100, 150, 80, 160, 70, 140]
        trend = TimeSeriesAnalyzer.analyze_trend(time_series)
        assert trend == TrendDirection.VOLATILE
    
    def test_analyze_trend_insufficient_data(self):
        """Test trend analysis with insufficient data."""
        trend = TimeSeriesAnalyzer.analyze_trend([100])
        assert trend == TrendDirection.INSUFFICIENT_DATA
        
        trend = TimeSeriesAnalyzer.analyze_trend([])
        assert trend == TrendDirection.INSUFFICIENT_DATA
    
    def test_analyze_trend_custom_threshold(self):
        """Test trend analysis with custom stability threshold."""
        time_series = [100, 107, 105, 108]
        
        # With default threshold (5%), average growth is ~2.3%, should be stable
        trend = TimeSeriesAnalyzer.analyze_trend(time_series)
        assert trend == TrendDirection.STABLE
        
        # With lower threshold (1%), should be increasing
        trend = TimeSeriesAnalyzer.analyze_trend(time_series, stability_threshold=1.0)
        assert trend == TrendDirection.INCREASING


class TestMultiYearComparison:
    """Test multi-year comparison analysis."""
    
    def test_compare_multi_year_complete(self):
        """Test multi-year comparison with complete data."""
        time_series = [100, 120, 150, 135]
        labels = ["2020", "2021", "2022", "2023"]
        
        result = TimeSeriesAnalyzer.compare_multi_year(time_series, labels)
        
        assert result['values'] == time_series
        assert result['labels'] == labels
        assert len(result['growth_rates']) == 4
        assert result['growth_rates'][0] is None
        assert result['growth_rates'][1] == 20.0
        assert result['cagr'] is not None
        assert result['trend'] in [t.value for t in TrendDirection]
        assert result['min_value'] == 100
        assert result['max_value'] == 150
        assert result['avg_value'] == 126.25
        assert result['total_change'] == 35
        assert result['total_change_pct'] == 35.0
    
    def test_compare_multi_year_no_labels(self):
        """Test multi-year comparison without labels."""
        time_series = [100, 120, 150]
        
        result = TimeSeriesAnalyzer.compare_multi_year(time_series)
        
        assert result['labels'] == ["Period 1", "Period 2", "Period 3"]
    
    def test_compare_multi_year_empty(self):
        """Test multi-year comparison with empty data."""
        result = TimeSeriesAnalyzer.compare_multi_year([])
        
        assert result['values'] == []
        assert result['growth_rates'] == []
        assert result['cagr'] is None
        assert result['trend'] == TrendDirection.INSUFFICIENT_DATA.value
        assert result['min_value'] is None
        assert result['max_value'] is None
        assert result['avg_value'] is None
        assert result['total_change'] is None
        assert result['total_change_pct'] is None
    
    def test_compare_multi_year_single_value(self):
        """Test multi-year comparison with single value."""
        time_series = [100]
        
        result = TimeSeriesAnalyzer.compare_multi_year(time_series)
        
        assert result['values'] == [100]
        assert result['growth_rates'] == []
        assert result['cagr'] is None
        assert result['min_value'] == 100
        assert result['max_value'] == 100
        assert result['avg_value'] == 100
        assert result['total_change'] == 0
        # With single value, growth rate from first to last is 0/100 = 0%
        assert result['total_change_pct'] == 0.0


class TestMovingAverage:
    """Test moving average calculation."""
    
    def test_calculate_moving_average_3_period(self):
        """Test 3-period moving average."""
        time_series = [100, 110, 120, 130, 140]
        moving_avg = TimeSeriesAnalyzer.calculate_moving_average(time_series, window_size=3)
        
        assert len(moving_avg) == 5
        assert moving_avg[0] is None
        assert moving_avg[1] is None
        assert moving_avg[2] == 110.0  # (100+110+120)/3
        assert moving_avg[3] == 120.0  # (110+120+130)/3
        assert moving_avg[4] == 130.0  # (120+130+140)/3
    
    def test_calculate_moving_average_2_period(self):
        """Test 2-period moving average."""
        time_series = [100, 120, 140]
        moving_avg = TimeSeriesAnalyzer.calculate_moving_average(time_series, window_size=2)
        
        assert len(moving_avg) == 3
        assert moving_avg[0] is None
        assert moving_avg[1] == 110.0  # (100+120)/2
        assert moving_avg[2] == 130.0  # (120+140)/2
    
    def test_calculate_moving_average_empty(self):
        """Test moving average with empty list."""
        moving_avg = TimeSeriesAnalyzer.calculate_moving_average([])
        assert moving_avg == []
    
    def test_calculate_moving_average_invalid_window(self):
        """Test moving average with invalid window size."""
        time_series = [100, 110, 120]
        moving_avg = TimeSeriesAnalyzer.calculate_moving_average(time_series, window_size=0)
        assert moving_avg == []
    
    def test_calculate_moving_average_window_larger_than_series(self):
        """Test moving average with window larger than series."""
        time_series = [100, 110]
        moving_avg = TimeSeriesAnalyzer.calculate_moving_average(time_series, window_size=5)
        
        assert len(moving_avg) == 2
        assert moving_avg[0] is None
        assert moving_avg[1] is None
