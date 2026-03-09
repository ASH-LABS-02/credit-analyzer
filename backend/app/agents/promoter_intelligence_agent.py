"""
Promoter Intelligence Agent

This agent analyzes company directors and key management personnel (promoters)
by researching their backgrounds, track records, and identifying any conflicts
of interest or reputation issues.

Requirements: 3.3
"""

import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from openai import AsyncOpenAI

from app.core.config import settings
from app.core.audit_logger import AuditLogger


class PromoterIntelligenceAgent:
    """
    AI agent for analyzing company promoters and key management.
    
    Performs promoter intelligence gathering to:
    - Research director backgrounds and professional history
    - Analyze track records from past business ventures
    - Identify conflicts of interest
    - Assess management quality and experience
    - Flag reputation issues or concerns
    
    Requirements: 3.3
    """
    
    # Red flag keywords for promoter analysis
    PROMOTER_RED_FLAGS = [
        "fraud", "convicted", "criminal", "investigation", "scandal",
        "misconduct", "violation", "penalty", "sanction", "banned",
        "disqualified", "removed", "resigned under pressure", "conflict of interest",
        "insider trading", "embezzlement", "misappropriation",
        "failed business", "bankruptcy", "liquidation", "wound up",
        "regulatory action", "disciplinary action", "censure"
    ]
    
    # Positive indicator keywords for promoters
    PROMOTER_POSITIVE_INDICATORS = [
        "award", "recognition", "achievement", "successful exit",
        "industry leader", "expert", "pioneer", "innovator",
        "board member", "advisor", "mentor", "speaker",
        "published", "patent", "certification", "qualification",
        "growth", "turnaround", "profitable", "ipo", "acquisition"
    ]
    
    def __init__(self, audit_logger: Optional[AuditLogger] = None):
        """
        Initialize the Promoter Intelligence Agent.
        
        Args:
            audit_logger: Optional audit logger for AI decision logging
        """
        self.openai = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.audit_logger = audit_logger
    
    async def analyze(
        self,
        company_name: str,
        promoters: Optional[List[Dict[str, str]]] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Conduct comprehensive promoter intelligence analysis.
        
        Args:
            company_name: Name of the company
            promoters: List of promoters with name, designation, etc.
                      If None, will attempt to identify key management
            additional_context: Optional additional context (industry, etc.)
        
        Returns:
            Dictionary containing:
                - summary: Overall promoter analysis summary
                - promoter_profiles: Detailed profiles for each promoter
                - track_record_analysis: Analysis of past business ventures
                - conflicts_of_interest: Identified conflicts
                - red_flags: List of concerns or red flags
                - positive_indicators: Strengths and positive findings
                - overall_assessment: Overall management quality assessment
                - analysis_date: Timestamp of analysis
        
        Requirements: 3.3
        """
        if not company_name:
            return self._empty_analysis_result("No company name provided")
        
        # If promoters not provided, attempt to identify them
        if not promoters:
            promoters = await self._identify_key_management(company_name, additional_context)
        
        if not promoters:
            return self._empty_analysis_result(
                f"Could not identify key management for {company_name}"
            )
        
        # Step 1: Research background for each promoter
        promoter_profiles = await self._research_promoter_backgrounds(
            promoters, company_name, additional_context
        )
        
        # Step 2: Analyze track records
        track_record_analysis = await self._analyze_track_records(
            promoter_profiles, company_name
        )
        
        # Step 3: Identify conflicts of interest
        conflicts = await self._identify_conflicts_of_interest(
            promoter_profiles, company_name
        )
        
        # Step 4: Identify red flags
        red_flags = await self._identify_promoter_red_flags(
            promoter_profiles, track_record_analysis
        )
        
        # Step 5: Identify positive indicators
        positive_indicators = await self._identify_promoter_strengths(
            promoter_profiles, track_record_analysis
        )
        
        # Step 6: Generate overall assessment
        overall_assessment = await self._generate_overall_assessment(
            promoter_profiles,
            track_record_analysis,
            conflicts,
            red_flags,
            positive_indicators
        )
        
        # Step 7: Generate summary
        summary = await self._generate_promoter_summary(
            company_name,
            promoter_profiles,
            red_flags,
            positive_indicators,
            overall_assessment
        )
        
        result = {
            "summary": summary,
            "promoter_profiles": promoter_profiles,
            "track_record_analysis": track_record_analysis,
            "conflicts_of_interest": conflicts,
            "red_flags": red_flags,
            "positive_indicators": positive_indicators,
            "overall_assessment": overall_assessment,
            "analysis_date": datetime.utcnow().isoformat(),
            "company_name": company_name
        }
        
        # Log AI decision
        if self.audit_logger:
            try:
                application_id = additional_context.get('application_id', 'unknown') if additional_context else 'unknown'
                await self.audit_logger.log_ai_decision(
                    agent_name='PromoterIntelligenceAgent',
                    application_id=application_id,
                    decision=f"Completed promoter analysis for {company_name}: {overall_assessment['rating']} rating (score: {overall_assessment['score']}/100)",
                    reasoning=f"Analyzed {len(promoter_profiles)} key management personnel. "
                             f"Track record: {track_record_analysis['overall_rating']}. "
                             f"Identified {len(red_flags)} red flags and {len(positive_indicators)} positive indicators. "
                             f"Recommendation: {overall_assessment['recommendation']}",
                    data_sources=['promoter_backgrounds', 'track_record_analysis', 'public_records'],
                    additional_details={
                        'promoters_analyzed': len(promoter_profiles),
                        'track_record_rating': track_record_analysis['overall_rating'],
                        'red_flags_count': len(red_flags),
                        'critical_red_flags': sum(1 for f in red_flags if f.get('severity') == 'critical'),
                        'conflicts_count': len(conflicts),
                        'positive_indicators_count': len(positive_indicators),
                        'overall_rating': overall_assessment['rating'],
                        'overall_score': overall_assessment['score']
                    }
                )
            except Exception as e:
                print(f"Error logging AI decision: {str(e)}")
        
        return result
    
    async def _identify_key_management(
        self,
        company_name: str,
        additional_context: Optional[Dict[str, Any]]
    ) -> List[Dict[str, str]]:
        """
        Identify key management personnel for the company.
        
        In production, this would search company websites, LinkedIn,
        regulatory filings, etc. For this implementation, we simulate
        the identification process.
        
        Args:
            company_name: Company to research
            additional_context: Additional context
        
        Returns:
            List of promoters with name and designation
        """
        context_str = ""
        if additional_context:
            industry = additional_context.get("industry", "")
            if industry:
                context_str = f" in the {industry} industry"
        
        prompt = f"""Identify the key management personnel (promoters/directors) for {company_name}{context_str}.

Generate a realistic list of 3-5 key management personnel that would typically be found for a company of this type. Include:
- CEO/Managing Director
- CFO or Finance Director
- Other key directors or founders

For each person, provide:
- name: Full name
- designation: Job title/position
- tenure: Approximate years with company (e.g., "5 years", "Since 2018")

Return as JSON with a "promoters" array.

IMPORTANT: Generate realistic names and positions typical for this type of company.
"""
        
        try:
            response = await self.openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a research assistant identifying company management. Generate realistic data."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.7
            )
            
            result = json.loads(response.choices[0].message.content)
            promoters = result.get("promoters", [])
            
            # Ensure required fields
            for promoter in promoters:
                if "name" not in promoter:
                    promoter["name"] = "Unknown"
                if "designation" not in promoter:
                    promoter["designation"] = "Director"
                if "tenure" not in promoter:
                    promoter["tenure"] = "Unknown"
            
            return promoters
        
        except Exception as e:
            print(f"Error identifying key management: {str(e)}")
            return []

    async def _research_promoter_backgrounds(
        self,
        promoters: List[Dict[str, str]],
        company_name: str,
        additional_context: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Research detailed backgrounds for each promoter.
        
        Gathers information about:
        - Educational background
        - Professional experience
        - Previous companies and roles
        - Industry expertise
        - Notable achievements
        
        Args:
            promoters: List of promoters to research
            company_name: Current company
            additional_context: Additional context
        
        Returns:
            List of detailed promoter profiles
        """
        profiles = []
        
        for promoter in promoters:
            name = promoter.get("name", "")
            designation = promoter.get("designation", "")
            
            if not name:
                continue
            
            # Research this promoter's background
            profile = await self._research_single_promoter(
                name, designation, company_name, additional_context
            )
            
            # Add original promoter info
            profile["name"] = name
            profile["designation"] = designation
            profile["tenure"] = promoter.get("tenure", "Unknown")
            
            profiles.append(profile)
        
        return profiles
    
    async def _research_single_promoter(
        self,
        name: str,
        designation: str,
        company_name: str,
        additional_context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Research a single promoter's background.
        
        Args:
            name: Promoter's name
            designation: Their position
            company_name: Current company
            additional_context: Additional context
        
        Returns:
            Detailed profile information
        """
        context_str = ""
        if additional_context:
            industry = additional_context.get("industry", "")
            if industry:
                context_str = f" in the {industry} industry"
        
        prompt = f"""Research and generate a realistic professional background for {name}, who is the {designation} at {company_name}{context_str}.

Provide:
- education: Educational qualifications (degrees, institutions)
- experience_years: Total years of professional experience (number)
- previous_roles: List of 2-4 previous significant roles with company names and positions
- industry_expertise: Areas of expertise and industry knowledge
- notable_achievements: Key achievements or accomplishments (2-3 items)
- professional_associations: Memberships, certifications, or affiliations
- other_directorships: Other companies where they serve as director (if any)

Return as JSON. Make the background realistic and appropriate for someone in this position.
"""
        
        try:
            response = await self.openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional background researcher. Generate realistic career profiles."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.7
            )
            
            profile = json.loads(response.choices[0].message.content)
            
            # Ensure required fields
            if "education" not in profile:
                profile["education"] = "Not available"
            if "experience_years" not in profile:
                profile["experience_years"] = 10
            if "previous_roles" not in profile:
                profile["previous_roles"] = []
            if "industry_expertise" not in profile:
                profile["industry_expertise"] = []
            if "notable_achievements" not in profile:
                profile["notable_achievements"] = []
            if "professional_associations" not in profile:
                profile["professional_associations"] = []
            if "other_directorships" not in profile:
                profile["other_directorships"] = []
            
            return profile
        
        except Exception as e:
            print(f"Error researching promoter {name}: {str(e)}")
            return {
                "education": "Not available",
                "experience_years": 0,
                "previous_roles": [],
                "industry_expertise": [],
                "notable_achievements": [],
                "professional_associations": [],
                "other_directorships": []
            }
    
    async def _analyze_track_records(
        self,
        promoter_profiles: List[Dict[str, Any]],
        company_name: str
    ) -> Dict[str, Any]:
        """
        Analyze track records from past business ventures.
        
        Evaluates:
        - Success/failure of previous companies
        - Financial performance of past ventures
        - Leadership effectiveness
        - Pattern of business outcomes
        
        Args:
            promoter_profiles: Detailed promoter profiles
            company_name: Current company
        
        Returns:
            Track record analysis with assessment
        """
        # Compile track record information
        track_records = []
        
        for profile in promoter_profiles:
            name = profile.get("name", "")
            previous_roles = profile.get("previous_roles", [])
            
            if previous_roles:
                track_records.append({
                    "promoter": name,
                    "previous_roles": previous_roles
                })
        
        if not track_records:
            return {
                "overall_rating": "insufficient_data",
                "analysis": "Insufficient information available to assess track records.",
                "successful_ventures": [],
                "failed_ventures": [],
                "patterns": []
            }
        
        # Use AI to analyze track records
        prompt = f"""Analyze the track records of the following promoters/directors of {company_name}:

"""
        
        for record in track_records:
            prompt += f"\n{record['promoter']}:\n"
            for role in record['previous_roles']:
                if isinstance(role, dict):
                    prompt += f"  - {role.get('position', '')} at {role.get('company', '')}\n"
                else:
                    prompt += f"  - {role}\n"
        
        prompt += """
Analyze their track records and provide:
- overall_rating: excellent/good/average/concerning/insufficient_data
- analysis: 2-3 paragraph analysis of their collective track record
- successful_ventures: List of successful past ventures with brief outcomes
- failed_ventures: List of failed ventures or concerning outcomes (if any)
- patterns: Key patterns observed (e.g., "consistent growth track record", "experience in turnarounds", etc.)

Return as JSON. Be balanced and evidence-based in your assessment.
"""
        
        try:
            response = await self.openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a management assessment analyst evaluating business track records."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            
            analysis = json.loads(response.choices[0].message.content)
            
            # Ensure required fields
            if "overall_rating" not in analysis:
                analysis["overall_rating"] = "average"
            if "analysis" not in analysis:
                analysis["analysis"] = "Track record analysis completed."
            if "successful_ventures" not in analysis:
                analysis["successful_ventures"] = []
            if "failed_ventures" not in analysis:
                analysis["failed_ventures"] = []
            if "patterns" not in analysis:
                analysis["patterns"] = []
            
            return analysis
        
        except Exception as e:
            print(f"Error analyzing track records: {str(e)}")
            return {
                "overall_rating": "error",
                "analysis": f"Error analyzing track records: {str(e)}",
                "successful_ventures": [],
                "failed_ventures": [],
                "patterns": []
            }
    
    async def _identify_conflicts_of_interest(
        self,
        promoter_profiles: List[Dict[str, Any]],
        company_name: str
    ) -> List[Dict[str, Any]]:
        """
        Identify potential conflicts of interest.
        
        Looks for:
        - Competing business interests
        - Related party transactions
        - Multiple directorships in competing firms
        - Family relationships in business dealings
        
        Args:
            promoter_profiles: Detailed promoter profiles
            company_name: Current company
        
        Returns:
            List of identified conflicts with severity
        """
        conflicts = []
        
        # Check for multiple directorships that might conflict
        for profile in promoter_profiles:
            name = profile.get("name", "")
            other_directorships = profile.get("other_directorships", [])
            
            if len(other_directorships) > 3:
                conflicts.append({
                    "promoter": name,
                    "type": "multiple_directorships",
                    "description": f"{name} holds {len(other_directorships)} other directorships, which may impact time commitment and focus.",
                    "severity": "low",
                    "details": other_directorships
                })
        
        # Use AI to identify more subtle conflicts
        ai_conflicts = await self._ai_identify_conflicts(promoter_profiles, company_name)
        conflicts.extend(ai_conflicts)
        
        # Sort by severity
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        conflicts.sort(key=lambda x: severity_order.get(x.get("severity", "low"), 4))
        
        return conflicts
    
    async def _ai_identify_conflicts(
        self,
        promoter_profiles: List[Dict[str, Any]],
        company_name: str
    ) -> List[Dict[str, Any]]:
        """
        Use AI to identify potential conflicts of interest.
        
        Args:
            promoter_profiles: Promoter profiles
            company_name: Current company
        
        Returns:
            List of identified conflicts
        """
        # Prepare profile summary
        profile_summary = ""
        for profile in promoter_profiles:
            profile_summary += f"\n{profile.get('name', '')} - {profile.get('designation', '')}:\n"
            profile_summary += f"  Other directorships: {', '.join(profile.get('other_directorships', [])) or 'None'}\n"
            profile_summary += f"  Previous roles: {len(profile.get('previous_roles', []))} roles\n"
        
        prompt = f"""Analyze the following promoter information for {company_name} and identify potential conflicts of interest:

{profile_summary}

Identify conflicts such as:
- Competing business interests
- Potential related party transactions
- Directorships in competing or supplier/customer companies
- Situations that might compromise independent judgment

For each conflict, provide:
- promoter: Name of the promoter
- type: Type of conflict (competing_interest, related_party, time_commitment, etc.)
- description: Clear description of the conflict
- severity: critical/high/medium/low
- details: Additional relevant details

Return as JSON with a "conflicts" array. Only include genuine potential conflicts.
If no significant conflicts are identified, return an empty array.
"""
        
        try:
            response = await self.openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a corporate governance analyst identifying conflicts of interest."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.2
            )
            
            result = json.loads(response.choices[0].message.content)
            return result.get("conflicts", [])
        
        except Exception as e:
            print(f"Error identifying conflicts: {str(e)}")
            return []

    async def _identify_promoter_red_flags(
        self,
        promoter_profiles: List[Dict[str, Any]],
        track_record_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Identify red flags in promoter backgrounds.
        
        Red flags include:
        - Criminal records or fraud
        - Regulatory violations
        - Failed businesses with questionable circumstances
        - Reputation issues
        - Disqualifications
        
        Args:
            promoter_profiles: Promoter profiles
            track_record_analysis: Track record analysis
        
        Returns:
            List of red flags with severity
        """
        red_flags = []
        
        # Check for failed ventures in track record
        failed_ventures = track_record_analysis.get("failed_ventures", [])
        if len(failed_ventures) > 2:
            red_flags.append({
                "type": "multiple_failures",
                "description": f"Multiple failed business ventures identified ({len(failed_ventures)} failures)",
                "severity": "high",
                "details": failed_ventures,
                "promoters_affected": "Multiple"
            })
        
        # Use AI to identify red flags from profiles
        ai_red_flags = await self._ai_identify_promoter_red_flags(
            promoter_profiles, track_record_analysis
        )
        red_flags.extend(ai_red_flags)
        
        # Sort by severity
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        red_flags.sort(key=lambda x: severity_order.get(x.get("severity", "low"), 4))
        
        return red_flags
    
    async def _ai_identify_promoter_red_flags(
        self,
        promoter_profiles: List[Dict[str, Any]],
        track_record_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Use AI to identify promoter red flags.
        
        Args:
            promoter_profiles: Promoter profiles
            track_record_analysis: Track record analysis
        
        Returns:
            List of red flags
        """
        # Prepare summary
        summary = f"Track Record Rating: {track_record_analysis.get('overall_rating', 'unknown')}\n\n"
        
        for profile in promoter_profiles:
            summary += f"{profile.get('name', '')} - {profile.get('designation', '')}:\n"
            summary += f"  Experience: {profile.get('experience_years', 0)} years\n"
            summary += f"  Education: {profile.get('education', 'N/A')}\n"
            summary += f"  Previous roles: {len(profile.get('previous_roles', []))}\n"
        
        if track_record_analysis.get("failed_ventures"):
            summary += f"\nFailed Ventures: {len(track_record_analysis['failed_ventures'])}\n"
        
        prompt = f"""Analyze the following promoter information and identify any red flags or concerns:

{summary}

Identify red flags such as:
- Patterns of business failures
- Lack of relevant experience
- Questionable track records
- Reputation concerns
- Governance issues
- Insufficient qualifications for the role

For each red flag, provide:
- type: Type of red flag (experience_gap, track_record_concern, qualification_issue, etc.)
- description: Clear description of the concern
- severity: critical/high/medium/low
- details: Supporting details
- promoters_affected: Which promoters this affects

Return as JSON with a "red_flags" array. Only include genuine concerns.
If no significant red flags are found, return an empty array.
"""
        
        try:
            response = await self.openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a due diligence analyst identifying management red flags. Be thorough but fair."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.2
            )
            
            result = json.loads(response.choices[0].message.content)
            return result.get("red_flags", [])
        
        except Exception as e:
            print(f"Error identifying promoter red flags: {str(e)}")
            return []
    
    async def _identify_promoter_strengths(
        self,
        promoter_profiles: List[Dict[str, Any]],
        track_record_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Identify positive indicators and strengths in promoter backgrounds.
        
        Strengths include:
        - Strong educational credentials
        - Relevant industry experience
        - Successful track record
        - Industry recognition
        - Deep expertise
        
        Args:
            promoter_profiles: Promoter profiles
            track_record_analysis: Track record analysis
        
        Returns:
            List of positive indicators
        """
        positive_indicators = []
        
        # Check for strong track record
        if track_record_analysis.get("overall_rating") in ["excellent", "good"]:
            positive_indicators.append({
                "type": "strong_track_record",
                "description": f"Management team has a {track_record_analysis['overall_rating']} track record",
                "details": track_record_analysis.get("analysis", ""),
                "promoters_affected": "Team"
            })
        
        # Check for successful ventures
        successful_ventures = track_record_analysis.get("successful_ventures", [])
        if len(successful_ventures) >= 2:
            positive_indicators.append({
                "type": "successful_ventures",
                "description": f"Multiple successful business ventures ({len(successful_ventures)} identified)",
                "details": successful_ventures,
                "promoters_affected": "Multiple"
            })
        
        # Check individual promoter strengths
        for profile in promoter_profiles:
            name = profile.get("name", "")
            experience_years = profile.get("experience_years", 0)
            
            # Strong experience
            if experience_years >= 20:
                positive_indicators.append({
                    "type": "extensive_experience",
                    "description": f"{name} has {experience_years} years of experience",
                    "details": f"Extensive industry experience in {profile.get('designation', 'leadership')} role",
                    "promoters_affected": name
                })
            
            # Notable achievements
            achievements = profile.get("notable_achievements", [])
            if len(achievements) >= 2:
                positive_indicators.append({
                    "type": "notable_achievements",
                    "description": f"{name} has significant achievements",
                    "details": achievements,
                    "promoters_affected": name
                })
        
        # Use AI to identify additional strengths
        ai_strengths = await self._ai_identify_promoter_strengths(
            promoter_profiles, track_record_analysis
        )
        positive_indicators.extend(ai_strengths)
        
        return positive_indicators
    
    async def _ai_identify_promoter_strengths(
        self,
        promoter_profiles: List[Dict[str, Any]],
        track_record_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Use AI to identify promoter strengths.
        
        Args:
            promoter_profiles: Promoter profiles
            track_record_analysis: Track record analysis
        
        Returns:
            List of positive indicators
        """
        summary = ""
        for profile in promoter_profiles:
            summary += f"\n{profile.get('name', '')} - {profile.get('designation', '')}:\n"
            summary += f"  Education: {profile.get('education', 'N/A')}\n"
            summary += f"  Experience: {profile.get('experience_years', 0)} years\n"
            summary += f"  Expertise: {', '.join(profile.get('industry_expertise', [])) or 'N/A'}\n"
            summary += f"  Achievements: {len(profile.get('notable_achievements', []))}\n"
        
        prompt = f"""Analyze the following promoter information and identify strengths and positive indicators:

{summary}

Track Record: {track_record_analysis.get('overall_rating', 'unknown')}

Identify strengths such as:
- Strong educational credentials
- Relevant industry expertise
- Proven leadership experience
- Industry recognition or awards
- Complementary skill sets in the team
- Deep domain knowledge

For each strength, provide:
- type: Type of strength (expertise, credentials, leadership, etc.)
- description: Clear description
- details: Supporting details
- promoters_affected: Which promoters this applies to

Return as JSON with a "strengths" array.
"""
        
        try:
            response = await self.openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an analyst identifying management strengths and capabilities."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            
            result = json.loads(response.choices[0].message.content)
            return result.get("strengths", [])
        
        except Exception as e:
            print(f"Error identifying promoter strengths: {str(e)}")
            return []
    
    async def _generate_overall_assessment(
        self,
        promoter_profiles: List[Dict[str, Any]],
        track_record_analysis: Dict[str, Any],
        conflicts: List[Dict[str, Any]],
        red_flags: List[Dict[str, Any]],
        positive_indicators: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate overall management quality assessment.
        
        Args:
            promoter_profiles: Promoter profiles
            track_record_analysis: Track record analysis
            conflicts: Identified conflicts
            red_flags: Identified red flags
            positive_indicators: Positive indicators
        
        Returns:
            Overall assessment with rating and analysis
        """
        # Calculate assessment score
        score = 50  # Start at neutral
        
        # Adjust based on track record
        track_rating = track_record_analysis.get("overall_rating", "average")
        if track_rating == "excellent":
            score += 20
        elif track_rating == "good":
            score += 10
        elif track_rating == "concerning":
            score -= 20
        
        # Adjust for red flags
        critical_flags = sum(1 for f in red_flags if f.get("severity") == "critical")
        high_flags = sum(1 for f in red_flags if f.get("severity") == "high")
        score -= (critical_flags * 15 + high_flags * 10)
        
        # Adjust for conflicts
        critical_conflicts = sum(1 for c in conflicts if c.get("severity") == "critical")
        high_conflicts = sum(1 for c in conflicts if c.get("severity") == "high")
        score -= (critical_conflicts * 10 + high_conflicts * 5)
        
        # Adjust for positive indicators
        score += min(len(positive_indicators) * 3, 20)
        
        # Ensure score is in valid range
        score = max(0, min(100, score))
        
        # Determine rating
        if score >= 80:
            rating = "excellent"
        elif score >= 65:
            rating = "good"
        elif score >= 50:
            rating = "average"
        elif score >= 35:
            rating = "below_average"
        else:
            rating = "concerning"
        
        # Generate detailed assessment using AI
        assessment_text = await self._generate_assessment_text(
            promoter_profiles,
            track_record_analysis,
            conflicts,
            red_flags,
            positive_indicators,
            rating,
            score
        )
        
        return {
            "rating": rating,
            "score": score,
            "assessment": assessment_text,
            "key_strengths": [p["description"] for p in positive_indicators[:3]],
            "key_concerns": [r["description"] for r in red_flags[:3]],
            "recommendation": self._generate_recommendation(rating, red_flags, conflicts)
        }
    
    async def _generate_assessment_text(
        self,
        promoter_profiles: List[Dict[str, Any]],
        track_record_analysis: Dict[str, Any],
        conflicts: List[Dict[str, Any]],
        red_flags: List[Dict[str, Any]],
        positive_indicators: List[Dict[str, Any]],
        rating: str,
        score: int
    ) -> str:
        """Generate detailed assessment text using AI."""
        prompt = f"""Generate a comprehensive management quality assessment based on the following analysis:

**Promoters:** {len(promoter_profiles)} key management personnel
**Track Record:** {track_record_analysis.get('overall_rating', 'unknown')}
**Red Flags:** {len(red_flags)} identified
**Conflicts of Interest:** {len(conflicts)} identified
**Positive Indicators:** {len(positive_indicators)} identified
**Overall Rating:** {rating} (Score: {score}/100)

Key Concerns:
"""
        
        for flag in red_flags[:3]:
            prompt += f"- {flag.get('description', '')}\n"
        
        prompt += "\nKey Strengths:\n"
        for indicator in positive_indicators[:3]:
            prompt += f"- {indicator.get('description', '')}\n"
        
        prompt += """
Provide a 2-3 paragraph assessment that:
1. Summarizes the overall management quality
2. Highlights the most significant strengths
3. Addresses key concerns or red flags
4. Provides context for the credit decision

Keep the tone professional and balanced.
"""
        
        try:
            response = await self.openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a credit analyst assessing management quality."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=600
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            print(f"Error generating assessment text: {str(e)}")
            return self._generate_fallback_assessment(
                rating, len(red_flags), len(positive_indicators)
            )
    
    def _generate_fallback_assessment(
        self,
        rating: str,
        red_flag_count: int,
        positive_count: int
    ) -> str:
        """Generate a rule-based assessment as fallback."""
        if rating == "excellent":
            return (
                f"The management team demonstrates excellent quality with {positive_count} "
                f"positive indicators identified. The team has strong credentials, relevant "
                f"experience, and a proven track record. "
                f"{'Some minor concerns were noted but do not materially impact the overall assessment.' if red_flag_count > 0 else 'No significant concerns were identified.'}"
            )
        elif rating == "good":
            return (
                f"The management team shows good quality with solid credentials and experience. "
                f"{positive_count} positive indicators were identified. "
                f"{'Some concerns require attention but are manageable.' if red_flag_count > 0 else 'The team appears well-qualified for their roles.'}"
            )
        elif rating == "average":
            return (
                f"The management team demonstrates average quality. While there are {positive_count} "
                f"positive indicators, {red_flag_count} concerns were also identified that require "
                f"careful consideration in the credit decision."
            )
        else:
            return (
                f"The management team assessment raises concerns. {red_flag_count} red flags were "
                f"identified that may impact credit risk. These concerns should be carefully "
                f"evaluated and potentially addressed through loan conditions or covenants."
            )
    
    def _generate_recommendation(
        self,
        rating: str,
        red_flags: List[Dict[str, Any]],
        conflicts: List[Dict[str, Any]]
    ) -> str:
        """Generate recommendation based on assessment."""
        critical_issues = sum(
            1 for item in red_flags + conflicts
            if item.get("severity") == "critical"
        )
        
        if critical_issues > 0:
            return "Critical management concerns identified. Recommend detailed due diligence before proceeding."
        elif rating in ["excellent", "good"]:
            return "Management quality supports credit approval."
        elif rating == "average":
            return "Management quality is acceptable but should be monitored. Consider additional covenants."
        else:
            return "Management concerns may warrant additional scrutiny or loan conditions."
    
    async def _generate_promoter_summary(
        self,
        company_name: str,
        promoter_profiles: List[Dict[str, Any]],
        red_flags: List[Dict[str, Any]],
        positive_indicators: List[Dict[str, Any]],
        overall_assessment: Dict[str, Any]
    ) -> str:
        """
        Generate comprehensive promoter analysis summary.
        
        Args:
            company_name: Company name
            promoter_profiles: Promoter profiles
            red_flags: Red flags
            positive_indicators: Positive indicators
            overall_assessment: Overall assessment
        
        Returns:
            Summary text
        """
        prompt = f"""Generate a comprehensive promoter intelligence summary for {company_name}.

**Key Management:** {len(promoter_profiles)} personnel analyzed
**Overall Rating:** {overall_assessment.get('rating', 'unknown')} ({overall_assessment.get('score', 0)}/100)
**Red Flags:** {len(red_flags)}
**Positive Indicators:** {len(positive_indicators)}

Key Strengths:
"""
        
        for strength in overall_assessment.get("key_strengths", [])[:3]:
            prompt += f"- {strength}\n"
        
        if overall_assessment.get("key_concerns"):
            prompt += "\nKey Concerns:\n"
            for concern in overall_assessment.get("key_concerns", [])[:3]:
                prompt += f"- {concern}\n"
        
        prompt += f"""
Recommendation: {overall_assessment.get('recommendation', '')}

Provide a 2-3 paragraph executive summary that:
1. Introduces the management team
2. Highlights key qualifications and experience
3. Addresses any concerns or red flags
4. Provides overall assessment for credit decision

Keep it professional and concise.
"""
        
        try:
            response = await self.openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a credit analyst summarizing promoter intelligence."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=600
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            print(f"Error generating promoter summary: {str(e)}")
            return self._generate_fallback_summary(
                company_name,
                len(promoter_profiles),
                overall_assessment
            )
    
    def _generate_fallback_summary(
        self,
        company_name: str,
        promoter_count: int,
        overall_assessment: Dict[str, Any]
    ) -> str:
        """Generate a rule-based summary as fallback."""
        rating = overall_assessment.get("rating", "unknown")
        score = overall_assessment.get("score", 0)
        
        summary = (
            f"Promoter intelligence analysis for {company_name} evaluated {promoter_count} "
            f"key management personnel. The overall management quality assessment is "
            f"{rating.replace('_', ' ')} with a score of {score}/100. "
        )
        
        key_strengths = overall_assessment.get("key_strengths", [])
        if key_strengths:
            summary += f"Key strengths include: {', '.join(key_strengths[:2])}. "
        
        key_concerns = overall_assessment.get("key_concerns", [])
        if key_concerns:
            summary += f"Concerns identified: {', '.join(key_concerns[:2])}. "
        
        summary += overall_assessment.get("recommendation", "")
        
        return summary
    
    def _empty_analysis_result(self, reason: str) -> Dict[str, Any]:
        """Return an empty analysis result with a reason."""
        return {
            "summary": f"Promoter analysis could not be completed: {reason}",
            "promoter_profiles": [],
            "track_record_analysis": {
                "overall_rating": "insufficient_data",
                "analysis": reason,
                "successful_ventures": [],
                "failed_ventures": [],
                "patterns": []
            },
            "conflicts_of_interest": [],
            "red_flags": [],
            "positive_indicators": [],
            "overall_assessment": {
                "rating": "insufficient_data",
                "score": 0,
                "assessment": reason,
                "key_strengths": [],
                "key_concerns": [],
                "recommendation": "Unable to assess management quality due to insufficient data."
            },
            "analysis_date": datetime.utcnow().isoformat(),
            "company_name": ""
        }
