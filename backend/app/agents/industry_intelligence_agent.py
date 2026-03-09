"""
Industry Intelligence Agent

This agent evaluates sector trends, competitive landscape, and industry-specific
risks to provide context for company performance and credit assessment.

Requirements: 3.4
"""

import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from openai import AsyncOpenAI

from app.core.config import settings
from app.core.audit_logger import AuditLogger


class IndustryIntelligenceAgent:
    """
    AI agent for analyzing industry trends and competitive positioning.
    
    Performs industry intelligence gathering to:
    - Evaluate sector trends and growth outlook
    - Analyze competitive landscape
    - Assess industry-specific risks
    - Provide context for company performance
    - Identify market opportunities and threats
    
    Requirements: 3.4
    """
    
    # Industry risk indicators
    INDUSTRY_RISK_KEYWORDS = [
        "declining", "downturn", "recession", "contraction", "shrinking",
        "disruption", "obsolete", "regulatory pressure", "oversupply",
        "price war", "margin pressure", "consolidation", "saturation",
        "cyclical downturn", "structural decline", "competition intensifying",
        "market share loss", "commoditization", "technological disruption"
    ]
    
    # Positive industry indicators
    INDUSTRY_POSITIVE_KEYWORDS = [
        "growth", "expanding", "boom", "emerging", "innovation",
        "demand surge", "favorable regulation", "market opportunity",
        "consolidation opportunity", "pricing power", "margin expansion",
        "technological advancement", "market leadership", "barriers to entry",
        "sustainable growth", "secular trend", "tailwinds"
    ]
    
    def __init__(self, audit_logger: Optional[AuditLogger] = None):
        """
        Initialize the Industry Intelligence Agent.
        
        Args:
            audit_logger: Optional audit logger for AI decision logging
        """
        self.openai = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.audit_logger = audit_logger
    
    async def analyze(
        self,
        company_name: str,
        industry: Optional[str] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Conduct comprehensive industry intelligence analysis.
        
        Args:
            company_name: Name of the company
            industry: Industry/sector (if known)
            additional_context: Optional additional context (location, sub-sector, etc.)
        
        Returns:
            Dictionary containing:
                - summary: Overall industry analysis summary
                - sector_trends: Analysis of sector trends and outlook
                - competitive_landscape: Competitive positioning analysis
                - industry_risks: Identified industry-specific risks
                - market_opportunities: Market opportunities identified
                - growth_outlook: Industry growth projections
                - overall_assessment: Overall industry attractiveness assessment
                - analysis_date: Timestamp of analysis
        
        Requirements: 3.4
        """
        if not company_name:
            return self._empty_analysis_result("No company name provided")
        
        # If industry not provided, attempt to identify it
        if not industry:
            industry = await self._identify_industry(company_name, additional_context)
        
        if not industry:
            return self._empty_analysis_result(
                f"Could not identify industry for {company_name}"
            )
        
        # Step 1: Analyze sector trends
        sector_trends = await self._analyze_sector_trends(
            industry, company_name, additional_context
        )
        
        # Step 2: Analyze competitive landscape
        competitive_landscape = await self._analyze_competitive_landscape(
            industry, company_name, additional_context
        )
        
        # Step 3: Identify industry-specific risks
        industry_risks = await self._identify_industry_risks(
            industry, sector_trends, competitive_landscape
        )
        
        # Step 4: Identify market opportunities
        market_opportunities = await self._identify_market_opportunities(
            industry, sector_trends, competitive_landscape
        )
        
        # Step 5: Assess growth outlook
        growth_outlook = await self._assess_growth_outlook(
            industry, sector_trends, additional_context
        )
        
        # Step 6: Generate overall assessment
        overall_assessment = await self._generate_overall_assessment(
            industry,
            sector_trends,
            competitive_landscape,
            industry_risks,
            market_opportunities,
            growth_outlook
        )
        
        # Step 7: Generate summary
        summary = await self._generate_industry_summary(
            company_name,
            industry,
            sector_trends,
            competitive_landscape,
            industry_risks,
            overall_assessment
        )
        
        result = {
            "summary": summary,
            "industry": industry,
            "sector_trends": sector_trends,
            "competitive_landscape": competitive_landscape,
            "industry_risks": industry_risks,
            "market_opportunities": market_opportunities,
            "growth_outlook": growth_outlook,
            "overall_assessment": overall_assessment,
            "analysis_date": datetime.utcnow().isoformat(),
            "company_name": company_name
        }
        
        # Log AI decision
        if self.audit_logger:
            try:
                application_id = additional_context.get('application_id', 'unknown') if additional_context else 'unknown'
                await self.audit_logger.log_ai_decision(
                    agent_name='IndustryIntelligenceAgent',
                    application_id=application_id,
                    decision=f"Completed industry analysis for {industry}: {overall_assessment.get('rating', 'unknown')} outlook",
                    reasoning=f"Analyzed sector trends, competitive landscape, and growth outlook for {industry}. "
                             f"Identified {len(industry_risks)} industry risks and {len(market_opportunities)} opportunities. "
                             f"Summary: {summary[:200]}...",
                    data_sources=['industry_reports', 'market_research', 'competitive_analysis'],
                    additional_details={
                        'industry': industry,
                        'sector_trends_rating': sector_trends.get('trend_direction', 'unknown'),
                        'industry_risks_count': len(industry_risks),
                        'market_opportunities_count': len(market_opportunities),
                        'growth_outlook': growth_outlook.get('rating', 'unknown'),
                        'overall_assessment': overall_assessment.get('rating', 'unknown')
                    }
                )
            except Exception as e:
                print(f"Error logging AI decision: {str(e)}")
        
        return result
    
    async def _identify_industry(
        self,
        company_name: str,
        additional_context: Optional[Dict[str, Any]]
    ) -> str:
        """
        Identify the industry/sector for the company.
        
        Args:
            company_name: Company to identify industry for
            additional_context: Additional context
        
        Returns:
            Industry name/classification
        """
        context_str = ""
        if additional_context:
            location = additional_context.get("location", "")
            business_type = additional_context.get("business_type", "")
            if location:
                context_str += f" located in {location}"
            if business_type:
                context_str += f" in the {business_type} business"
        
        prompt = f"""Identify the primary industry/sector for {company_name}{context_str}.

Provide:
- industry: Primary industry classification (e.g., "Manufacturing - Automotive", "Technology - Software", "Retail - E-commerce")
- sub_sector: More specific sub-sector if applicable
- industry_code: Standard industry code (SIC or NAICS) if identifiable

Return as JSON. Be specific but realistic based on the company name and context.
"""
        
        try:
            response = await self.openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an industry classification expert. Identify industries accurately."
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
            industry = result.get("industry", "Unknown Industry")
            
            return industry
        
        except Exception as e:
            print(f"Error identifying industry: {str(e)}")
            return "Unknown Industry"
    
    async def _analyze_sector_trends(
        self,
        industry: str,
        company_name: str,
        additional_context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze sector trends and outlook.
        
        Evaluates:
        - Current market conditions
        - Growth trends
        - Technological changes
        - Regulatory environment
        - Economic factors
        
        Args:
            industry: Industry to analyze
            company_name: Company name for context
            additional_context: Additional context
        
        Returns:
            Sector trends analysis
        """
        context_str = ""
        if additional_context:
            location = additional_context.get("location", "")
            if location:
                context_str = f" in {location}"
        
        prompt = f"""Analyze the current trends and outlook for the {industry} industry{context_str}.

Provide a comprehensive analysis including:
- current_state: Current market conditions (growing/stable/declining/volatile)
- key_trends: List of 3-5 key trends shaping the industry
- growth_drivers: Factors driving growth or expansion
- headwinds: Challenges or negative factors
- technological_changes: Relevant technological disruptions or innovations
- regulatory_environment: Regulatory factors affecting the industry
- economic_sensitivity: How sensitive the industry is to economic cycles (high/medium/low)
- outlook: Short-term (1-2 year) outlook (positive/neutral/negative)

Return as JSON. Base analysis on realistic industry dynamics.
"""
        
        try:
            response = await self.openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an industry analyst providing sector trend analysis."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.4
            )
            
            trends = json.loads(response.choices[0].message.content)
            
            # Ensure required fields
            if "current_state" not in trends:
                trends["current_state"] = "stable"
            if "key_trends" not in trends:
                trends["key_trends"] = []
            if "growth_drivers" not in trends:
                trends["growth_drivers"] = []
            if "headwinds" not in trends:
                trends["headwinds"] = []
            if "technological_changes" not in trends:
                trends["technological_changes"] = []
            if "regulatory_environment" not in trends:
                trends["regulatory_environment"] = "Stable regulatory environment"
            if "economic_sensitivity" not in trends:
                trends["economic_sensitivity"] = "medium"
            if "outlook" not in trends:
                trends["outlook"] = "neutral"
            
            return trends
        
        except Exception as e:
            print(f"Error analyzing sector trends: {str(e)}")
            return {
                "current_state": "unknown",
                "key_trends": [],
                "growth_drivers": [],
                "headwinds": [],
                "technological_changes": [],
                "regulatory_environment": "Unknown",
                "economic_sensitivity": "medium",
                "outlook": "neutral"
            }

    async def _analyze_competitive_landscape(
        self,
        industry: str,
        company_name: str,
        additional_context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze competitive landscape and positioning.
        
        Evaluates:
        - Market structure and concentration
        - Key competitors
        - Competitive intensity
        - Barriers to entry
        - Company positioning
        
        Args:
            industry: Industry to analyze
            company_name: Company name
            additional_context: Additional context
        
        Returns:
            Competitive landscape analysis
        """
        prompt = f"""Analyze the competitive landscape for the {industry} industry, with focus on {company_name}.

Provide:
- market_structure: Market structure (fragmented/moderately concentrated/highly concentrated/monopolistic)
- competitive_intensity: Level of competition (low/moderate/high/intense)
- key_competitors: List of 3-5 major competitors or competitor types
- barriers_to_entry: Assessment of barriers to entry (low/moderate/high)
- barriers_description: Description of key barriers (capital requirements, regulations, technology, etc.)
- competitive_factors: Key factors for competitive success (3-5 factors)
- market_share_dynamics: How market share is distributed and changing
- pricing_power: Industry pricing power (weak/moderate/strong)
- differentiation_potential: Ability to differentiate (low/moderate/high)

Return as JSON. Provide realistic competitive analysis.
"""
        
        try:
            response = await self.openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a competitive strategy analyst."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.4
            )
            
            landscape = json.loads(response.choices[0].message.content)
            
            # Ensure required fields
            if "market_structure" not in landscape:
                landscape["market_structure"] = "moderately concentrated"
            if "competitive_intensity" not in landscape:
                landscape["competitive_intensity"] = "moderate"
            if "key_competitors" not in landscape:
                landscape["key_competitors"] = []
            if "barriers_to_entry" not in landscape:
                landscape["barriers_to_entry"] = "moderate"
            if "barriers_description" not in landscape:
                landscape["barriers_description"] = ""
            if "competitive_factors" not in landscape:
                landscape["competitive_factors"] = []
            if "market_share_dynamics" not in landscape:
                landscape["market_share_dynamics"] = "Stable market share distribution"
            if "pricing_power" not in landscape:
                landscape["pricing_power"] = "moderate"
            if "differentiation_potential" not in landscape:
                landscape["differentiation_potential"] = "moderate"
            
            return landscape
        
        except Exception as e:
            print(f"Error analyzing competitive landscape: {str(e)}")
            return {
                "market_structure": "unknown",
                "competitive_intensity": "moderate",
                "key_competitors": [],
                "barriers_to_entry": "moderate",
                "barriers_description": "",
                "competitive_factors": [],
                "market_share_dynamics": "Unknown",
                "pricing_power": "moderate",
                "differentiation_potential": "moderate"
            }
    
    async def _identify_industry_risks(
        self,
        industry: str,
        sector_trends: Dict[str, Any],
        competitive_landscape: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Identify industry-specific risks.
        
        Risks include:
        - Cyclical risks
        - Regulatory risks
        - Technological disruption
        - Competitive pressures
        - Supply chain risks
        
        Args:
            industry: Industry being analyzed
            sector_trends: Sector trends analysis
            competitive_landscape: Competitive landscape analysis
        
        Returns:
            List of industry risks with severity
        """
        risks = []
        
        # Check for declining industry
        if sector_trends.get("current_state") == "declining":
            risks.append({
                "type": "market_decline",
                "description": f"The {industry} industry is currently in decline",
                "severity": "high",
                "details": "Declining market conditions may impact revenue and profitability",
                "mitigation": "Assess company's ability to gain market share or diversify"
            })
        
        # Check for high economic sensitivity
        if sector_trends.get("economic_sensitivity") == "high":
            risks.append({
                "type": "cyclical_risk",
                "description": "Industry is highly sensitive to economic cycles",
                "severity": "medium",
                "details": "Economic downturns could significantly impact performance",
                "mitigation": "Evaluate financial resilience and counter-cyclical strategies"
            })
        
        # Check for intense competition
        if competitive_landscape.get("competitive_intensity") in ["high", "intense"]:
            risks.append({
                "type": "competitive_pressure",
                "description": "Intense competitive pressure in the industry",
                "severity": "medium",
                "details": "High competition may pressure margins and market share",
                "mitigation": "Assess competitive advantages and differentiation"
            })
        
        # Check for weak pricing power
        if competitive_landscape.get("pricing_power") == "weak":
            risks.append({
                "type": "pricing_pressure",
                "description": "Limited pricing power in the industry",
                "severity": "medium",
                "details": "Weak pricing power may limit profitability",
                "mitigation": "Evaluate cost structure and operational efficiency"
            })
        
        # Use AI to identify additional risks
        ai_risks = await self._ai_identify_industry_risks(
            industry, sector_trends, competitive_landscape
        )
        risks.extend(ai_risks)
        
        # Sort by severity
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        risks.sort(key=lambda x: severity_order.get(x.get("severity", "low"), 4))
        
        return risks
    
    async def _ai_identify_industry_risks(
        self,
        industry: str,
        sector_trends: Dict[str, Any],
        competitive_landscape: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Use AI to identify additional industry risks.
        
        Args:
            industry: Industry being analyzed
            sector_trends: Sector trends
            competitive_landscape: Competitive landscape
        
        Returns:
            List of identified risks
        """
        prompt = f"""Identify key industry-specific risks for the {industry} industry based on the following analysis:

**Current State:** {sector_trends.get('current_state', 'unknown')}
**Outlook:** {sector_trends.get('outlook', 'neutral')}
**Economic Sensitivity:** {sector_trends.get('economic_sensitivity', 'medium')}
**Competitive Intensity:** {competitive_landscape.get('competitive_intensity', 'moderate')}

**Headwinds:**
"""
        
        for headwind in sector_trends.get("headwinds", [])[:5]:
            prompt += f"- {headwind}\n"
        
        prompt += """
Identify industry-specific risks such as:
- Regulatory risks
- Technological disruption risks
- Supply chain vulnerabilities
- Market saturation risks
- Structural industry changes
- Environmental or sustainability risks

For each risk, provide:
- type: Type of risk (regulatory, technological, supply_chain, etc.)
- description: Clear description of the risk
- severity: critical/high/medium/low
- details: More detailed explanation
- mitigation: Suggested mitigation or assessment approach

Return as JSON with a "risks" array. Focus on material risks relevant to credit assessment.
"""
        
        try:
            response = await self.openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a risk analyst identifying industry-specific risks."
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
            return result.get("risks", [])
        
        except Exception as e:
            print(f"Error identifying industry risks: {str(e)}")
            return []
    
    async def _identify_market_opportunities(
        self,
        industry: str,
        sector_trends: Dict[str, Any],
        competitive_landscape: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Identify market opportunities in the industry.
        
        Opportunities include:
        - Growth markets
        - Emerging trends
        - Consolidation opportunities
        - Innovation potential
        - Market gaps
        
        Args:
            industry: Industry being analyzed
            sector_trends: Sector trends
            competitive_landscape: Competitive landscape
        
        Returns:
            List of market opportunities
        """
        opportunities = []
        
        # Check for positive outlook
        if sector_trends.get("outlook") == "positive":
            opportunities.append({
                "type": "market_growth",
                "description": f"Positive outlook for the {industry} industry",
                "details": "Favorable market conditions support growth opportunities",
                "potential_impact": "high"
            })
        
        # Check for growth drivers
        growth_drivers = sector_trends.get("growth_drivers", [])
        if len(growth_drivers) >= 2:
            opportunities.append({
                "type": "growth_drivers",
                "description": "Multiple growth drivers identified",
                "details": f"Key drivers: {', '.join(growth_drivers[:3])}",
                "potential_impact": "medium"
            })
        
        # Check for high barriers to entry
        if competitive_landscape.get("barriers_to_entry") == "high":
            opportunities.append({
                "type": "protected_market",
                "description": "High barriers to entry protect incumbents",
                "details": competitive_landscape.get("barriers_description", ""),
                "potential_impact": "medium"
            })
        
        # Use AI to identify additional opportunities
        ai_opportunities = await self._ai_identify_market_opportunities(
            industry, sector_trends, competitive_landscape
        )
        opportunities.extend(ai_opportunities)
        
        return opportunities
    
    async def _ai_identify_market_opportunities(
        self,
        industry: str,
        sector_trends: Dict[str, Any],
        competitive_landscape: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Use AI to identify market opportunities.
        
        Args:
            industry: Industry being analyzed
            sector_trends: Sector trends
            competitive_landscape: Competitive landscape
        
        Returns:
            List of opportunities
        """
        prompt = f"""Identify market opportunities in the {industry} industry based on the following:

**Growth Drivers:**
"""
        
        for driver in sector_trends.get("growth_drivers", [])[:5]:
            prompt += f"- {driver}\n"
        
        prompt += f"""
**Key Trends:**
"""
        
        for trend in sector_trends.get("key_trends", [])[:5]:
            prompt += f"- {trend}\n"
        
        prompt += f"""
**Market Structure:** {competitive_landscape.get('market_structure', 'unknown')}
**Differentiation Potential:** {competitive_landscape.get('differentiation_potential', 'moderate')}

Identify opportunities such as:
- Emerging market segments
- Innovation opportunities
- Consolidation potential
- Geographic expansion
- Product/service diversification
- Technology adoption benefits

For each opportunity, provide:
- type: Type of opportunity (market_expansion, innovation, consolidation, etc.)
- description: Clear description
- details: More detailed explanation
- potential_impact: high/medium/low

Return as JSON with an "opportunities" array.
"""
        
        try:
            response = await self.openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a market analyst identifying business opportunities."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.4
            )
            
            result = json.loads(response.choices[0].message.content)
            return result.get("opportunities", [])
        
        except Exception as e:
            print(f"Error identifying market opportunities: {str(e)}")
            return []
    
    async def _assess_growth_outlook(
        self,
        industry: str,
        sector_trends: Dict[str, Any],
        additional_context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Assess industry growth outlook.
        
        Args:
            industry: Industry being analyzed
            sector_trends: Sector trends
            additional_context: Additional context
        
        Returns:
            Growth outlook assessment
        """
        prompt = f"""Assess the growth outlook for the {industry} industry.

Current State: {sector_trends.get('current_state', 'unknown')}
Outlook: {sector_trends.get('outlook', 'neutral')}

Provide:
- short_term_growth: Expected growth rate for next 1-2 years (e.g., "3-5%", "declining", "flat")
- medium_term_growth: Expected growth rate for 3-5 years
- growth_quality: Quality of growth (sustainable/cyclical/speculative/uncertain)
- key_assumptions: Key assumptions underlying the growth outlook (list)
- confidence_level: Confidence in the outlook (high/medium/low)
- growth_narrative: 2-3 sentence narrative explaining the growth outlook

Return as JSON.
"""
        
        try:
            response = await self.openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an industry analyst assessing growth outlook."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            
            outlook = json.loads(response.choices[0].message.content)
            
            # Ensure required fields
            if "short_term_growth" not in outlook:
                outlook["short_term_growth"] = "2-4%"
            if "medium_term_growth" not in outlook:
                outlook["medium_term_growth"] = "3-5%"
            if "growth_quality" not in outlook:
                outlook["growth_quality"] = "sustainable"
            if "key_assumptions" not in outlook:
                outlook["key_assumptions"] = []
            if "confidence_level" not in outlook:
                outlook["confidence_level"] = "medium"
            if "growth_narrative" not in outlook:
                outlook["growth_narrative"] = f"The {industry} industry is expected to show moderate growth."
            
            return outlook
        
        except Exception as e:
            print(f"Error assessing growth outlook: {str(e)}")
            return {
                "short_term_growth": "unknown",
                "medium_term_growth": "unknown",
                "growth_quality": "uncertain",
                "key_assumptions": [],
                "confidence_level": "low",
                "growth_narrative": "Unable to assess growth outlook."
            }

    async def _generate_overall_assessment(
        self,
        industry: str,
        sector_trends: Dict[str, Any],
        competitive_landscape: Dict[str, Any],
        industry_risks: List[Dict[str, Any]],
        market_opportunities: List[Dict[str, Any]],
        growth_outlook: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate overall industry attractiveness assessment.
        
        Args:
            industry: Industry name
            sector_trends: Sector trends
            competitive_landscape: Competitive landscape
            industry_risks: Industry risks
            market_opportunities: Market opportunities
            growth_outlook: Growth outlook
        
        Returns:
            Overall assessment with rating and analysis
        """
        # Calculate assessment score
        score = 50  # Start at neutral
        
        # Adjust based on outlook
        outlook = sector_trends.get("outlook", "neutral")
        if outlook == "positive":
            score += 15
        elif outlook == "negative":
            score -= 15
        
        # Adjust based on current state
        current_state = sector_trends.get("current_state", "stable")
        if current_state == "growing":
            score += 10
        elif current_state == "declining":
            score -= 15
        elif current_state == "volatile":
            score -= 5
        
        # Adjust for competitive intensity
        comp_intensity = competitive_landscape.get("competitive_intensity", "moderate")
        if comp_intensity == "low":
            score += 10
        elif comp_intensity in ["high", "intense"]:
            score -= 10
        
        # Adjust for barriers to entry
        barriers = competitive_landscape.get("barriers_to_entry", "moderate")
        if barriers == "high":
            score += 10
        elif barriers == "low":
            score -= 5
        
        # Adjust for risks
        critical_risks = sum(1 for r in industry_risks if r.get("severity") == "critical")
        high_risks = sum(1 for r in industry_risks if r.get("severity") == "high")
        score -= (critical_risks * 15 + high_risks * 8)
        
        # Adjust for opportunities
        high_impact_opps = sum(1 for o in market_opportunities if o.get("potential_impact") == "high")
        score += min(high_impact_opps * 5, 15)
        
        # Adjust for growth quality
        growth_quality = growth_outlook.get("growth_quality", "sustainable")
        if growth_quality == "sustainable":
            score += 10
        elif growth_quality in ["speculative", "uncertain"]:
            score -= 5
        
        # Ensure score is in valid range
        score = max(0, min(100, score))
        
        # Determine rating
        if score >= 75:
            rating = "highly_attractive"
        elif score >= 60:
            rating = "attractive"
        elif score >= 45:
            rating = "neutral"
        elif score >= 30:
            rating = "challenging"
        else:
            rating = "unfavorable"
        
        # Generate detailed assessment using AI
        assessment_text = await self._generate_assessment_text(
            industry,
            sector_trends,
            competitive_landscape,
            industry_risks,
            market_opportunities,
            growth_outlook,
            rating,
            score
        )
        
        return {
            "rating": rating,
            "score": score,
            "assessment": assessment_text,
            "key_strengths": self._extract_key_strengths(
                sector_trends, competitive_landscape, market_opportunities
            ),
            "key_challenges": [r["description"] for r in industry_risks[:3]],
            "credit_implications": self._generate_credit_implications(rating, industry_risks)
        }
    
    def _extract_key_strengths(
        self,
        sector_trends: Dict[str, Any],
        competitive_landscape: Dict[str, Any],
        market_opportunities: List[Dict[str, Any]]
    ) -> List[str]:
        """Extract key industry strengths."""
        strengths = []
        
        if sector_trends.get("outlook") == "positive":
            strengths.append("Positive industry outlook")
        
        if sector_trends.get("current_state") == "growing":
            strengths.append("Growing market conditions")
        
        if competitive_landscape.get("barriers_to_entry") == "high":
            strengths.append("High barriers to entry protect incumbents")
        
        if competitive_landscape.get("pricing_power") == "strong":
            strengths.append("Strong industry pricing power")
        
        # Add top opportunities
        for opp in market_opportunities[:2]:
            if opp.get("potential_impact") == "high":
                strengths.append(opp.get("description", ""))
        
        return strengths[:5]  # Limit to top 5
    
    def _generate_credit_implications(
        self,
        rating: str,
        industry_risks: List[Dict[str, Any]]
    ) -> str:
        """Generate credit implications based on assessment."""
        if rating == "highly_attractive":
            return "Favorable industry conditions support credit quality. Industry dynamics are positive for lending."
        elif rating == "attractive":
            return "Industry conditions are generally supportive of credit quality with manageable risks."
        elif rating == "neutral":
            return "Industry presents balanced risk-reward profile. Company-specific factors will be key differentiators."
        elif rating == "challenging":
            critical_count = sum(1 for r in industry_risks if r.get("severity") == "critical")
            if critical_count > 0:
                return "Challenging industry conditions present elevated credit risk. Recommend enhanced monitoring and conservative underwriting."
            return "Industry headwinds require careful assessment of company resilience and competitive positioning."
        else:
            return "Unfavorable industry conditions present significant credit concerns. Recommend heightened scrutiny and risk mitigation measures."
    
    async def _generate_assessment_text(
        self,
        industry: str,
        sector_trends: Dict[str, Any],
        competitive_landscape: Dict[str, Any],
        industry_risks: List[Dict[str, Any]],
        market_opportunities: List[Dict[str, Any]],
        growth_outlook: Dict[str, Any],
        rating: str,
        score: int
    ) -> str:
        """Generate detailed assessment text using AI."""
        prompt = f"""Generate a comprehensive industry assessment for the {industry} industry.

**Overall Rating:** {rating.replace('_', ' ').title()} (Score: {score}/100)
**Current State:** {sector_trends.get('current_state', 'unknown')}
**Outlook:** {sector_trends.get('outlook', 'neutral')}
**Growth Outlook:** {growth_outlook.get('short_term_growth', 'unknown')} (short-term)
**Competitive Intensity:** {competitive_landscape.get('competitive_intensity', 'moderate')}
**Industry Risks:** {len(industry_risks)} identified
**Market Opportunities:** {len(market_opportunities)} identified

Key Challenges:
"""
        
        for risk in industry_risks[:3]:
            prompt += f"- {risk.get('description', '')}\n"
        
        prompt += "\nKey Opportunities:\n"
        for opp in market_opportunities[:3]:
            prompt += f"- {opp.get('description', '')}\n"
        
        prompt += """
Provide a 2-3 paragraph assessment that:
1. Summarizes the overall industry attractiveness
2. Highlights key trends and competitive dynamics
3. Addresses major risks and opportunities
4. Provides context for credit assessment

Keep the tone professional and analytical.
"""
        
        try:
            response = await self.openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an industry analyst providing comprehensive assessments."
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
            return self._generate_fallback_assessment(rating, industry, score)
    
    def _generate_fallback_assessment(
        self,
        rating: str,
        industry: str,
        score: int
    ) -> str:
        """Generate a rule-based assessment as fallback."""
        rating_text = rating.replace("_", " ").title()
        
        if rating == "highly_attractive":
            return (
                f"The {industry} industry demonstrates highly attractive characteristics "
                f"with a score of {score}/100. The sector shows strong growth prospects, "
                f"favorable competitive dynamics, and limited structural risks. Industry "
                f"conditions are supportive of credit quality and business performance."
            )
        elif rating == "attractive":
            return (
                f"The {industry} industry presents attractive characteristics with a score "
                f"of {score}/100. While some challenges exist, the overall industry dynamics "
                f"are favorable with good growth prospects and manageable competitive pressures."
            )
        elif rating == "neutral":
            return (
                f"The {industry} industry presents a balanced risk-reward profile with a "
                f"score of {score}/100. The sector faces both opportunities and challenges, "
                f"making company-specific factors critical for credit assessment."
            )
        elif rating == "challenging":
            return (
                f"The {industry} industry faces challenging conditions with a score of "
                f"{score}/100. Significant headwinds and competitive pressures require "
                f"careful evaluation of company resilience and positioning."
            )
        else:
            return (
                f"The {industry} industry presents unfavorable conditions with a score of "
                f"{score}/100. Structural challenges and elevated risks warrant heightened "
                f"scrutiny in credit assessment."
            )
    
    async def _generate_industry_summary(
        self,
        company_name: str,
        industry: str,
        sector_trends: Dict[str, Any],
        competitive_landscape: Dict[str, Any],
        industry_risks: List[Dict[str, Any]],
        overall_assessment: Dict[str, Any]
    ) -> str:
        """
        Generate comprehensive industry analysis summary.
        
        Args:
            company_name: Company name
            industry: Industry name
            sector_trends: Sector trends
            competitive_landscape: Competitive landscape
            industry_risks: Industry risks
            overall_assessment: Overall assessment
        
        Returns:
            Summary text
        """
        prompt = f"""Generate a comprehensive industry intelligence summary for {company_name} in the {industry} industry.

**Industry Rating:** {overall_assessment.get('rating', 'unknown').replace('_', ' ').title()} ({overall_assessment.get('score', 0)}/100)
**Current State:** {sector_trends.get('current_state', 'unknown')}
**Outlook:** {sector_trends.get('outlook', 'neutral')}
**Competitive Intensity:** {competitive_landscape.get('competitive_intensity', 'moderate')}

Key Strengths:
"""
        
        for strength in overall_assessment.get("key_strengths", [])[:3]:
            prompt += f"- {strength}\n"
        
        prompt += "\nKey Challenges:\n"
        for challenge in overall_assessment.get("key_challenges", [])[:3]:
            prompt += f"- {challenge}\n"
        
        prompt += f"""
Credit Implications: {overall_assessment.get('credit_implications', '')}

Provide a 2-3 paragraph executive summary that:
1. Introduces the industry context for {company_name}
2. Highlights key industry dynamics and trends
3. Addresses competitive positioning considerations
4. Provides overall industry assessment for credit decision

Keep it professional and concise.
"""
        
        try:
            response = await self.openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a credit analyst summarizing industry intelligence."
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
            print(f"Error generating industry summary: {str(e)}")
            return self._generate_fallback_summary(
                company_name,
                industry,
                overall_assessment
            )
    
    def _generate_fallback_summary(
        self,
        company_name: str,
        industry: str,
        overall_assessment: Dict[str, Any]
    ) -> str:
        """Generate a rule-based summary as fallback."""
        rating = overall_assessment.get("rating", "unknown").replace("_", " ").title()
        score = overall_assessment.get("score", 0)
        
        summary = (
            f"Industry intelligence analysis for {company_name} in the {industry} "
            f"industry reveals a {rating} assessment with a score of {score}/100. "
        )
        
        key_strengths = overall_assessment.get("key_strengths", [])
        if key_strengths:
            summary += f"Key industry strengths include: {', '.join(key_strengths[:2])}. "
        
        key_challenges = overall_assessment.get("key_challenges", [])
        if key_challenges:
            summary += f"Primary challenges: {', '.join(key_challenges[:2])}. "
        
        summary += overall_assessment.get("credit_implications", "")
        
        return summary
    
    def _empty_analysis_result(self, reason: str) -> Dict[str, Any]:
        """Return an empty analysis result with a reason."""
        return {
            "summary": f"Industry analysis could not be completed: {reason}",
            "industry": "Unknown",
            "sector_trends": {
                "current_state": "unknown",
                "key_trends": [],
                "growth_drivers": [],
                "headwinds": [],
                "technological_changes": [],
                "regulatory_environment": "Unknown",
                "economic_sensitivity": "unknown",
                "outlook": "unknown"
            },
            "competitive_landscape": {
                "market_structure": "unknown",
                "competitive_intensity": "unknown",
                "key_competitors": [],
                "barriers_to_entry": "unknown",
                "barriers_description": "",
                "competitive_factors": [],
                "market_share_dynamics": "Unknown",
                "pricing_power": "unknown",
                "differentiation_potential": "unknown"
            },
            "industry_risks": [],
            "market_opportunities": [],
            "growth_outlook": {
                "short_term_growth": "unknown",
                "medium_term_growth": "unknown",
                "growth_quality": "uncertain",
                "key_assumptions": [],
                "confidence_level": "low",
                "growth_narrative": reason
            },
            "overall_assessment": {
                "rating": "insufficient_data",
                "score": 0,
                "assessment": reason,
                "key_strengths": [],
                "key_challenges": [],
                "credit_implications": "Unable to assess industry impact on credit quality due to insufficient data."
            },
            "analysis_date": datetime.utcnow().isoformat(),
            "company_name": ""
        }
