"""
Tests for Financial Analysis Agent

Tests the FinancialAnalysisAgent's ability to:
- Calculate financial ratios
- Analyze trends
- Compare against benchmarks
- Provide metric definitions
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.agents.financial_analysis_agent import FinancialAnalysisAgent


@pytest.fixture
def sample_extracted_data():
    """Sample extracted financial data for testing."""
    return {
        "financial_data": {
            "company_info": {
                "company_name": "Test Company Inc.",
                "industry": "Technology",
                "fiscal_year": "2023"
            },
            "financial_metrics": {
                "revenue": {
                    "values": [1000000, 1200000, 1500000],
                    "years": ["2021", "2022", "2023"],
                    "currency": "USD",
                    "confidence": "high"
                },
                "profit": {
                    "values": [100000, 150000, 200000],
                    "years": ["2021", "2022", "2023"],
                    "currency": "USD",
                    "confidence": "high"
                },
                "debt": {
                    "values": [300000, 280000, 250000],
                    "years": ["2021", "2022", "2023"],
                    "currency": "USD",
                    "confidence": "high"
                },
                "cash_flow": {
                    "values": [120000, 160000, 210000],
                    "years": ["2021", "2022", "2023"],
                    "currency": "USD",
                    "confidence": "high"
                },
                "current_assets": {
                    "value": 500000,
                    "year": "2023",
                    "confidence": "high"
                },
                "current_liabilities": {
                    "value": 200000,
                    "year": "2023",
                    "confidence": "high"
                },
                "total_assets": {
                    "value": 2000000,
                    "year": "2023",
                    "confidence": "high"
                },
                "total_equity": {
                    "value": 1500000,
                    "year": "2023",
                    "confidence": "high"
                },
                "total_debt": {
                    "value": 250000,
                    "year": "2023",
                    "confidence": "high"
                }
            }
        },
        "source_tracking": {},
        "ambiguous_flags": []
    }


@pytest.fixture
def agent():
    """Create a FinancialAnalysisAgent instance."""
    return FinancialAnalysisAgent()


@pytest.mark.asyncio
async def test_calculate_ratios(agent, sample_extracted_data):
    """Test that financial ratios are calculated correctly."""
    ratios = await agent._calculate_ratios(sample_extracted_data["financial_data"])
    
    # Check that ratios are calculated
    assert "current_ratio" in ratios
    assert "debt_to_equity" in ratios
    assert "net_profit_margin" in ratios
    assert "roe" in ratios
    assert "asset_turnover" in ratios
    
    # Verify ratio values
    assert ratios["current_ratio"]["value"] == pytest.approx(2.5, rel=0.01)  # 500000 / 200000
    assert ratios["debt_to_equity"]["value"] == pytest.approx(0.167, rel=0.01)  # 250000 / 1500000
    assert ratios["net_profit_margin"]["value"] == pytest.approx(0.133, rel=0.01)  # 200000 / 1500000
    assert ratios["roe"]["value"] == pytest.approx(0.133, rel=0.01)  # 200000 / 1500000
    assert ratios["asset_turnover"]["value"] == pytest.approx(0.75, rel=0.01)  # 1500000 / 2000000
    
    # Check that metadata is included
    assert "formatted_value" in ratios["current_ratio"]
    assert "definition" in ratios["current_ratio"]
    assert "formula" in ratios["current_ratio"]


@pytest.mark.asyncio
async def test_analyze_trends(agent, sample_extracted_data):
    """Test that trend analysis is performed correctly."""
    trends = await agent._analyze_trends(sample_extracted_data["financial_data"])
    
    # Check that trends are analyzed for key metrics
    assert "revenue" in trends
    assert "profit" in trends
    assert "debt" in trends
    assert "cash_flow" in trends
    
    # Verify trend data structure
    revenue_trend = trends["revenue"]
    assert "values" in revenue_trend
    assert "years" in revenue_trend
    assert "growth_rates" in revenue_trend
    assert "cagr" in revenue_trend
    assert "trend_direction" in revenue_trend
    assert "interpretation" in revenue_trend
    
    # Verify revenue is increasing
    assert revenue_trend["trend_direction"] == "increasing"
    
    # Verify growth rates are calculated
    assert len(revenue_trend["growth_rates"]) == 3
    assert revenue_trend["growth_rates"][0] is None  # First period has no prior
    assert revenue_trend["growth_rates"][1] == pytest.approx(20.0, rel=0.01)  # (1200000-1000000)/1000000 * 100
    assert revenue_trend["growth_rates"][2] == pytest.approx(25.0, rel=0.01)  # (1500000-1200000)/1200000 * 100


@pytest.mark.asyncio
async def test_compare_benchmarks(agent, sample_extracted_data):
    """Test that benchmark comparisons are performed correctly."""
    # First calculate ratios
    ratios = await agent._calculate_ratios(sample_extracted_data["financial_data"])
    
    # Then compare against benchmarks
    benchmarks = await agent._compare_benchmarks(
        ratios,
        sample_extracted_data["financial_data"]
    )
    
    # Check that benchmarks are provided
    assert len(benchmarks) > 0
    
    # Verify benchmark data structure
    for ratio_name, benchmark_data in benchmarks.items():
        assert "value" in benchmark_data
        assert "benchmark_good" in benchmark_data
        assert "benchmark_acceptable" in benchmark_data
        assert "benchmark_poor" in benchmark_data
        assert "performance" in benchmark_data
        assert "comparison" in benchmark_data
        assert benchmark_data["performance"] in ["good", "acceptable", "poor"]


@pytest.mark.asyncio
async def test_get_metric_definitions(agent, sample_extracted_data):
    """Test that metric definitions are provided."""
    ratios = await agent._calculate_ratios(sample_extracted_data["financial_data"])
    trends = await agent._analyze_trends(sample_extracted_data["financial_data"])
    
    definitions = agent._get_metric_definitions(ratios, trends)
    
    # Check that definitions are provided for ratios
    assert "current_ratio" in definitions
    assert "debt_to_equity" in definitions
    
    # Check definition structure
    current_ratio_def = definitions["current_ratio"]
    assert "name" in current_ratio_def
    assert "formula" in current_ratio_def
    assert "description" in current_ratio_def
    assert "interpretation" in current_ratio_def
    
    # Check that trend definitions are included
    assert "revenue_trend" in definitions
    assert "revenue_growth" in definitions


@pytest.mark.asyncio
async def test_analyze_complete_workflow(agent, sample_extracted_data):
    """Test the complete analysis workflow."""
    # Mock OpenAI response for summary generation
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Test Company Inc. demonstrates strong financial health with improving profitability and declining debt levels."
    
    with patch.object(agent.openai.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
        mock_create.return_value = mock_response
        
        result = await agent.analyze(sample_extracted_data)
        
        # Verify result structure
        assert "ratios" in result
        assert "trends" in result
        assert "benchmarks" in result
        assert "summary" in result
        assert "definitions" in result
        
        # Verify ratios are calculated
        assert len(result["ratios"]) > 0
        
        # Verify trends are analyzed
        assert len(result["trends"]) > 0
        
        # Verify benchmarks are compared
        assert len(result["benchmarks"]) > 0
        
        # Verify summary is generated
        assert isinstance(result["summary"], str)
        assert len(result["summary"]) > 0
        
        # Verify definitions are provided
        assert len(result["definitions"]) > 0


@pytest.mark.asyncio
async def test_analyze_with_empty_data(agent):
    """Test analysis with empty financial data."""
    empty_data = {
        "financial_data": {},
        "source_tracking": {},
        "ambiguous_flags": []
    }
    
    result = await agent.analyze(empty_data)
    
    # Should return empty results with appropriate message
    assert result["ratios"] == {}
    assert result["trends"] == {}
    assert result["benchmarks"] == {}
    assert "Insufficient" in result["summary"]
    assert result["definitions"] == {}


@pytest.mark.asyncio
async def test_analyze_with_partial_data(agent):
    """Test analysis with partial financial data."""
    partial_data = {
        "financial_data": {
            "financial_metrics": {
                "revenue": {
                    "values": [1000000, 1200000],
                    "years": ["2022", "2023"],
                    "currency": "USD",
                    "confidence": "high"
                },
                "current_assets": {
                    "value": 500000,
                    "year": "2023",
                    "confidence": "high"
                },
                "current_liabilities": {
                    "value": 200000,
                    "year": "2023",
                    "confidence": "high"
                }
            }
        },
        "source_tracking": {},
        "ambiguous_flags": []
    }
    
    # Mock OpenAI response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Limited financial data available for analysis."
    
    with patch.object(agent.openai.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
        mock_create.return_value = mock_response
        
        result = await agent.analyze(partial_data)
        
        # Should calculate available ratios
        assert "current_ratio" in result["ratios"]
        
        # Should analyze available trends
        assert "revenue" in result["trends"]
        
        # Should still provide summary
        assert isinstance(result["summary"], str)


@pytest.mark.asyncio
async def test_fallback_summary_generation(agent, sample_extracted_data):
    """Test fallback summary generation when OpenAI fails."""
    ratios = await agent._calculate_ratios(sample_extracted_data["financial_data"])
    trends = await agent._analyze_trends(sample_extracted_data["financial_data"])
    benchmarks = await agent._compare_benchmarks(
        ratios,
        sample_extracted_data["financial_data"]
    )
    
    # Generate fallback summary
    summary = agent._generate_fallback_summary(ratios, trends, benchmarks)
    
    # Verify summary is generated
    assert isinstance(summary, str)
    assert len(summary) > 0
    
    # Should contain some analysis keywords
    assert any(keyword in summary.lower() for keyword in ["financial", "health", "trend", "performance"])


def test_format_ratio_value(agent):
    """Test ratio value formatting."""
    # Test percentage ratios
    assert agent._format_ratio_value("net_profit_margin", 0.15) == "15.00%"
    assert agent._format_ratio_value("roe", 0.12) == "12.00%"
    assert agent._format_ratio_value("roa", 0.08) == "8.00%"
    
    # Test non-percentage ratios
    assert agent._format_ratio_value("current_ratio", 2.5) == "2.50"
    assert agent._format_ratio_value("debt_to_equity", 0.75) == "0.75"


def test_assess_performance(agent):
    """Test performance assessment against benchmarks."""
    benchmark = {"good": 2.0, "acceptable": 1.5, "poor": 1.0}
    
    # Test normal ratios (higher is better)
    assert agent._assess_performance("current_ratio", 2.5, benchmark) == "good"
    assert agent._assess_performance("current_ratio", 1.7, benchmark) == "acceptable"
    assert agent._assess_performance("current_ratio", 0.8, benchmark) == "poor"
    
    # Test inverse ratios (lower is better)
    debt_benchmark = {"good": 0.5, "acceptable": 1.0, "poor": 2.0}
    assert agent._assess_performance("debt_to_equity", 0.3, debt_benchmark) == "good"
    assert agent._assess_performance("debt_to_equity", 0.8, debt_benchmark) == "acceptable"
    assert agent._assess_performance("debt_to_equity", 2.5, debt_benchmark) == "poor"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
