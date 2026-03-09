"""
Unit tests for FinancialCalculator service
"""

import pytest
from app.services.financial_calculator import FinancialCalculator


class TestLiquidityRatios:
    """Test liquidity ratio calculations"""
    
    def test_current_ratio_normal(self):
        """Test current ratio with normal values"""
        result = FinancialCalculator.calculate_current_ratio(
            current_assets=200000,
            current_liabilities=100000
        )
        assert result == 2.0
    
    def test_current_ratio_zero_denominator(self):
        """Test current ratio with zero liabilities"""
        result = FinancialCalculator.calculate_current_ratio(
            current_assets=200000,
            current_liabilities=0
        )
        assert result is None
    
    def test_quick_ratio_normal(self):
        """Test quick ratio with normal values"""
        result = FinancialCalculator.calculate_quick_ratio(
            current_assets=200000,
            inventory=50000,
            current_liabilities=100000
        )
        assert result == 1.5
    
    def test_quick_ratio_zero_denominator(self):
        """Test quick ratio with zero liabilities"""
        result = FinancialCalculator.calculate_quick_ratio(
            current_assets=200000,
            inventory=50000,
            current_liabilities=0
        )
        assert result is None


class TestLeverageRatios:
    """Test leverage ratio calculations"""
    
    def test_debt_to_equity_normal(self):
        """Test debt-to-equity ratio with normal values"""
        result = FinancialCalculator.calculate_debt_to_equity(
            total_debt=300000,
            total_equity=500000
        )
        assert result == 0.6
    
    def test_debt_to_equity_zero_denominator(self):
        """Test debt-to-equity ratio with zero equity"""
        result = FinancialCalculator.calculate_debt_to_equity(
            total_debt=300000,
            total_equity=0
        )
        assert result is None
    
    def test_debt_ratio_normal(self):
        """Test debt ratio with normal values"""
        result = FinancialCalculator.calculate_debt_ratio(
            total_debt=300000,
            total_assets=1000000
        )
        assert result == 0.3
    
    def test_debt_ratio_zero_denominator(self):
        """Test debt ratio with zero assets"""
        result = FinancialCalculator.calculate_debt_ratio(
            total_debt=300000,
            total_assets=0
        )
        assert result is None


class TestProfitabilityRatios:
    """Test profitability ratio calculations"""
    
    def test_net_profit_margin_normal(self):
        """Test net profit margin with normal values"""
        result = FinancialCalculator.calculate_net_profit_margin(
            net_income=100000,
            revenue=1000000
        )
        assert result == 0.1
    
    def test_net_profit_margin_zero_denominator(self):
        """Test net profit margin with zero revenue"""
        result = FinancialCalculator.calculate_net_profit_margin(
            net_income=100000,
            revenue=0
        )
        assert result is None
    
    def test_roe_normal(self):
        """Test ROE with normal values"""
        result = FinancialCalculator.calculate_roe(
            net_income=100000,
            total_equity=500000
        )
        assert result == 0.2
    
    def test_roe_zero_denominator(self):
        """Test ROE with zero equity"""
        result = FinancialCalculator.calculate_roe(
            net_income=100000,
            total_equity=0
        )
        assert result is None
    
    def test_roa_normal(self):
        """Test ROA with normal values"""
        result = FinancialCalculator.calculate_roa(
            net_income=100000,
            total_assets=1000000
        )
        assert result == 0.1
    
    def test_roa_zero_denominator(self):
        """Test ROA with zero assets"""
        result = FinancialCalculator.calculate_roa(
            net_income=100000,
            total_assets=0
        )
        assert result is None


