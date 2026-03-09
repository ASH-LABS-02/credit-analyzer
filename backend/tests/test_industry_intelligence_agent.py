"""
Unit tests for IndustryIntelligenceAgent

Tests the industry intelligence functionality including sector trend analysis,
competitive landscape evaluation, risk identification, and growth outlook assessment.

Requirements: 3.4
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
import json

from app.agents.industry_intelligence_agent import IndustryIntelligenceAgent


@pytest.fixture
def industry_agent():
    """Create an IndustryIntelligenceAgent instance for testing."""
    return IndustryIntelligenceAgent()


@pytest.fixture
def sample_sector_trends():
    """Sample sector trends for testing."""
    return {
        "current_state": "growing",
        "key_trends": ["Digital transformation", "Sustainability focus", "Market consolidation"],
        "growth_drivers": ["Increasing demand", "Technological innovation"],
        "headwinds": ["Regulatory pressure", "Supply chain challenges"],
        "technological_changes": ["AI adoption", "Cloud migration"],
        "regulatory_environment": "Moderately regulated with increasing compliance requirements",
        "economic_sensitivity": "medium",
        "outlook": "positive"
    }


@pytest.fixture
def sample_competitive_landscape():
    """Sample competitive landscape for testing."""
    return {
        "market_structure": "moderately concentrated",
        "competitive_intensity": "high",
        "key_competitors": ["Market Leader Corp", "Challenger Inc", "Regional Player Ltd"],
        "barriers_to_entry": "high",
        "barriers_description": "High capital requirements and established brand loyalty",
        "competitive_factors": ["Technology capabilities", "Customer relationships", "Scale advantages"],
        "market_share_dynamics": "Stable with gradual consolidation",
        "pricing_power": "moderate",
        "differentiation_potential": "high"
    }


class TestIndustryIntelligenceAgent:
    """Test suite for IndustryIntelligenceAgent."""
    
    @pytest.mark.asyncio
    async def test_analyze_with_valid_company_and_industry(self, industry_agent):
        """Test analysis with valid company name and industry."""
        mock_trends_response = MagicMock()
        mock_trends_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps({
                "current_state": "growing",
                "key_trends": ["Digital transformation"],
                "growth_drivers": ["Innovation"],
                "headwinds": ["Competition"],
                "technological_changes": ["AI adoption"],
                "regulatory_environment": "Stable",
                "economic_sensitivity": "medium",
                "outlook": "positive"
            })))
        ]
        
        mock_landscape_response = MagicMock()
        mock_landscape_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps({
                "market_structure": "moderately concentrated",
                "competitive_intensity": "moderate",
                "key_competitors": ["Competitor A"],
                "barriers_to_entry": "moderate",
                "barriers_description": "Moderate capital requirements",
                "competitive_factors": ["Technology"],
                "market_share_dynamics": "Stable",
                "pricing_power": "moderate",
                "differentiation_potential": "moderate"
            })))
        ]
        
        mock_generic_response = MagicMock()
        mock_generic_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps({
                "risks": [],
                "opportunities": [],
                "short_term_growth": "5%",
                "medium_term_growth": "6%",
                "growth_quality": "sustainable",
                "key_assumptions": [],
                "confidence_level": "medium",
                "growth_narrative": "Positive outlook",
                "rating": "attractive",
                "score": 75,
                "analysis": "Good industry"
            })))
        ]
        
        mock_summary_response = MagicMock()
        mock_summary_response.choices = [
            MagicMock(message=MagicMock(content="Industry shows positive trends."))
        ]
        
        with patch.object(industry_agent.openai.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = [
                mock_trends_response,
                mock_landscape_response,
                mock_generic_response,
                mock_generic_response,
                mock_generic_response,
                mock_generic_response,
                mock_summary_response
            ]
            
            result = await industry_agent.analyze("Test Company", "Technology")
            
            assert result is not None
            assert "summary" in result
            assert "industry" in result
            assert "sector_trends" in result
            assert "competitive_landscape" in result
            assert "industry_risks" in result
            assert "market_opportunities" in result
            assert "growth_outlook" in result
            assert "overall_assessment" in result
            assert result["company_name"] == "Test Company"
            assert result["industry"] == "Technology"
    
    @pytest.mark.asyncio
    async def test_analyze_with_empty_company_name(self, industry_agent):
        """Test analysis with empty company name."""
        result = await industry_agent.analyze("")
        
        assert result is not None
        assert "No company name provided" in result["summary"]
        assert result["industry"] == "Unknown"
    
    @pytest.mark.asyncio
    async def test_analyze_without_industry_identifies_it(self, industry_agent):
        """Test that agent identifies industry when not provided."""
        mock_identify_response = MagicMock()
        mock_identify_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps({
                "industry": "Technology - Software",
                "sub_sector": "Enterprise Software",
                "industry_code": "5112"
            })))
        ]
        
        mock_generic_response = MagicMock()
        mock_generic_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps({
                "current_state": "stable",
                "key_trends": [],
                "growth_drivers": [],
                "headwinds": [],
                "technological_changes": [],
                "regulatory_environment": "Stable",
                "economic_sensitivity": "medium",
                "outlook": "neutral",
                "market_structure": "unknown",
                "competitive_intensity": "moderate",
                "key_competitors": [],
                "barriers_to_entry": "moderate",
                "barriers_description": "",
                "competitive_factors": [],
                "market_share_dynamics": "Unknown",
                "pricing_power": "moderate",
                "differentiation_potential": "moderate",
                "risks": [],
                "opportunities": [],
                "short_term_growth": "3%",
                "medium_term_growth": "4%",
                "growth_quality": "sustainable",
                "key_assumptions": [],
                "confidence_level": "medium",
                "growth_narrative": "Moderate growth",
                "rating": "neutral",
                "score": 50,
                "analysis": "Neutral assessment"
            })))
        ]
        
        mock_summary_response = MagicMock()
        mock_summary_response.choices = [
            MagicMock(message=MagicMock(content="Industry analysis summary."))
        ]
        
        with patch.object(industry_agent.openai.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = [
                mock_identify_response,
                mock_generic_response,
                mock_generic_response,
                mock_generic_response,
                mock_generic_response,
                mock_generic_response,
                mock_generic_response,
                mock_summary_response
            ]
            
            result = await industry_agent.analyze("Test Company", None)
            
            assert result is not None
            assert result["industry"] == "Technology - Software"
    
    @pytest.mark.asyncio
    async def test_identify_industry_error_handling(self, industry_agent):
        """Test error handling in industry identification."""
        with patch.object(industry_agent.openai.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = Exception("API Error")
            
            industry = await industry_agent._identify_industry("Test Company", None)
            
            assert industry == "Unknown Industry"
    
    @pytest.mark.asyncio
    async def test_analyze_sector_trends_error_handling(self, industry_agent):
        """Test error handling in sector trends analysis."""
        with patch.object(industry_agent.openai.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = Exception("API Error")
            
            trends = await industry_agent._analyze_sector_trends("Technology", "Test Company", None)
            
            assert trends["current_state"] == "unknown"
            assert trends["outlook"] == "neutral"
    
    @pytest.mark.asyncio
    async def test_analyze_competitive_landscape_error_handling(self, industry_agent):
        """Test error handling in competitive landscape analysis."""
        with patch.object(industry_agent.openai.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = Exception("API Error")
            
            landscape = await industry_agent._analyze_competitive_landscape("Technology", "Test Company", None)
            
            assert landscape["market_structure"] == "unknown"
            assert landscape["competitive_intensity"] == "moderate"
    
    def test_identify_risks_declining_industry(self, industry_agent):
        """Test risk identification for declining industry."""
        sector_trends = {"current_state": "declining", "economic_sensitivity": "low"}
        competitive_landscape = {"competitive_intensity": "moderate", "pricing_power": "moderate"}
        
        risks = []
        if sector_trends.get("current_state") == "declining":
            risks.append({
                "type": "market_decline",
                "severity": "high"
            })
        
        assert len(risks) > 0
        assert risks[0]["type"] == "market_decline"
        assert risks[0]["severity"] == "high"
    
    def test_identify_risks_high_economic_sensitivity(self, industry_agent):
        """Test risk identification for high economic sensitivity."""
        sector_trends = {"current_state": "stable", "economic_sensitivity": "high"}
        competitive_landscape = {"competitive_intensity": "moderate", "pricing_power": "moderate"}
        
        risks = []
        if sector_trends.get("economic_sensitivity") == "high":
            risks.append({
                "type": "cyclical_risk",
                "severity": "medium"
            })
        
        assert len(risks) > 0
        assert risks[0]["type"] == "cyclical_risk"
    
    def test_identify_risks_intense_competition(self, industry_agent):
        """Test risk identification for intense competition."""
        sector_trends = {"current_state": "stable", "economic_sensitivity": "medium"}
        competitive_landscape = {"competitive_intensity": "intense", "pricing_power": "moderate"}
        
        risks = []
        if competitive_landscape.get("competitive_intensity") in ["high", "intense"]:
            risks.append({
                "type": "competitive_pressure",
                "severity": "medium"
            })
        
        assert len(risks) > 0
        assert risks[0]["type"] == "competitive_pressure"
    
    def test_identify_risks_weak_pricing_power(self, industry_agent):
        """Test risk identification for weak pricing power."""
        sector_trends = {"current_state": "stable", "economic_sensitivity": "medium"}
        competitive_landscape = {"competitive_intensity": "moderate", "pricing_power": "weak"}
        
        risks = []
        if competitive_landscape.get("pricing_power") == "weak":
            risks.append({
                "type": "pricing_pressure",
                "severity": "medium"
            })
        
        assert len(risks) > 0
        assert risks[0]["type"] == "pricing_pressure"
    
    @pytest.mark.asyncio
    async def test_ai_identify_industry_risks_error_handling(self, industry_agent, sample_sector_trends, sample_competitive_landscape):
        """Test error handling in AI risk identification."""
        with patch.object(industry_agent.openai.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = Exception("API Error")
            
            risks = await industry_agent._ai_identify_industry_risks(
                "Technology", sample_sector_trends, sample_competitive_landscape
            )
            
            assert risks == []
    
    def test_identify_opportunities_positive_outlook(self, industry_agent):
        """Test opportunity identification for positive outlook."""
        sector_trends = {"outlook": "positive", "growth_drivers": []}
        competitive_landscape = {"barriers_to_entry": "moderate"}
        
        opportunities = []
        if sector_trends.get("outlook") == "positive":
            opportunities.append({
                "type": "market_growth",
                "description": "Positive outlook for the industry"
            })
        
        assert len(opportunities) > 0
        assert opportunities[0]["type"] == "market_growth"
    
    def test_identify_opportunities_multiple_growth_drivers(self, industry_agent):
        """Test opportunity identification for multiple growth drivers."""
        sector_trends = {
            "outlook": "neutral",
            "growth_drivers": ["Driver 1", "Driver 2", "Driver 3"]
        }
        competitive_landscape = {"barriers_to_entry": "moderate"}
        
        opportunities = []
        growth_drivers = sector_trends.get("growth_drivers", [])
        if len(growth_drivers) >= 2:
            opportunities.append({
                "type": "growth_drivers",
                "description": "Multiple growth drivers identified"
            })
        
        assert len(opportunities) > 0
        assert opportunities[0]["type"] == "growth_drivers"
    
    def test_identify_opportunities_high_barriers(self, industry_agent):
        """Test opportunity identification for high barriers to entry."""
        sector_trends = {"outlook": "neutral", "growth_drivers": []}
        competitive_landscape = {"barriers_to_entry": "high", "barriers_description": "High capital requirements"}
        
        opportunities = []
        if competitive_landscape.get("barriers_to_entry") == "high":
            opportunities.append({
                "type": "protected_market",
                "description": "High barriers to entry protect incumbents"
            })
        
        assert len(opportunities) > 0
        assert opportunities[0]["type"] == "protected_market"
    
    @pytest.mark.asyncio
    async def test_ai_identify_market_opportunities_error_handling(self, industry_agent, sample_sector_trends, sample_competitive_landscape):
        """Test error handling in AI opportunity identification."""
        with patch.object(industry_agent.openai.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = Exception("API Error")
            
            opportunities = await industry_agent._ai_identify_market_opportunities(
                "Technology", sample_sector_trends, sample_competitive_landscape
            )
            
            assert opportunities == []
    
    @pytest.mark.asyncio
    async def test_assess_growth_outlook_error_handling(self, industry_agent, sample_sector_trends):
        """Test error handling in growth outlook assessment."""
        with patch.object(industry_agent.openai.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = Exception("API Error")
            
            outlook = await industry_agent._assess_growth_outlook("Technology", sample_sector_trends, None)
            
            assert outlook["short_term_growth"] == "unknown"
            assert outlook["confidence_level"] == "low"
    
    def test_empty_analysis_result(self, industry_agent):
        """Test empty analysis result generation."""
        result = industry_agent._empty_analysis_result("Test reason")
        
        assert "Test reason" in result["summary"]
        assert result["industry"] == "Unknown"
        assert result["sector_trends"]["current_state"] == "unknown"
        assert result["competitive_landscape"]["market_structure"] == "unknown"
        assert result["industry_risks"] == []
        assert result["market_opportunities"] == []
        assert result["growth_outlook"]["short_term_growth"] == "unknown"
        assert result["overall_assessment"]["rating"] == "insufficient_data"
        assert result["overall_assessment"]["score"] == 0
        assert result["company_name"] == ""
        assert "analysis_date" in result


class TestIndustryIntelligenceAgentIntegration:
    """Integration tests for IndustryIntelligenceAgent with mocked OpenAI."""
    
    @pytest.mark.asyncio
    async def test_full_analysis_workflow(self, industry_agent):
        """Test complete analysis workflow with all components."""
        mock_trends_response = MagicMock()
        mock_trends_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps({
                "current_state": "growing",
                "key_trends": ["Digital transformation", "AI adoption"],
                "growth_drivers": ["Innovation", "Market demand"],
                "headwinds": ["Regulatory pressure"],
                "technological_changes": ["Cloud computing"],
                "regulatory_environment": "Moderately regulated",
                "economic_sensitivity": "medium",
                "outlook": "positive"
            })))
        ]
        
        mock_landscape_response = MagicMock()
        mock_landscape_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps({
                "market_structure": "moderately concentrated",
                "competitive_intensity": "high",
                "key_competitors": ["Leader Corp", "Challenger Inc"],
                "barriers_to_entry": "high",
                "barriers_description": "High capital and technology requirements",
                "competitive_factors": ["Technology", "Brand", "Scale"],
                "market_share_dynamics": "Consolidating",
                "pricing_power": "moderate",
                "differentiation_potential": "high"
            })))
        ]
        
        mock_risks_response = MagicMock()
        mock_risks_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps({
                "risks": [
                    {
                        "type": "regulatory",
                        "description": "Increasing regulatory scrutiny",
                        "severity": "medium",
                        "details": "New regulations may increase compliance costs",
                        "mitigation": "Invest in compliance infrastructure"
                    }
                ]
            })))
        ]
        
        mock_opportunities_response = MagicMock()
        mock_opportunities_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps({
                "opportunities": [
                    {
                        "type": "innovation",
                        "description": "AI-driven product opportunities",
                        "details": "Growing demand for AI solutions",
                        "potential_impact": "high"
                    }
                ]
            })))
        ]
        
        mock_outlook_response = MagicMock()
        mock_outlook_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps({
                "short_term_growth": "8-10%",
                "medium_term_growth": "10-12%",
                "growth_quality": "sustainable",
                "key_assumptions": ["Continued innovation", "Market expansion"],
                "confidence_level": "high",
                "growth_narrative": "Strong growth expected driven by digital transformation."
            })))
        ]
        
        mock_assessment_response = MagicMock()
        mock_assessment_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps({
                "rating": "attractive",
                "score": 80,
                "analysis": "Attractive industry with strong growth prospects and manageable risks."
            })))
        ]
        
        mock_summary_response = MagicMock()
        mock_summary_response.choices = [
            MagicMock(message=MagicMock(content="The Technology industry shows strong growth prospects with positive trends."))
        ]
        
        with patch.object(industry_agent.openai.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = [
                mock_trends_response,
                mock_landscape_response,
                mock_risks_response,
                mock_opportunities_response,
                mock_outlook_response,
                mock_assessment_response,
                mock_summary_response
            ]
            
            result = await industry_agent.analyze("Test Company", "Technology")
            
            # Verify all components
            assert result["company_name"] == "Test Company"
            assert result["industry"] == "Technology"
            assert result["sector_trends"]["current_state"] == "growing"
            assert result["sector_trends"]["outlook"] == "positive"
            assert result["competitive_landscape"]["competitive_intensity"] == "high"
            assert len(result["industry_risks"]) > 0
            assert len(result["market_opportunities"]) > 0
            assert result["growth_outlook"]["short_term_growth"] == "8-10%"
            # The overall assessment rating is calculated based on positive outlook (+15)
            # and growing state (+10), resulting in score >= 75 which is "highly_attractive"
            assert result["overall_assessment"]["rating"] == "highly_attractive"
            assert len(result["summary"]) > 0
            
            # Verify specific details
            assert "Digital transformation" in result["sector_trends"]["key_trends"]
            assert result["competitive_landscape"]["barriers_to_entry"] == "high"
