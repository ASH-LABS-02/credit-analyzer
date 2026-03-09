"""
Financial Calculator Service

Provides methods for calculating financial ratios and metrics used in credit analysis.
Handles edge cases such as zero denominators.
Includes time-series analysis functions for growth rates, trends, and multi-year comparisons.
"""

from typing import Dict, Optional, List
from enum import Enum


class FinancialCalculator:
    """
    Calculator for financial ratios and metrics.
    
    This class provides static methods for calculating various financial ratios
    used in credit analysis, including liquidity, leverage, profitability, and
    efficiency ratios.
    """
    
    # Liquidity Ratios
    
    @staticmethod
    def calculate_current_ratio(
        current_assets: float,
        current_liabilities: float
    ) -> Optional[float]:
        """
        Calculate current ratio (current assets / current liabilities).
        
        Measures a company's ability to pay short-term obligations.
        
        Args:
            current_assets: Total current assets
            current_liabilities: Total current liabilities
            
        Returns:
            Current ratio or None if denominator is zero
        """
        if current_liabilities == 0:
            return None
        return current_assets / current_liabilities
    
    @staticmethod
    def calculate_quick_ratio(
        current_assets: float,
        inventory: float,
        current_liabilities: float
    ) -> Optional[float]:
        """
        Calculate quick ratio ((current assets - inventory) / current liabilities).
        
        Measures a company's ability to meet short-term obligations with liquid assets.
        Also known as the acid-test ratio.
        
        Args:
            current_assets: Total current assets
            inventory: Inventory value
            current_liabilities: Total current liabilities
            
        Returns:
            Quick ratio or None if denominator is zero
        """
        if current_liabilities == 0:
            return None
        return (current_assets - inventory) / current_liabilities
    
    # Leverage Ratios
    
    @staticmethod
    def calculate_debt_to_equity(
        total_debt: float,
        total_equity: float
    ) -> Optional[float]:
        """
        Calculate debt-to-equity ratio (total debt / total equity).
        
        Measures the degree of financial leverage.
        
        Args:
            total_debt: Total debt
            total_equity: Total equity
            
        Returns:
            Debt-to-equity ratio or None if denominator is zero
        """
        if total_equity == 0:
            return None
        return total_debt / total_equity
    
    @staticmethod
    def calculate_debt_ratio(
        total_debt: float,
        total_assets: float
    ) -> Optional[float]:
        """
        Calculate debt ratio (total debt / total assets).
        
        Measures the proportion of assets financed by debt.
        
        Args:
            total_debt: Total debt
            total_assets: Total assets
            
        Returns:
            Debt ratio or None if denominator is zero
        """
        if total_assets == 0:
            return None
        return total_debt / total_assets
    
    # Profitability Ratios
    
    @staticmethod
    def calculate_net_profit_margin(
        net_income: float,
        revenue: float
    ) -> Optional[float]:
        """
        Calculate net profit margin (net income / revenue).
        
        Measures how much profit is generated from revenue.
        
        Args:
            net_income: Net income
            revenue: Total revenue
            
        Returns:
            Net profit margin or None if denominator is zero
        """
        if revenue == 0:
            return None
        return net_income / revenue
    
    @staticmethod
    def calculate_roe(
        net_income: float,
        total_equity: float
    ) -> Optional[float]:
        """
        Calculate return on equity (ROE) (net income / total equity).
        
        Measures profitability relative to shareholders' equity.
        
        Args:
            net_income: Net income
            total_equity: Total equity
            
        Returns:
            ROE or None if denominator is zero
        """
        if total_equity == 0:
            return None
        return net_income / total_equity
    
    @staticmethod
    def calculate_roa(
        net_income: float,
        total_assets: float
    ) -> Optional[float]:
        """
        Calculate return on assets (ROA) (net income / total assets).
        
        Measures how efficiently assets are used to generate profit.
        
        Args:
            net_income: Net income
            total_assets: Total assets
            
        Returns:
            ROA or None if denominator is zero
        """
        if total_assets == 0:
            return None
        return net_income / total_assets
    
    # Efficiency Ratios
    
    @staticmethod
    def calculate_asset_turnover(
        revenue: float,
        total_assets: float
    ) -> Optional[float]:
        """
        Calculate asset turnover ratio (revenue / total assets).
        
        Measures how efficiently assets are used to generate revenue.
        
        Args:
            revenue: Total revenue
            total_assets: Total assets
            
        Returns:
            Asset turnover ratio or None if denominator is zero
        """
        if total_assets == 0:
            return None
        return revenue / total_assets
    
    @staticmethod
    def calculate_inventory_turnover(
        cost_of_goods_sold: float,
        average_inventory: float
    ) -> Optional[float]:
        """
        Calculate inventory turnover ratio (COGS / average inventory).
        
        Measures how many times inventory is sold and replaced over a period.
        
        Args:
            cost_of_goods_sold: Cost of goods sold
            average_inventory: Average inventory value
            
        Returns:
            Inventory turnover ratio or None if denominator is zero
        """
        if average_inventory == 0:
            return None
        return cost_of_goods_sold / average_inventory
    
    # Comprehensive Ratio Calculation
    
    @staticmethod
    def calculate_ratios(financial_data: Dict) -> Dict:
        """
        Calculate all available financial ratios from provided data.
        
        Args:
            financial_data: Dictionary containing financial metrics
            
        Returns:
            Dictionary of calculated ratios (only includes ratios where
            all required data is available and denominators are non-zero)
        """
        ratios = {}
        
        # Liquidity Ratios
        if 'current_assets' in financial_data and 'current_liabilities' in financial_data:
            current_ratio = FinancialCalculator.calculate_current_ratio(
                financial_data['current_assets'],
                financial_data['current_liabilities']
            )
            if current_ratio is not None:
                ratios['current_ratio'] = current_ratio
        
        if all(k in financial_data for k in ['current_assets', 'inventory', 'current_liabilities']):
            quick_ratio = FinancialCalculator.calculate_quick_ratio(
                financial_data['current_assets'],
                financial_data['inventory'],
                financial_data['current_liabilities']
            )
            if quick_ratio is not None:
                ratios['quick_ratio'] = quick_ratio
        
        # Leverage Ratios
        if 'total_debt' in financial_data and 'total_equity' in financial_data:
            debt_to_equity = FinancialCalculator.calculate_debt_to_equity(
                financial_data['total_debt'],
                financial_data['total_equity']
            )
            if debt_to_equity is not None:
                ratios['debt_to_equity'] = debt_to_equity
        
        if 'total_debt' in financial_data and 'total_assets' in financial_data:
            debt_ratio = FinancialCalculator.calculate_debt_ratio(
                financial_data['total_debt'],
                financial_data['total_assets']
            )
            if debt_ratio is not None:
                ratios['debt_ratio'] = debt_ratio
        
        # Profitability Ratios
        if 'net_income' in financial_data and 'revenue' in financial_data:
            net_profit_margin = FinancialCalculator.calculate_net_profit_margin(
                financial_data['net_income'],
                financial_data['revenue']
            )
            if net_profit_margin is not None:
                ratios['net_profit_margin'] = net_profit_margin
        
        if 'net_income' in financial_data and 'total_equity' in financial_data:
            roe = FinancialCalculator.calculate_roe(
                financial_data['net_income'],
                financial_data['total_equity']
            )
            if roe is not None:
                ratios['roe'] = roe
        
        if 'net_income' in financial_data and 'total_assets' in financial_data:
            roa = FinancialCalculator.calculate_roa(
                financial_data['net_income'],
                financial_data['total_assets']
            )
            if roa is not None:
                ratios['roa'] = roa
        
        # Efficiency Ratios
        if 'revenue' in financial_data and 'total_assets' in financial_data:
            asset_turnover = FinancialCalculator.calculate_asset_turnover(
                financial_data['revenue'],
                financial_data['total_assets']
            )
            if asset_turnover is not None:
                ratios['asset_turnover'] = asset_turnover
        
        if 'cost_of_goods_sold' in financial_data and 'average_inventory' in financial_data:
            inventory_turnover = FinancialCalculator.calculate_inventory_turnover(
                financial_data['cost_of_goods_sold'],
                financial_data['average_inventory']
            )
            if inventory_turnover is not None:
                ratios['inventory_turnover'] = inventory_turnover
        
        return ratios


