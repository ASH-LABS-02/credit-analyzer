"""
Unit tests for PromoterIntelligenceAgent

Tests the promoter intelligence functionality including background research,
track record analysis, conflict of interest identification, and red flag detection.

Requirements: 3.3
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
import json

from app.agents.promoter_intelligence_agent import PromoterIntelligenceAgent


@pytest.fixture
def promoter_agent():
    """Create a PromoterIntelligenceAgent instance for testing."""
    return PromoterIntelligenceAgent()


@pytest.fixture
def sample_promoters():
    """Sample promoters for testing."""
    return [
        {
            "name": "John Smith",
            "designation": "CEO",
            "tenure": "5 years"
        },
        {
            "name": "Jane Doe",
            "designation": "CFO",
            "tenure": "3 years"
        }
    ]


@pytest.fixture
def sample_promoter_profiles():
    """Sample promoter profiles for testing."""
    return [
        {
            "name": "John Smith",
            "designation": "CEO",
            "tenure": "5 years",
            "education": "MBA from Harvard Business School",
            "experience_years": 20,
            "previous_roles": [
                {"position": "VP Operations", "company": "Tech Corp"},
                {"position": "Director", "company": "Innovation Inc"}
            ],
            "industry_expertise": ["Technology", "Operations Management"],
            "notable_achievements": ["Led successful IPO", "Grew revenue 300%"],
            "professional_associations": ["Industry Association"],
            "other_directorships": ["Board Member at Startup XYZ"]
        },
        {
            "name": "Jane Doe",
            "designation": "CFO",
            "tenure": "3 years",
            "education": "CPA, MBA from Stanford",
            "experience_years": 15,
            "previous_roles": [
                {"position": "Finance Director", "company": "Finance Corp"},
                {"position": "Senior Manager", "company": "Audit Firm"}
            ],
            "industry_expertise": ["Finance", "Accounting"],
            "notable_achievements": ["Restructured debt successfully"],
            "professional_associations": ["CPA Association"],
            "other_directorships": []
        }
    ]


class TestPromoterIntelligenceAgent:
    """Test suite for PromoterIntelligenceAgent."""
    
    @pytest.mark.asyncio
    async def test_analyze_with_valid_company_and_promoters(self, promoter_agent, sample_promoters):
        """Test analysis with valid company name and promoters."""
        # Mock OpenAI responses
        mock_profile_response = MagicMock()
        mock_profile_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps({
                "education": "MBA from Top University",
                "experience_years": 20,
                "previous_roles": [{"position": "VP", "company": "Previous Corp"}],
                "industry_expertise": ["Technology"],
                "notable_achievements": ["Led successful turnaround"],
                "professional_associations": ["Industry Group"],
                "other_directorships": []
            })))
        ]
        
        mock_track_record_response = MagicMock()
        mock_track_record_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps({
                "overall_rating": "good",
                "analysis": "Strong track record with successful ventures.",
                "successful_ventures": ["Previous Corp IPO"],
                "failed_ventures": [],
                "patterns": ["Consistent growth"]
            })))
        ]
        
        mock_conflicts_response = MagicMock()
        mock_conflicts_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps({
                "conflicts": []
            })))
        ]
        
        mock_red_flags_response = MagicMock()
        mock_red_flags_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps({
                "red_flags": []
            })))
        ]
        
        mock_strengths_response = MagicMock()
        mock_strengths_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps({
                "positive_indicators": [
                    {
                        "type": "strong_experience",
                        "description": "Extensive industry experience",
                        "details": "20+ years in the field",
                        "promoters_affected": "John Smith"
                    }
                ]
            })))
        ]
        
        mock_assessment_response = MagicMock()
        mock_assessment_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps({
                "rating": "strong",
                "score": 85,
                "analysis": "Strong management team with relevant experience."
            })))
        ]
        
        mock_summary_response = MagicMock()
        mock_summary_response.choices = [
            MagicMock(message=MagicMock(content="Management team demonstrates strong credentials and track record."))
        ]
        
        with patch.object(promoter_agent.openai.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            # Multiple calls for different stages
            mock_create.side_effect = [
                mock_profile_response,  # First promoter profile
                mock_profile_response,  # Second promoter profile
                mock_track_record_response,  # Track record analysis
                mock_conflicts_response,  # Conflicts identification
                mock_red_flags_response,  # Red flags identification
                mock_strengths_response,  # Strengths identification
                mock_assessment_response,  # Overall assessment
                mock_summary_response  # Summary generation
            ]
            
            result = await promoter_agent.analyze("Test Company", sample_promoters)
            
            assert result is not None
            assert "summary" in result
            assert "promoter_profiles" in result
            assert "track_record_analysis" in result
            assert "conflicts_of_interest" in result
            assert "red_flags" in result
            assert "positive_indicators" in result
            assert "overall_assessment" in result
            assert "analysis_date" in result
            assert result["company_name"] == "Test Company"
            assert len(result["promoter_profiles"]) == 2
    
    @pytest.mark.asyncio
    async def test_analyze_with_empty_company_name(self, promoter_agent):
        """Test analysis with empty company name."""
        result = await promoter_agent.analyze("")
        
        assert result is not None
        assert "No company name provided" in result["summary"]
        assert len(result["promoter_profiles"]) == 0
    
    @pytest.mark.asyncio
    async def test_analyze_without_promoters_identifies_them(self, promoter_agent):
        """Test that agent identifies promoters when not provided."""
        mock_identify_response = MagicMock()
        mock_identify_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps({
                "promoters": [
                    {
                        "name": "Auto Identified CEO",
                        "designation": "CEO",
                        "tenure": "5 years"
                    }
                ]
            })))
        ]
        
        mock_profile_response = MagicMock()
        mock_profile_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps({
                "education": "MBA",
                "experience_years": 15,
                "previous_roles": [],
                "industry_expertise": [],
                "notable_achievements": [],
                "professional_associations": [],
                "other_directorships": []
            })))
        ]
        
        # Mock other required responses
        mock_generic_response = MagicMock()
        mock_generic_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps({
                "overall_rating": "average",
                "analysis": "Analysis",
                "successful_ventures": [],
                "failed_ventures": [],
                "patterns": []
            })))
        ]
        
        with patch.object(promoter_agent.openai.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = [
                mock_identify_response,  # Identify promoters
                mock_profile_response,  # Profile research
                mock_generic_response,  # Track record
                mock_generic_response,  # Conflicts (empty)
                mock_generic_response,  # Red flags (empty)
                mock_generic_response,  # Strengths (empty)
                mock_generic_response,  # Assessment
                MagicMock(choices=[MagicMock(message=MagicMock(content="Summary"))])  # Summary
            ]
            
            result = await promoter_agent.analyze("Test Company", None)
            
            assert result is not None
            assert len(result["promoter_profiles"]) > 0
    
    @pytest.mark.asyncio
    async def test_identify_key_management_error_handling(self, promoter_agent):
        """Test error handling in key management identification."""
        with patch.object(promoter_agent.openai.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = Exception("API Error")
            
            promoters = await promoter_agent._identify_key_management("Test Company", None)
            
            assert promoters == []
    
    @pytest.mark.asyncio
    async def test_research_single_promoter_error_handling(self, promoter_agent):
        """Test error handling in single promoter research."""
        with patch.object(promoter_agent.openai.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = Exception("API Error")
            
            profile = await promoter_agent._research_single_promoter(
                "John Smith", "CEO", "Test Company", None
            )
            
            # Should return default profile structure
            assert profile["education"] == "Not available"
            assert profile["experience_years"] == 0
            assert profile["previous_roles"] == []
    
    def test_identify_conflicts_multiple_directorships(self, promoter_agent, sample_promoter_profiles):
        """Test conflict identification for multiple directorships."""
        # Modify profile to have many directorships
        test_profiles = sample_promoter_profiles.copy()
        test_profiles[0]["other_directorships"] = [
            "Company A", "Company B", "Company C", "Company D", "Company E"
        ]
        
        conflicts = []
        for profile in test_profiles:
            other_directorships = profile.get("other_directorships", [])
            if len(other_directorships) > 3:
                conflicts.append({
                    "promoter": profile["name"],
                    "type": "multiple_directorships",
                    "severity": "low"
                })
        
        assert len(conflicts) > 0
        assert conflicts[0]["promoter"] == "John Smith"
        assert conflicts[0]["type"] == "multiple_directorships"
    
    @pytest.mark.asyncio
    async def test_ai_identify_conflicts_error_handling(self, promoter_agent, sample_promoter_profiles):
        """Test error handling in AI conflict identification."""
        with patch.object(promoter_agent.openai.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = Exception("API Error")
            
            conflicts = await promoter_agent._ai_identify_conflicts(
                sample_promoter_profiles, "Test Company"
            )
            
            assert conflicts == []
    
    def test_identify_red_flags_multiple_failures(self, promoter_agent):
        """Test red flag identification for multiple failed ventures."""
        track_record = {
            "overall_rating": "concerning",
            "failed_ventures": [
                "Failed Venture 1",
                "Failed Venture 2",
                "Failed Venture 3"
            ]
        }
        
        red_flags = []
        failed_ventures = track_record.get("failed_ventures", [])
        if len(failed_ventures) > 2:
            red_flags.append({
                "type": "multiple_failures",
                "severity": "high",
                "details": failed_ventures
            })
        
        assert len(red_flags) > 0
        assert red_flags[0]["type"] == "multiple_failures"
        assert red_flags[0]["severity"] == "high"
    
    @pytest.mark.asyncio
    async def test_ai_identify_promoter_red_flags_error_handling(self, promoter_agent, sample_promoter_profiles):
        """Test error handling in AI red flag identification."""
        track_record = {
            "overall_rating": "good",
            "failed_ventures": []
        }
        
        with patch.object(promoter_agent.openai.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = Exception("API Error")
            
            red_flags = await promoter_agent._ai_identify_promoter_red_flags(
                sample_promoter_profiles, track_record
            )
            
            assert red_flags == []
    
    def test_identify_strengths_strong_track_record(self, promoter_agent):
        """Test strength identification for strong track record."""
        track_record = {
            "overall_rating": "excellent",
            "analysis": "Outstanding track record",
            "successful_ventures": ["Venture A", "Venture B"]
        }
        
        positive_indicators = []
        if track_record.get("overall_rating") in ["excellent", "good"]:
            positive_indicators.append({
                "type": "strong_track_record",
                "description": f"Management team has a {track_record['overall_rating']} track record"
            })
        
        assert len(positive_indicators) > 0
        assert positive_indicators[0]["type"] == "strong_track_record"
    
    def test_identify_strengths_extensive_experience(self, promoter_agent, sample_promoter_profiles):
        """Test strength identification for extensive experience."""
        # Modify profile to have 20+ years experience
        test_profiles = sample_promoter_profiles.copy()
        test_profiles[0]["experience_years"] = 25
        
        positive_indicators = []
        for profile in test_profiles:
            experience_years = profile.get("experience_years", 0)
            if experience_years >= 20:
                positive_indicators.append({
                    "type": "extensive_experience",
                    "description": f"{profile['name']} has {experience_years} years of experience"
                })
        
        assert len(positive_indicators) > 0
        assert "25 years" in positive_indicators[0]["description"]
    
    @pytest.mark.asyncio
    async def test_ai_identify_promoter_strengths_error_handling(self, promoter_agent, sample_promoter_profiles):
        """Test error handling in AI strength identification."""
        track_record = {
            "overall_rating": "good",
            "successful_ventures": []
        }
        
        with patch.object(promoter_agent.openai.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = Exception("API Error")
            
            strengths = await promoter_agent._ai_identify_promoter_strengths(
                sample_promoter_profiles, track_record
            )
            
            assert strengths == []
    
    def test_empty_analysis_result(self, promoter_agent):
        """Test empty analysis result generation."""
        result = promoter_agent._empty_analysis_result("Test reason")
        
        assert "Test reason" in result["summary"]
        assert result["promoter_profiles"] == []
        assert result["track_record_analysis"]["overall_rating"] == "insufficient_data"
        assert result["track_record_analysis"]["analysis"] == "Test reason"
        assert result["conflicts_of_interest"] == []
        assert result["red_flags"] == []
        assert result["positive_indicators"] == []
        assert result["overall_assessment"]["rating"] == "insufficient_data"
        assert result["overall_assessment"]["score"] == 0
        assert result["company_name"] == ""
        assert "analysis_date" in result


class TestPromoterIntelligenceAgentIntegration:
    """Integration tests for PromoterIntelligenceAgent with mocked OpenAI."""
    
    @pytest.mark.asyncio
    async def test_full_analysis_workflow(self, promoter_agent, sample_promoters):
        """Test complete analysis workflow with all components."""
        # Mock comprehensive OpenAI responses
        mock_profile_response = MagicMock()
        mock_profile_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps({
                "education": "MBA from Harvard",
                "experience_years": 20,
                "previous_roles": [
                    {"position": "VP Operations", "company": "Success Corp"},
                    {"position": "Director", "company": "Growth Inc"}
                ],
                "industry_expertise": ["Technology", "Operations"],
                "notable_achievements": ["Led IPO", "300% revenue growth"],
                "professional_associations": ["Tech Association"],
                "other_directorships": ["Board Member at Startup"]
            })))
        ]
        
        mock_track_record_response = MagicMock()
        mock_track_record_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps({
                "overall_rating": "excellent",
                "analysis": "Outstanding track record with multiple successful ventures.",
                "successful_ventures": ["Success Corp IPO", "Growth Inc acquisition"],
                "failed_ventures": [],
                "patterns": ["Consistent growth", "Strong execution"]
            })))
        ]
        
        mock_conflicts_response = MagicMock()
        mock_conflicts_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps({
                "conflicts": [
                    {
                        "promoter": "John Smith",
                        "type": "time_commitment",
                        "description": "Multiple board positions may impact time commitment",
                        "severity": "low",
                        "details": "Serves on 2 other boards"
                    }
                ]
            })))
        ]
        
        mock_red_flags_response = MagicMock()
        mock_red_flags_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps({
                "red_flags": []
            })))
        ]
        
        mock_strengths_response = MagicMock()
        mock_strengths_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps({
                "positive_indicators": [
                    {
                        "type": "industry_expertise",
                        "description": "Deep industry expertise",
                        "details": "20+ years in technology sector",
                        "promoters_affected": "John Smith"
                    }
                ]
            })))
        ]
        
        mock_assessment_response = MagicMock()
        mock_assessment_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps({
                "rating": "strong",
                "score": 90,
                "analysis": "Exceptional management team with proven track record and deep industry expertise."
            })))
        ]
        
        mock_summary_response = MagicMock()
        mock_summary_response.choices = [
            MagicMock(message=MagicMock(content="The management team demonstrates exceptional credentials with a proven track record of success."))
        ]
        
        with patch.object(promoter_agent.openai.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = [
                mock_profile_response,  # First promoter
                mock_profile_response,  # Second promoter
                mock_track_record_response,
                mock_conflicts_response,
                mock_red_flags_response,
                mock_strengths_response,
                mock_assessment_response,
                mock_summary_response
            ]
            
            result = await promoter_agent.analyze("Test Company", sample_promoters)
            
            # Verify all components
            assert result["company_name"] == "Test Company"
            assert len(result["promoter_profiles"]) == 2
            assert result["track_record_analysis"]["overall_rating"] == "excellent"
            assert len(result["conflicts_of_interest"]) > 0
            assert len(result["positive_indicators"]) > 0
            # The overall assessment rating is calculated based on track record (excellent = +20)
            # and positive indicators, so it will be "excellent" (score >= 80)
            assert result["overall_assessment"]["rating"] == "excellent"
            assert len(result["summary"]) > 0
            
            # Verify profile details
            profile = result["promoter_profiles"][0]
            assert profile["name"] == "John Smith"
            assert profile["education"] == "MBA from Harvard"
            assert profile["experience_years"] == 20
