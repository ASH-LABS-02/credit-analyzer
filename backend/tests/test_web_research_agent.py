"""
Unit tests for WebResearchAgent

Tests the web research functionality including news gathering,
red flag identification, positive indicator detection, and source citation.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
import json

from app.agents.web_research_agent import WebResearchAgent


@pytest.fixture
def web_research_agent():
    """Create a WebResearchAgent instance for testing."""
    return WebResearchAgent()


@pytest.fixture
def sample_news_items():
    """Sample news items for testing."""
    return [
        {
            "title": "Company XYZ Announces Major Expansion",
            "summary": "Company XYZ announced plans to expand operations into three new markets.",
            "source": "Business News Daily",
            "date": "2024-01-15",
            "url": "https://example.com/news/xyz-expansion",
            "relevance": "high"
        },
        {
            "title": "Company XYZ Faces Lawsuit Over Contract Dispute",
            "summary": "A major client has filed a lawsuit against Company XYZ alleging breach of contract.",
            "source": "Legal Times",
            "date": "2024-01-10",
            "url": "https://example.com/news/xyz-lawsuit",
            "relevance": "high"
        },
        {
            "title": "Company XYZ Reports Strong Q4 Results",
            "summary": "Company XYZ reported revenue growth of 25% in Q4, exceeding analyst expectations.",
            "source": "Financial Post",
            "date": "2024-01-05",
            "url": "https://example.com/news/xyz-q4-results",
            "relevance": "high"
        }
    ]


class TestWebResearchAgent:
    """Test suite for WebResearchAgent."""
    
    @pytest.mark.asyncio
    async def test_research_with_valid_company_name(self, web_research_agent):
        """Test research with a valid company name."""
        # Mock OpenAI responses
        mock_news_response = MagicMock()
        mock_news_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps({
                "news_items": [
                    {
                        "title": "Test Company Announces Growth",
                        "summary": "Test Company reported strong growth in recent quarter.",
                        "source": "Business News",
                        "date": "2024-01-15",
                        "url": "https://example.com/news/test",
                        "relevance": "high"
                    }
                ]
            })))
        ]
        
        mock_summary_response = MagicMock()
        mock_summary_response.choices = [
            MagicMock(message=MagicMock(content="Test Company shows positive growth trends with no significant red flags identified."))
        ]
        
        with patch.object(web_research_agent.openai.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            # First call returns news items, subsequent calls return summaries
            mock_create.side_effect = [
                mock_news_response,  # _gather_news
                mock_summary_response  # _generate_research_summary
            ]
            
            result = await web_research_agent.research("Test Company")
            
            assert result is not None
            assert "summary" in result
            assert "news_items" in result
            assert "red_flags" in result
            assert "positive_indicators" in result
            assert "sources" in result
            assert "research_date" in result
            assert result["company_name"] == "Test Company"
            assert len(result["news_items"]) > 0
    
    @pytest.mark.asyncio
    async def test_research_with_empty_company_name(self, web_research_agent):
        """Test research with empty company name."""
        result = await web_research_agent.research("")
        
        assert result is not None
        assert "No company name provided" in result["summary"]
        assert len(result["news_items"]) == 0
        assert len(result["red_flags"]) == 0
        assert len(result["positive_indicators"]) == 0
    
    @pytest.mark.asyncio
    async def test_research_with_additional_context(self, web_research_agent):
        """Test research with additional context."""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps({
                "news_items": [
                    {
                        "title": "Tech Company Innovation",
                        "summary": "Company launches new product in technology sector.",
                        "source": "Tech News",
                        "date": "2024-01-15",
                        "url": "https://example.com/news/tech",
                        "relevance": "high"
                    }
                ]
            })))
        ]
        
        mock_summary_response = MagicMock()
        mock_summary_response.choices = [
            MagicMock(message=MagicMock(content="Research summary for tech company."))
        ]
        
        with patch.object(web_research_agent.openai.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = [mock_response, mock_summary_response]
            
            additional_context = {
                "industry": "Technology",
                "location": "San Francisco"
            }
            
            result = await web_research_agent.research("Tech Company", additional_context)
            
            assert result is not None
            assert result["company_name"] == "Tech Company"
    
    def test_identify_red_flags_from_keywords(self, web_research_agent, sample_news_items):
        """Test red flag identification from keyword matching."""
        # The sample news items include a lawsuit, which should be flagged
        red_flags = []
        
        for item in sample_news_items:
            title_lower = item.get("title", "").lower()
            summary_lower = item.get("summary", "").lower()
            combined_text = f"{title_lower} {summary_lower}"
            
            found_keywords = [
                keyword for keyword in web_research_agent.RED_FLAG_KEYWORDS
                if keyword in combined_text
            ]
            
            if found_keywords:
                severity = web_research_agent._assess_red_flag_severity(found_keywords)
                red_flags.append({
                    "description": item.get("title", ""),
                    "severity": severity,
                    "keywords": found_keywords
                })
        
        assert len(red_flags) > 0
        assert any("lawsuit" in flag["keywords"] for flag in red_flags)
    
    def test_assess_red_flag_severity_critical(self, web_research_agent):
        """Test severity assessment for critical keywords."""
        keywords = ["bankruptcy", "fraud"]
        severity = web_research_agent._assess_red_flag_severity(keywords)
        assert severity == "critical"
    
    def test_assess_red_flag_severity_high(self, web_research_agent):
        """Test severity assessment for high severity keywords."""
        keywords = ["lawsuit", "investigation"]
        severity = web_research_agent._assess_red_flag_severity(keywords)
        assert severity == "high"
    
    def test_assess_red_flag_severity_medium(self, web_research_agent):
        """Test severity assessment for medium severity."""
        keywords = ["warning", "concern"]
        severity = web_research_agent._assess_red_flag_severity(keywords)
        assert severity == "medium"
    
    def test_assess_red_flag_severity_low(self, web_research_agent):
        """Test severity assessment for low severity."""
        keywords = ["risk"]
        severity = web_research_agent._assess_red_flag_severity(keywords)
        assert severity == "low"
    
    def test_identify_positive_indicators_from_keywords(self, web_research_agent, sample_news_items):
        """Test positive indicator identification from keyword matching."""
        positive_indicators = []
        
        for item in sample_news_items:
            title_lower = item.get("title", "").lower()
            summary_lower = item.get("summary", "").lower()
            combined_text = f"{title_lower} {summary_lower}"
            
            found_keywords = [
                keyword for keyword in web_research_agent.POSITIVE_KEYWORDS
                if keyword in combined_text
            ]
            
            if found_keywords:
                positive_indicators.append({
                    "description": item.get("title", ""),
                    "keywords": found_keywords
                })
        
        # Should find "expansion" and "growth" keywords
        assert len(positive_indicators) > 0
        assert any("expansion" in indicator["keywords"] or "growth" in indicator["keywords"] 
                  for indicator in positive_indicators)
    
    def test_compile_sources(self, web_research_agent, sample_news_items):
        """Test source compilation and deduplication."""
        sources = web_research_agent._compile_sources(
            news_items=sample_news_items,
            red_flags=[],
            positive_indicators=[]
        )
        
        assert len(sources) == len(sample_news_items)
        
        # Check that each source has required fields
        for source in sources:
            assert "name" in source
            assert "url" in source
            assert "title" in source
            assert "date" in source
            assert "access_date" in source
        
        # Check that URLs are unique
        urls = [s["url"] for s in sources]
        assert len(urls) == len(set(urls))
    
    def test_compile_sources_deduplication(self, web_research_agent):
        """Test that duplicate sources are removed."""
        news_items = [
            {
                "title": "News 1",
                "source": "Source A",
                "url": "https://example.com/news1",
                "date": "2024-01-15"
            },
            {
                "title": "News 2",
                "source": "Source A",
                "url": "https://example.com/news1",  # Duplicate URL
                "date": "2024-01-16"
            }
        ]
        
        sources = web_research_agent._compile_sources(
            news_items=news_items,
            red_flags=[],
            positive_indicators=[]
        )
        
        # Should only have one source due to deduplication
        assert len(sources) == 1
    
    def test_generate_fallback_summary_with_red_flags(self, web_research_agent):
        """Test fallback summary generation with red flags."""
        news_items = [{"title": "News 1"}, {"title": "News 2"}]
        red_flags = [
            {
                "description": "Critical Issue",
                "severity": "critical"
            }
        ]
        positive_indicators = []
        
        summary = web_research_agent._generate_fallback_summary(
            "Test Company",
            news_items,
            red_flags,
            positive_indicators
        )
        
        assert "Test Company" in summary
        assert "2 relevant news items" in summary
        assert "CRITICAL CONCERN" in summary
        assert "Critical Issue" in summary
    
    def test_generate_fallback_summary_with_positive_indicators(self, web_research_agent):
        """Test fallback summary generation with positive indicators."""
        news_items = [{"title": "News 1"}]
        red_flags = []
        positive_indicators = [
            {
                "description": "Major Expansion"
            }
        ]
        
        summary = web_research_agent._generate_fallback_summary(
            "Test Company",
            news_items,
            red_flags,
            positive_indicators
        )
        
        assert "Test Company" in summary
        assert "No significant red flags" in summary
        assert "1 positive indicator" in summary
        assert "Major Expansion" in summary
    
    def test_generate_fallback_summary_balanced(self, web_research_agent):
        """Test fallback summary with both red flags and positive indicators."""
        news_items = [{"title": "News 1"}, {"title": "News 2"}]
        red_flags = [
            {
                "description": "Minor Issue",
                "severity": "low"
            }
        ]
        positive_indicators = [
            {
                "description": "Growth Achievement"
            }
        ]
        
        summary = web_research_agent._generate_fallback_summary(
            "Test Company",
            news_items,
            red_flags,
            positive_indicators
        )
        
        assert "Test Company" in summary
        assert "concern" in summary.lower()
        assert "positive indicator" in summary.lower()
    
    @pytest.mark.asyncio
    async def test_gather_news_error_handling(self, web_research_agent):
        """Test error handling in news gathering."""
        with patch.object(web_research_agent.openai.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = Exception("API Error")
            
            news_items = await web_research_agent._gather_news("Test Company", None)
            
            # Should return empty list on error
            assert news_items == []
    
    @pytest.mark.asyncio
    async def test_ai_identify_red_flags_error_handling(self, web_research_agent):
        """Test error handling in AI red flag identification."""
        news_items = [{"title": "Test News", "summary": "Test summary"}]
        
        with patch.object(web_research_agent.openai.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = Exception("API Error")
            
            red_flags = await web_research_agent._ai_identify_red_flags("Test Company", news_items)
            
            # Should return empty list on error
            assert red_flags == []
    
    @pytest.mark.asyncio
    async def test_generate_research_summary_error_handling(self, web_research_agent):
        """Test error handling in summary generation."""
        news_items = [{"title": "Test News"}]
        red_flags = []
        positive_indicators = []
        
        with patch.object(web_research_agent.openai.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = Exception("API Error")
            
            summary = await web_research_agent._generate_research_summary(
                "Test Company",
                news_items,
                red_flags,
                positive_indicators
            )
            
            # Should return fallback summary
            assert "Test Company" in summary
            assert len(summary) > 0
    
    def test_empty_research_result(self, web_research_agent):
        """Test empty research result generation."""
        result = web_research_agent._empty_research_result("Test reason")
        
        assert "Test reason" in result["summary"]
        assert result["news_items"] == []
        assert result["red_flags"] == []
        assert result["positive_indicators"] == []
        assert result["sources"] == []
        assert result["company_name"] == ""
        assert "research_date" in result


class TestWebResearchAgentIntegration:
    """Integration tests for WebResearchAgent with mocked OpenAI."""
    
    @pytest.mark.asyncio
    async def test_full_research_workflow(self, web_research_agent):
        """Test complete research workflow with all components."""
        # Mock OpenAI responses for the full workflow
        mock_news_response = MagicMock()
        mock_news_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps({
                "news_items": [
                    {
                        "title": "Company Faces Lawsuit",
                        "summary": "Company is being sued for breach of contract.",
                        "source": "Legal News",
                        "date": "2024-01-15",
                        "url": "https://example.com/lawsuit",
                        "relevance": "high"
                    },
                    {
                        "title": "Company Announces Expansion",
                        "summary": "Company plans to expand into new markets.",
                        "source": "Business News",
                        "date": "2024-01-10",
                        "url": "https://example.com/expansion",
                        "relevance": "high"
                    }
                ]
            })))
        ]
        
        mock_red_flags_response = MagicMock()
        mock_red_flags_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps({
                "red_flags": [
                    {
                        "description": "Legal dispute with major client",
                        "details": "Ongoing lawsuit may impact revenue",
                        "severity": "high",
                        "source": "Legal News"
                    }
                ]
            })))
        ]
        
        mock_positive_response = MagicMock()
        mock_positive_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps({
                "positive_indicators": [
                    {
                        "description": "Strategic market expansion",
                        "details": "Entering three new markets",
                        "source": "Business News"
                    }
                ]
            })))
        ]
        
        mock_summary_response = MagicMock()
        mock_summary_response.choices = [
            MagicMock(message=MagicMock(content="Company shows mixed signals with expansion plans offset by legal challenges."))
        ]
        
        with patch.object(web_research_agent.openai.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = [
                mock_news_response,
                mock_red_flags_response,
                mock_positive_response,
                mock_summary_response
            ]
            
            result = await web_research_agent.research("Test Company")
            
            # Verify all components are present
            assert result["company_name"] == "Test Company"
            assert len(result["news_items"]) == 2
            assert len(result["red_flags"]) > 0  # Should have keyword-matched + AI-identified
            assert len(result["positive_indicators"]) > 0
            assert len(result["sources"]) > 0
            assert len(result["summary"]) > 0
            
            # Verify red flags include both keyword-matched and AI-identified
            red_flag_descriptions = [rf["description"] for rf in result["red_flags"]]
            assert any("lawsuit" in desc.lower() for desc in red_flag_descriptions)
            
            # Verify sources are compiled
            assert len(result["sources"]) >= 2