class TrendDirection(Enum):
    """Enum for trend direction classification."""
    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"
    VOLATILE = "volatile"
    INSUFFICIENT_DATA = "insufficient_data"


class TimeSeriesAnalyzer:
    """
    Analyzer for time-series financial data.
    
    Provides methods for calculating growth rates, identifying trends,
    and performing multi-year comparisons.
    """
    
    @staticmethod
    def calculate_growth_rate(
        current_value: float,
        previous_value: float
    ) -> Optional[float]:
        """
        Calculate year-over-year growth rate between two periods.
        
        Formula: ((current - previous) / previous) * 100
        
        Args:
            current_value: Value in the current period
            previous_value: Value in the previous period
            
        Returns:
            Growth rate as a percentage, or None if previous value is zero
        """
        if previous_value == 0:
            return None
        return ((current_value - previous_value) / previous_value) * 100
    
    @staticmethod
    def calculate_growth_rates(time_series: List[float]) -> List[Optional[float]]:
        """
        Calculate year-over-year growth rates for a time series.
        
        For a time series [v0, v1, v2, ...], returns growth rates
        [None, g1, g2, ...] where gi = ((vi - vi-1) / vi-1) * 100
        
        Args:
            time_series: List of values in chronological order
            
        Returns:
            List of growth rates (first element is None as there's no prior period)
        """
        if not time_series or len(time_series) < 2:
            return []
        
        growth_rates = [None]  # No growth rate for first period
        
        for i in range(1, len(time_series)):
            growth_rate = TimeSeriesAnalyzer.calculate_growth_rate(
                time_series[i],
                time_series[i - 1]
            )
            growth_rates.append(growth_rate)
        
        return growth_rates
    
    @staticmethod
    def calculate_cagr(
        initial_value: float,
        final_value: float,
        num_periods: int
    ) -> Optional[float]:
        """
        Calculate Compound Annual Growth Rate (CAGR).
        
        Formula: ((final_value / initial_value) ^ (1 / num_periods) - 1) * 100
        
        Args:
            initial_value: Starting value
            final_value: Ending value
            num_periods: Number of periods between initial and final values
            
        Returns:
            CAGR as a percentage, or None if calculation is not possible
        """
        if initial_value <= 0 or num_periods <= 0:
            return None
        
        try:
            cagr = (pow(final_value / initial_value, 1 / num_periods) - 1) * 100
            return cagr
        except (ValueError, ZeroDivisionError):
            return None
    
    @staticmethod
    def analyze_trend(
        time_series: List[float],
        stability_threshold: float = 5.0
    ) -> TrendDirection:
        """
        Analyze the overall trend direction of a time series.
        
        Classifies the trend as increasing, decreasing, stable, volatile,
        or insufficient data based on growth rates and variability.
        
        Args:
            time_series: List of values in chronological order
            stability_threshold: Percentage threshold for considering trend stable
            
        Returns:
            TrendDirection enum indicating the trend classification
        """
        if not time_series or len(time_series) < 2:
            return TrendDirection.INSUFFICIENT_DATA
        
        growth_rates = TimeSeriesAnalyzer.calculate_growth_rates(time_series)
        # Filter out None values
        valid_growth_rates = [gr for gr in growth_rates if gr is not None]
        
        if not valid_growth_rates:
            return TrendDirection.INSUFFICIENT_DATA
        
        # Calculate average growth rate
        avg_growth = sum(valid_growth_rates) / len(valid_growth_rates)
        
        # Calculate standard deviation of growth rates with overflow protection
        if len(valid_growth_rates) > 1:
            try:
                # Clip extreme values to prevent overflow
                clipped_rates = [max(min(gr, 1e6), -1e6) for gr in valid_growth_rates]
                clipped_avg = sum(clipped_rates) / len(clipped_rates)
                variance = sum((gr - clipped_avg) ** 2 for gr in clipped_rates) / len(clipped_rates)
                std_dev = variance ** 0.5
            except (OverflowError, ValueError):
                # If calculation fails, treat as volatile
                return TrendDirection.VOLATILE
        else:
            std_dev = 0
        
        # Classify trend
        # High volatility: standard deviation is large relative to average
        if std_dev > 20:  # High volatility threshold
            return TrendDirection.VOLATILE
        
        # Stable: average growth rate is close to zero
        if abs(avg_growth) < stability_threshold:
            return TrendDirection.STABLE
        
        # Increasing or decreasing based on average growth
        if avg_growth > 0:
            return TrendDirection.INCREASING
        else:
            return TrendDirection.DECREASING
    
    @staticmethod
    def compare_multi_year(
        time_series: List[float],
        labels: Optional[List[str]] = None
    ) -> Dict:
        """
        Perform comprehensive multi-year comparison analysis.
        
        Provides growth rates, CAGR, trend analysis, and period-over-period changes.
        
        Args:
            time_series: List of values in chronological order
            labels: Optional list of period labels (e.g., ["2021", "2022", "2023"])
            
        Returns:
            Dictionary containing:
                - values: Original time series
                - labels: Period labels
                - growth_rates: Year-over-year growth rates
                - cagr: Compound annual growth rate
                - trend: Trend direction classification
                - min_value: Minimum value in series
                - max_value: Maximum value in series
                - avg_value: Average value across periods
                - total_change: Total change from first to last period
                - total_change_pct: Total percentage change
        """
        if not time_series:
            return {
                'values': [],
                'labels': labels or [],
                'growth_rates': [],
                'cagr': None,
                'trend': TrendDirection.INSUFFICIENT_DATA.value,
                'min_value': None,
                'max_value': None,
                'avg_value': None,
                'total_change': None,
                'total_change_pct': None
            }
        
        # Generate default labels if not provided
        if labels is None:
            labels = [f"Period {i+1}" for i in range(len(time_series))]
        
        # Calculate growth rates
        growth_rates = TimeSeriesAnalyzer.calculate_growth_rates(time_series)
        
        # Calculate CAGR
        cagr = None
        if len(time_series) >= 2:
            cagr = TimeSeriesAnalyzer.calculate_cagr(
                time_series[0],
                time_series[-1],
                len(time_series) - 1
            )
        
        # Analyze trend
        trend = TimeSeriesAnalyzer.analyze_trend(time_series)
        
        # Calculate statistics
        min_value = min(time_series)
        max_value = max(time_series)
        avg_value = sum(time_series) / len(time_series)
        
        # Calculate total change
        total_change = time_series[-1] - time_series[0]
        total_change_pct = TimeSeriesAnalyzer.calculate_growth_rate(
            time_series[-1],
            time_series[0]
        )
        
        return {
            'values': time_series,
            'labels': labels,
            'growth_rates': growth_rates,
            'cagr': cagr,
            'trend': trend.value,
            'min_value': min_value,
            'max_value': max_value,
            'avg_value': avg_value,
            'total_change': total_change,
            'total_change_pct': total_change_pct
        }
    
    @staticmethod
    def calculate_moving_average(
        time_series: List[float],
        window_size: int = 3
    ) -> List[Optional[float]]:
        """
        Calculate moving average for a time series.
        
        Args:
            time_series: List of values in chronological order
            window_size: Number of periods to include in each average
            
        Returns:
            List of moving averages (None for periods with insufficient data)
        """
        if not time_series or window_size < 1:
            return []
        
        moving_averages = []
        
        for i in range(len(time_series)):
            if i < window_size - 1:
                # Not enough data for moving average
                moving_averages.append(None)
            else:
                # Calculate average of window
                window = time_series[i - window_size + 1:i + 1]
                avg = sum(window) / len(window)
                moving_averages.append(avg)
        
        return moving_averages