class TestEfficiencyRatios:
    """Test efficiency ratio calculations"""
    
    def test_asset_turnover_normal(self):
        """Test asset turnover with normal values"""
        result = FinancialCalculator.calculate_asset_turnover(
            revenue=2000000,
            total_assets=1000000
        )
        assert result == 2.0
    
    def test_asset_turnover_zero_denominator(self):
        """Test asset turnover with zero assets"""
        result = FinancialCalculator.calculate_asset_turnover(
            revenue=2000000,
            total_assets=0
        )
        assert result is None
    
    def test_inventory_turnover_normal(self):
        """Test inventory turnover with normal values"""
        result = FinancialCalculator.calculate_inventory_turnover(
            cost_of_goods_sold=600000,
            average_inventory=100000
        )
        assert result == 6.0
    
    def test_inventory_turnover_zero_denominator(self):
        """Test inventory turnover with zero inventory"""
        result = FinancialCalculator.calculate_inventory_turnover(
            cost_of_goods_sold=600000,
            average_inventory=0
        )
        assert result is None


class TestCalculateRatios:
    """Test comprehensive ratio calculation"""
    
    def test_calculate_ratios_complete_data(self):
        """Test calculate_ratios with complete financial data"""
        financial_data = {
            'current_assets': 200000,
            'current_liabilities': 100000,
            'inventory': 50000,
            'total_debt': 300000,
            'total_equity': 500000,
            'total_assets': 1000000,
            'net_income': 100000,
            'revenue': 1000000,
            'cost_of_goods_sold': 600000,
            'average_inventory': 100000
        }
        
        ratios = FinancialCalculator.calculate_ratios(financial_data)
        
        assert 'current_ratio' in ratios
        assert ratios['current_ratio'] == 2.0
        
        assert 'quick_ratio' in ratios
        assert ratios['quick_ratio'] == 1.5
        
        assert 'debt_to_equity' in ratios
        assert ratios['debt_to_equity'] == 0.6
        
        assert 'debt_ratio' in ratios
        assert ratios['debt_ratio'] == 0.3
        
        assert 'net_profit_margin' in ratios
        assert ratios['net_profit_margin'] == 0.1
        
        assert 'roe' in ratios
        assert ratios['roe'] == 0.2
        
        assert 'roa' in ratios
        assert ratios['roa'] == 0.1
        
        assert 'asset_turnover' in ratios
        assert ratios['asset_turnover'] == 1.0
        
        assert 'inventory_turnover' in ratios
        assert ratios['inventory_turnover'] == 6.0
    
    def test_calculate_ratios_partial_data(self):
        """Test calculate_ratios with partial financial data"""
        financial_data = {
            'current_assets': 200000,
            'current_liabilities': 100000,
            'net_income': 100000,
            'revenue': 1000000
        }
        
        ratios = FinancialCalculator.calculate_ratios(financial_data)
        
        # Should have ratios for available data
        assert 'current_ratio' in ratios
        assert 'net_profit_margin' in ratios
        
        # Should not have ratios for missing data
        assert 'debt_to_equity' not in ratios
        assert 'roe' not in ratios
        assert 'inventory_turnover' not in ratios
    
    def test_calculate_ratios_with_zero_denominators(self):
        """Test calculate_ratios with zero denominators"""
        financial_data = {
            'current_assets': 200000,
            'current_liabilities': 0,  # Zero denominator
            'total_debt': 300000,
            'total_equity': 0,  # Zero denominator
            'net_income': 100000,
            'revenue': 1000000
        }
        
        ratios = FinancialCalculator.calculate_ratios(financial_data)
        
        # Should not include ratios with zero denominators
        assert 'current_ratio' not in ratios
        assert 'debt_to_equity' not in ratios
        
        # Should include valid ratios
        assert 'net_profit_margin' in ratios
        assert ratios['net_profit_margin'] == 0.1
    
    def test_calculate_ratios_empty_data(self):
        """Test calculate_ratios with empty data"""
        financial_data = {}
        
        ratios = FinancialCalculator.calculate_ratios(financial_data)
        
        assert ratios == {}
    
    def test_calculate_ratios_negative_values(self):
        """Test calculate_ratios with negative values (losses)"""
        financial_data = {
            'net_income': -50000,  # Loss
            'revenue': 1000000,
            'total_equity': 500000
        }
        
        ratios = FinancialCalculator.calculate_ratios(financial_data)
        
        # Should handle negative values correctly
        assert 'net_profit_margin' in ratios
        assert ratios['net_profit_margin'] == -0.05
        
        assert 'roe' in ratios
        assert ratios['roe'] == -0.1
