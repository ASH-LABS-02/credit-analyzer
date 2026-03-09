"""
Property-based tests for FinancialCalculator service

Feature: intelli-credit-platform
Property 7: Financial Ratio Calculation Correctness

Validates: Requirements 4.1
"""

import pytest
from hypothesis import given, strategies as st, assume, settings
from app.services.financial_calculator import FinancialCalculator


# Strategy for generating non-zero positive financial values
positive_nonzero = st.floats(min_value=0.01, max_value=1e12, allow_nan=False, allow_infinity=False)

# Strategy for generating any financial values (including negative for income/losses)
any_financial = st.floats(min_value=-1e12, max_value=1e12, allow_nan=False, allow_infinity=False)


class TestProperty7FinancialRatioCalculationCorrectness:
    """
    Property 7: Financial Ratio Calculation Correctness
    
    For any set of financial data with non-zero denominators, the calculated ratios
    (current ratio, debt-to-equity, net profit margin, ROE, asset turnover) should
    match the standard financial formulas.
    
    Validates: Requirements 4.1
    """
    
    @pytest.mark.property
    @settings(max_examples=5)
    @given(
        current_assets=positive_nonzero,
        current_liabilities=positive_nonzero
    )
    def test_current_ratio_formula_correctness(
        self,
        current_assets: float,
        current_liabilities: float
    ):
        """
        Property: Current Ratio = Current Assets / Current Liabilities
        
        For any positive non-zero current assets and current liabilities,
        the calculated current ratio should equal the manual calculation.
        """
        result = FinancialCalculator.calculate_current_ratio(
            current_assets=current_assets,
            current_liabilities=current_liabilities
        )
        
        expected = current_assets / current_liabilities
        
        assert result is not None
        assert abs(result - expected) < 1e-9, \
            f"Current ratio mismatch: got {result}, expected {expected}"
    
    @pytest.mark.property
    @settings(max_examples=3)
    @given(
        total_debt=positive_nonzero,
        total_equity=positive_nonzero
    )
    def test_debt_to_equity_formula_correctness(
        self,
        total_debt: float,
        total_equity: float
    ):
        """
        Property: Debt-to-Equity Ratio = Total Debt / Total Equity
        
        For any positive non-zero total debt and total equity,
        the calculated debt-to-equity ratio should equal the manual calculation.
        """
        result = FinancialCalculator.calculate_debt_to_equity(
            total_debt=total_debt,
            total_equity=total_equity
        )
        
        expected = total_debt / total_equity
        
        assert result is not None
        assert abs(result - expected) < 1e-9, \
            f"Debt-to-equity ratio mismatch: got {result}, expected {expected}"
    
    @pytest.mark.property
    @settings(max_examples=3)
    @given(
        net_income=any_financial,
        revenue=positive_nonzero
    )
    def test_net_profit_margin_formula_correctness(
        self,
        net_income: float,
        revenue: float
    ):
        """
        Property: Net Profit Margin = Net Income / Revenue
        
        For any net income (can be negative for losses) and positive non-zero revenue,
        the calculated net profit margin should equal the manual calculation.
        """
        result = FinancialCalculator.calculate_net_profit_margin(
            net_income=net_income,
            revenue=revenue
        )
        
        expected = net_income / revenue
        
        assert result is not None
        assert abs(result - expected) < 1e-9, \
            f"Net profit margin mismatch: got {result}, expected {expected}"
    
    @pytest.mark.property
    @settings(max_examples=5)
    @given(
        net_income=any_financial,
        total_equity=positive_nonzero
    )
    def test_roe_formula_correctness(
        self,
        net_income: float,
        total_equity: float
    ):
        """
        Property: ROE (Return on Equity) = Net Income / Total Equity
        
        For any net income (can be negative for losses) and positive non-zero total equity,
        the calculated ROE should equal the manual calculation.
        """
        result = FinancialCalculator.calculate_roe(
            net_income=net_income,
            total_equity=total_equity
        )
        
        expected = net_income / total_equity
        
        assert result is not None
        assert abs(result - expected) < 1e-9, \
            f"ROE mismatch: got {result}, expected {expected}"
    
    @pytest.mark.property
    @settings(max_examples=5)
    @given(
        revenue=positive_nonzero,
        total_assets=positive_nonzero
    )
    def test_asset_turnover_formula_correctness(
        self,
        revenue: float,
        total_assets: float
    ):
        """
        Property: Asset Turnover = Revenue / Total Assets
        
        For any positive non-zero revenue and total assets,
        the calculated asset turnover should equal the manual calculation.
        """
        result = FinancialCalculator.calculate_asset_turnover(
            revenue=revenue,
            total_assets=total_assets
        )
        
        expected = revenue / total_assets
        
        assert result is not None
        assert abs(result - expected) < 1e-9, \
            f"Asset turnover mismatch: got {result}, expected {expected}"
    
    @pytest.mark.property
    @settings(max_examples=5)
    @given(
        current_assets=positive_nonzero,
        inventory=st.floats(min_value=0, max_value=1e12, allow_nan=False, allow_infinity=False),
        current_liabilities=positive_nonzero
    )
    def test_quick_ratio_formula_correctness(
        self,
        current_assets: float,
        inventory: float,
        current_liabilities: float
    ):
        """
        Property: Quick Ratio = (Current Assets - Inventory) / Current Liabilities
        
        For any positive non-zero current assets, non-negative inventory,
        and positive non-zero current liabilities,
        the calculated quick ratio should equal the manual calculation.
        """
        # Ensure inventory doesn't exceed current assets
        assume(inventory <= current_assets)
        
        result = FinancialCalculator.calculate_quick_ratio(
            current_assets=current_assets,
            inventory=inventory,
            current_liabilities=current_liabilities
        )
        
        expected = (current_assets - inventory) / current_liabilities
        
        assert result is not None
        assert abs(result - expected) < 1e-9, \
            f"Quick ratio mismatch: got {result}, expected {expected}"
    
    @pytest.mark.property
    @settings(max_examples=5)
    @given(
        total_debt=positive_nonzero,
        total_assets=positive_nonzero
    )
    def test_debt_ratio_formula_correctness(
        self,
        total_debt: float,
        total_assets: float
    ):
        """
        Property: Debt Ratio = Total Debt / Total Assets
        
        For any positive non-zero total debt and total assets,
        the calculated debt ratio should equal the manual calculation.
        """
        # Ensure debt doesn't exceed assets (realistic constraint)
        assume(total_debt <= total_assets * 2)  # Allow some leverage
        
        result = FinancialCalculator.calculate_debt_ratio(
            total_debt=total_debt,
            total_assets=total_assets
        )
        
        expected = total_debt / total_assets
        
        assert result is not None
        assert abs(result - expected) < 1e-9, \
            f"Debt ratio mismatch: got {result}, expected {expected}"
    
    @pytest.mark.property
    @settings(max_examples=5)
    @given(
        net_income=any_financial,
        total_assets=positive_nonzero
    )
    def test_roa_formula_correctness(
        self,
        net_income: float,
        total_assets: float
    ):
        """
        Property: ROA (Return on Assets) = Net Income / Total Assets
        
        For any net income (can be negative for losses) and positive non-zero total assets,
        the calculated ROA should equal the manual calculation.
        """
        result = FinancialCalculator.calculate_roa(
            net_income=net_income,
            total_assets=total_assets
        )
        
        expected = net_income / total_assets
        
        assert result is not None
        assert abs(result - expected) < 1e-9, \
            f"ROA mismatch: got {result}, expected {expected}"
    
    @pytest.mark.property
    @settings(max_examples=5)
    @given(
        cost_of_goods_sold=positive_nonzero,
        average_inventory=positive_nonzero
    )
    def test_inventory_turnover_formula_correctness(
        self,
        cost_of_goods_sold: float,
        average_inventory: float
    ):
        """
        Property: Inventory Turnover = Cost of Goods Sold / Average Inventory
        
        For any positive non-zero COGS and average inventory,
        the calculated inventory turnover should equal the manual calculation.
        """
        result = FinancialCalculator.calculate_inventory_turnover(
            cost_of_goods_sold=cost_of_goods_sold,
            average_inventory=average_inventory
        )
        
        expected = cost_of_goods_sold / average_inventory
        
        assert result is not None
        assert abs(result - expected) < 1e-9, \
            f"Inventory turnover mismatch: got {result}, expected {expected}"
    
    @pytest.mark.property
    @settings(max_examples=5)
    @given(
        current_assets=positive_nonzero,
        current_liabilities=positive_nonzero,
        inventory=st.floats(min_value=0, max_value=1e12, allow_nan=False, allow_infinity=False),
        total_debt=positive_nonzero,
        total_equity=positive_nonzero,
        total_assets=positive_nonzero,
        net_income=any_financial,
        revenue=positive_nonzero,
        cost_of_goods_sold=positive_nonzero,
        average_inventory=positive_nonzero
    )
    def test_calculate_ratios_comprehensive_correctness(
        self,
        current_assets: float,
        current_liabilities: float,
        inventory: float,
        total_debt: float,
        total_equity: float,
        total_assets: float,
        net_income: float,
        revenue: float,
        cost_of_goods_sold: float,
        average_inventory: float
    ):
        """
        Property: All ratios in calculate_ratios() should match their individual formulas
        
        For any complete set of financial data with non-zero denominators,
        the comprehensive calculate_ratios method should produce results
        that match the individual ratio calculation methods.
        """
        # Ensure realistic constraints
        assume(inventory <= current_assets)
        assume(total_debt <= total_assets * 2)
        
        financial_data = {
            'current_assets': current_assets,
            'current_liabilities': current_liabilities,
            'inventory': inventory,
            'total_debt': total_debt,
            'total_equity': total_equity,
            'total_assets': total_assets,
            'net_income': net_income,
            'revenue': revenue,
            'cost_of_goods_sold': cost_of_goods_sold,
            'average_inventory': average_inventory
        }
        
        ratios = FinancialCalculator.calculate_ratios(financial_data)
        
        # Verify each ratio matches its formula
        assert 'current_ratio' in ratios
        expected_current_ratio = current_assets / current_liabilities
        assert abs(ratios['current_ratio'] - expected_current_ratio) < 1e-9
        
        assert 'quick_ratio' in ratios
        expected_quick_ratio = (current_assets - inventory) / current_liabilities
        assert abs(ratios['quick_ratio'] - expected_quick_ratio) < 1e-9
        
        assert 'debt_to_equity' in ratios
        expected_debt_to_equity = total_debt / total_equity
        assert abs(ratios['debt_to_equity'] - expected_debt_to_equity) < 1e-9
        
        assert 'debt_ratio' in ratios
        expected_debt_ratio = total_debt / total_assets
        assert abs(ratios['debt_ratio'] - expected_debt_ratio) < 1e-9
        
        assert 'net_profit_margin' in ratios
        expected_npm = net_income / revenue
        assert abs(ratios['net_profit_margin'] - expected_npm) < 1e-9
        
        assert 'roe' in ratios
        expected_roe = net_income / total_equity
        assert abs(ratios['roe'] - expected_roe) < 1e-9
        
        assert 'roa' in ratios
        expected_roa = net_income / total_assets
        assert abs(ratios['roa'] - expected_roa) < 1e-9
        
        assert 'asset_turnover' in ratios
        expected_asset_turnover = revenue / total_assets
        assert abs(ratios['asset_turnover'] - expected_asset_turnover) < 1e-9
        
        assert 'inventory_turnover' in ratios
        expected_inventory_turnover = cost_of_goods_sold / average_inventory
        assert abs(ratios['inventory_turnover'] - expected_inventory_turnover) < 1e-9
    
    @pytest.mark.property
    @settings(max_examples=5)
    @given(
        current_assets=positive_nonzero,
        net_income=any_financial,
        revenue=positive_nonzero
    )
    def test_calculate_ratios_handles_zero_denominators(
        self,
        current_assets: float,
        net_income: float,
        revenue: float
    ):
        """
        Property: calculate_ratios should exclude ratios with zero denominators
        
        For any financial data where some denominators are zero,
        the calculate_ratios method should only include ratios
        where all required data is available and denominators are non-zero.
        """
        financial_data = {
            'current_assets': current_assets,
            'current_liabilities': 0,  # Zero denominator
            'total_debt': 100000,
            'total_equity': 0,  # Zero denominator
            'net_income': net_income,
            'revenue': revenue
        }
        
        ratios = FinancialCalculator.calculate_ratios(financial_data)
        
        # Should not include ratios with zero denominators
        assert 'current_ratio' not in ratios
        assert 'debt_to_equity' not in ratios
        
        # Should include valid ratios
        assert 'net_profit_margin' in ratios
        expected_npm = net_income / revenue
        assert abs(ratios['net_profit_margin'] - expected_npm) < 1e-9
