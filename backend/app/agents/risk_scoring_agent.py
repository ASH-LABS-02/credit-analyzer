"""
Risk Scoring Agent

This agent calculates weighted risk scores from multiple factors (financial health,
cash flow, industry, promoter, external intelligence) and generates credit recommendations
with detailed explanations.

Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7
"""

import json
from typing import Dict, Any, Optional
from openai import AsyncOpenAI

from app.core.config import settings
from app.core.audit_logger import AuditLogger
from app.models.domain import CreditRecommendation, RiskFactorScore, RiskAssessment


class RiskScoringAgent:
    """
    AI agent for risk scoring and credit decision generation.
    
    Calculates a weighted credit score (0-100) from five risk factors:
    - Financial Health: 35% weight
    - Cash Flow: 25% weight
    - Industry: 15% weight
    - Promoter: 15% weight
    - External Intelligence: 10% weight
    
    Generates credit recommendations based on score thresholds:
    - Score >= 70: Approve
    - Score 40-69: Approve with conditions
    - Score < 40: Reject
    
    Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7
    """
    
    # Risk factor weights as specified in requirements
    WEIGHTS = {
        'financial_health': 0.35,
        'cash_flow': 0.25,
        'industry': 0.15,
        'promoter': 0.15,
        'external_intelligence': 0.10
    }
    
    # Score thresholds for recommendations
    THRESHOLD_APPROVE = 70.0
    THRESHOLD_CONDITIONAL = 40.0
    
    def __init__(self, audit_logger: Optional[AuditLogger] = None):
        """
        Initialize the Risk Scoring Agent.
        
        Args:
            audit_logger: Optional audit logger for AI decision logging
        """
        self.openai = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.audit_logger = audit_logger
    
    async def score(self, analysis_data: Dict[str, Any]) -> RiskAssessment:
        """
        Calculate weighted risk score and generate credit recommendation.
        
        Args:
            analysis_data: Dictionary containing:
                - financial: Financial analysis results from FinancialAnalysisAgent
                - forecasts: Forecast results from ForecastingAgent
                - research: Research findings from research agents
                    - web: Web research results
                    - promoter: Promoter intelligence results
                    - industry: Industry intelligence results
        
        Returns:
            RiskAssessment object with overall score, individual factor scores,
            recommendation, and detailed explanations
        
        Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7
        """
        # Extract data components
        financial_data = analysis_data.get('financial', {})
        forecasts_data = analysis_data.get('forecasts', {})
        research_data = analysis_data.get('research', {})
        
        # Score each risk factor (0-100)
        financial_health_score = await self._score_financial_health(financial_data)
        cash_flow_score = await self._score_cash_flow(financial_data, forecasts_data)
        industry_score = await self._score_industry(research_data.get('industry', {}))
        promoter_score = await self._score_promoter(research_data.get('promoter', {}))
        external_intelligence_score = await self._score_external_intelligence(
            research_data.get('web', {})
        )
        
        # Calculate weighted overall score
        overall_score = (
            financial_health_score.score * self.WEIGHTS['financial_health'] +
            cash_flow_score.score * self.WEIGHTS['cash_flow'] +
            industry_score.score * self.WEIGHTS['industry'] +
            promoter_score.score * self.WEIGHTS['promoter'] +
            external_intelligence_score.score * self.WEIGHTS['external_intelligence']
        )
        
        # Determine recommendation based on thresholds
        recommendation = self._determine_recommendation(overall_score)
        
        # Generate overall summary
        summary = await self._generate_summary(
            overall_score,
            recommendation,
            financial_health_score,
            cash_flow_score,
            industry_score,
            promoter_score,
            external_intelligence_score
        )
        
        # Build RiskAssessment
        risk_assessment = RiskAssessment(
            overall_score=round(overall_score, 2),
            recommendation=recommendation,
            financial_health=financial_health_score,
            cash_flow=cash_flow_score,
            industry=industry_score,
            promoter=promoter_score,
            external_intelligence=external_intelligence_score,
            summary=summary
        )
        
        # Log AI decision
        if self.audit_logger:
            try:
                application_id = analysis_data.get('application_id', 'unknown')
                await self.audit_logger.log_ai_decision(
                    agent_name='RiskScoringAgent',
                    application_id=application_id,
                    decision=f"Credit score: {risk_assessment.overall_score}/100, Recommendation: {recommendation.value}",
                    reasoning=f"Calculated weighted risk score from 5 factors: "
                             f"Financial Health ({financial_health_score.score:.1f}), "
                             f"Cash Flow ({cash_flow_score.score:.1f}), "
                             f"Industry ({industry_score.score:.1f}), "
                             f"Promoter ({promoter_score.score:.1f}), "
                             f"External Intelligence ({external_intelligence_score.score:.1f}). "
                             f"Summary: {summary[:200]}...",
                    data_sources=['financial_analysis', 'forecasts', 'web_research', 'promoter_intelligence', 'industry_intelligence'],
                    additional_details={
                        'overall_score': risk_assessment.overall_score,
                        'recommendation': recommendation.value,
                        'financial_health_score': financial_health_score.score,
                        'cash_flow_score': cash_flow_score.score,
                        'industry_score': industry_score.score,
                        'promoter_score': promoter_score.score,
                        'external_intelligence_score': external_intelligence_score.score,
                        'weights_applied': self.WEIGHTS
                    }
                )
            except Exception as e:
                print(f"Error logging AI decision: {str(e)}")
        
        return risk_assessment
    
    async def _score_financial_health(
        self,
        financial_data: Dict[str, Any]
    ) -> RiskFactorScore:
        """
        Score financial health based on ratios and benchmarks.
        
        Args:
            financial_data: Financial analysis results
        
        Returns:
            RiskFactorScore for financial health (0-100)
        
        Requirements: 6.1, 6.2, 6.3
        """
        ratios = financial_data.get('ratios', {})
        benchmarks = financial_data.get('benchmarks', {})
        trends = financial_data.get('trends', {})
        
        if not ratios:
            return RiskFactorScore(
                factor_name='financial_health',
                score=50.0,
                weight=self.WEIGHTS['financial_health'],
                explanation='Insufficient financial data for comprehensive assessment.',
                key_findings=['Limited financial data available']
            )
        
        # Calculate score based on benchmark performance
        performance_scores = []
        key_findings = []
        
        for ratio_name, benchmark_data in benchmarks.items():
            performance = benchmark_data.get('performance', 'acceptable')
            
            if performance == 'good':
                performance_scores.append(85)
                key_findings.append(f"Strong {ratio_name.replace('_', ' ')}")
            elif performance == 'acceptable':
                performance_scores.append(60)
            else:  # poor
                performance_scores.append(30)
                key_findings.append(f"Weak {ratio_name.replace('_', ' ')}")
        
        # Base score from ratio performance
        base_score = sum(performance_scores) / len(performance_scores) if performance_scores else 50.0
        
        # Adjust for trends
        revenue_trend = trends.get('revenue', {})
        profit_trend = trends.get('profit', {})
        
        trend_adjustment = 0
        if revenue_trend.get('trend_direction') == 'increasing':
            trend_adjustment += 5
            key_findings.append('Positive revenue growth trend')
        elif revenue_trend.get('trend_direction') == 'decreasing':
            trend_adjustment -= 5
            key_findings.append('Declining revenue trend')
        
        if profit_trend.get('trend_direction') == 'increasing':
            trend_adjustment += 5
            key_findings.append('Improving profitability')
        elif profit_trend.get('trend_direction') == 'decreasing':
            trend_adjustment -= 5
            key_findings.append('Declining profitability')
        
        final_score = max(0, min(100, base_score + trend_adjustment))
        
        # Generate explanation
        explanation = await self._generate_factor_explanation(
            'financial_health',
            final_score,
            {
                'ratios': ratios,
                'benchmarks': benchmarks,
                'trends': trends,
                'key_findings': key_findings
            }
        )
        
        return RiskFactorScore(
            factor_name='financial_health',
            score=round(final_score, 2),
            weight=self.WEIGHTS['financial_health'],
            explanation=explanation,
            key_findings=key_findings[:5]  # Limit to top 5 findings
        )
    
    async def _score_cash_flow(
        self,
        financial_data: Dict[str, Any],
        forecasts_data: Dict[str, Any]
    ) -> RiskFactorScore:
        """
        Score cash flow adequacy and sustainability.
        
        Args:
            financial_data: Financial analysis results
            forecasts_data: Forecast results
        
        Returns:
            RiskFactorScore for cash flow (0-100)
        
        Requirements: 6.1, 6.2, 6.3
        """
        trends = financial_data.get('trends', {})
        cash_flow_trend = trends.get('cash_flow', {})
        forecasts = forecasts_data.get('forecasts', {})
        cash_flow_forecast = forecasts.get('cash_flow', {})
        
        key_findings = []
        score_components = []
        
        # Component 1: Historical cash flow trend (40% of factor score)
        if cash_flow_trend:
            trend_direction = cash_flow_trend.get('trend_direction', 'unknown')
            cagr = cash_flow_trend.get('cagr')
            
            if trend_direction == 'increasing':
                score_components.append(80)
                key_findings.append('Positive cash flow growth trend')
            elif trend_direction == 'stable':
                score_components.append(65)
                key_findings.append('Stable cash flow generation')
            elif trend_direction == 'decreasing':
                score_components.append(35)
                key_findings.append('Declining cash flow trend')
            else:
                score_components.append(50)
            
            if cagr and cagr > 10:
                key_findings.append(f'Strong cash flow CAGR of {cagr:.1f}%')
            elif cagr and cagr < -5:
                key_findings.append(f'Concerning cash flow decline of {cagr:.1f}%')
        else:
            score_components.append(50)
            key_findings.append('Limited cash flow history')
        
        # Component 2: Cash flow forecast (30% of factor score)
        if cash_flow_forecast:
            projected_values = cash_flow_forecast.get('projected_values', [])
            forecast_growth = cash_flow_forecast.get('forecast_growth_rate', 0)
            
            if projected_values and all(v > 0 for v in projected_values):
                if forecast_growth > 5:
                    score_components.append(85)
                    key_findings.append('Projected cash flow growth')
                elif forecast_growth > 0:
                    score_components.append(70)
                    key_findings.append('Stable projected cash flow')
                else:
                    score_components.append(45)
                    key_findings.append('Projected cash flow decline')
            else:
                score_components.append(50)
        else:
            score_components.append(50)
        
        # Component 3: Current ratio (liquidity) (30% of factor score)
        ratios = financial_data.get('ratios', {})
        current_ratio_data = ratios.get('current_ratio', {})
        
        if current_ratio_data:
            current_ratio = current_ratio_data.get('value', 0)
            
            if current_ratio >= 2.0:
                score_components.append(90)
                key_findings.append('Strong liquidity position')
            elif current_ratio >= 1.5:
                score_components.append(75)
                key_findings.append('Adequate liquidity')
            elif current_ratio >= 1.0:
                score_components.append(55)
                key_findings.append('Acceptable liquidity')
            else:
                score_components.append(30)
                key_findings.append('Weak liquidity position')
        else:
            score_components.append(50)
        
        # Calculate final score
        final_score = sum(score_components) / len(score_components) if score_components else 50.0
        
        # Generate explanation
        explanation = await self._generate_factor_explanation(
            'cash_flow',
            final_score,
            {
                'cash_flow_trend': cash_flow_trend,
                'cash_flow_forecast': cash_flow_forecast,
                'ratios': ratios,
                'key_findings': key_findings
            }
        )
        
        return RiskFactorScore(
            factor_name='cash_flow',
            score=round(final_score, 2),
            weight=self.WEIGHTS['cash_flow'],
            explanation=explanation,
            key_findings=key_findings[:5]
        )
    
    async def _score_industry(
        self,
        industry_data: Dict[str, Any]
    ) -> RiskFactorScore:
        """
        Score industry outlook and competitive position.
        
        Args:
            industry_data: Industry intelligence results
        
        Returns:
            RiskFactorScore for industry (0-100)
        
        Requirements: 6.1, 6.2, 6.3
        """
        if not industry_data:
            return RiskFactorScore(
                factor_name='industry',
                score=50.0,
                weight=self.WEIGHTS['industry'],
                explanation='Limited industry intelligence available.',
                key_findings=['Industry analysis pending']
            )
        
        # Extract industry analysis components
        sector_outlook = industry_data.get('sector_outlook', '')
        competitive_position = industry_data.get('competitive_position', '')
        industry_risks = industry_data.get('industry_risks', [])
        growth_potential = industry_data.get('growth_potential', '')
        
        # Use AI to score based on qualitative analysis
        score = await self._ai_score_qualitative_factor(
            'industry',
            {
                'sector_outlook': sector_outlook,
                'competitive_position': competitive_position,
                'industry_risks': industry_risks,
                'growth_potential': growth_potential
            }
        )
        
        # Extract key findings
        key_findings = []
        if 'positive' in sector_outlook.lower() or 'growing' in sector_outlook.lower():
            key_findings.append('Favorable industry outlook')
        if 'strong' in competitive_position.lower():
            key_findings.append('Strong competitive position')
        if industry_risks:
            key_findings.extend(industry_risks[:2])
        if 'high' in growth_potential.lower():
            key_findings.append('High growth potential')
        
        # Generate explanation
        explanation = await self._generate_factor_explanation(
            'industry',
            score,
            {
                'sector_outlook': sector_outlook,
                'competitive_position': competitive_position,
                'industry_risks': industry_risks,
                'key_findings': key_findings
            }
        )
        
        return RiskFactorScore(
            factor_name='industry',
            score=round(score, 2),
            weight=self.WEIGHTS['industry'],
            explanation=explanation,
            key_findings=key_findings[:5]
        )
    
    async def _score_promoter(
        self,
        promoter_data: Dict[str, Any]
    ) -> RiskFactorScore:
        """
        Score promoter/management quality and track record.
        
        Args:
            promoter_data: Promoter intelligence results
        
        Returns:
            RiskFactorScore for promoter (0-100)
        
        Requirements: 6.1, 6.2, 6.3
        """
        if not promoter_data:
            return RiskFactorScore(
                factor_name='promoter',
                score=50.0,
                weight=self.WEIGHTS['promoter'],
                explanation='Limited promoter intelligence available.',
                key_findings=['Promoter analysis pending']
            )
        
        # Extract promoter analysis components
        background = promoter_data.get('background', '')
        track_record = promoter_data.get('track_record', '')
        reputation = promoter_data.get('reputation', '')
        red_flags = promoter_data.get('red_flags', [])
        experience = promoter_data.get('experience', '')
        
        # Use AI to score based on qualitative analysis
        score = await self._ai_score_qualitative_factor(
            'promoter',
            {
                'background': background,
                'track_record': track_record,
                'reputation': reputation,
                'red_flags': red_flags,
                'experience': experience
            }
        )
        
        # Adjust score for red flags
        if red_flags:
            score = max(0, score - (len(red_flags) * 10))
        
        # Extract key findings
        key_findings = []
        if 'experienced' in background.lower() or 'strong' in track_record.lower():
            key_findings.append('Experienced management team')
        if 'successful' in track_record.lower():
            key_findings.append('Proven track record')
        if red_flags:
            key_findings.extend([f'Red flag: {flag}' for flag in red_flags[:2]])
        if 'positive' in reputation.lower():
            key_findings.append('Positive industry reputation')
        
        # Generate explanation
        explanation = await self._generate_factor_explanation(
            'promoter',
            score,
            {
                'background': background,
                'track_record': track_record,
                'red_flags': red_flags,
                'key_findings': key_findings
            }
        )
        
        return RiskFactorScore(
            factor_name='promoter',
            score=round(score, 2),
            weight=self.WEIGHTS['promoter'],
            explanation=explanation,
            key_findings=key_findings[:5]
        )
    
    async def _score_external_intelligence(
        self,
        web_data: Dict[str, Any]
    ) -> RiskFactorScore:
        """
        Score based on external intelligence (news, reputation, market sentiment).
        
        Args:
            web_data: Web research results
        
        Returns:
            RiskFactorScore for external intelligence (0-100)
        
        Requirements: 6.1, 6.2, 6.3
        """
        if not web_data:
            return RiskFactorScore(
                factor_name='external_intelligence',
                score=50.0,
                weight=self.WEIGHTS['external_intelligence'],
                explanation='Limited external intelligence available.',
                key_findings=['External research pending']
            )
        
        # Extract web research components
        news_summary = web_data.get('news_summary', '')
        market_sentiment = web_data.get('market_sentiment', '')
        red_flags = web_data.get('red_flags', [])
        positive_indicators = web_data.get('positive_indicators', [])
        regulatory_issues = web_data.get('regulatory_issues', [])
        
        # Use AI to score based on qualitative analysis
        score = await self._ai_score_qualitative_factor(
            'external_intelligence',
            {
                'news_summary': news_summary,
                'market_sentiment': market_sentiment,
                'red_flags': red_flags,
                'positive_indicators': positive_indicators,
                'regulatory_issues': regulatory_issues
            }
        )
        
        # Adjust score for red flags and positive indicators
        if red_flags:
            score = max(0, score - (len(red_flags) * 8))
        if positive_indicators:
            score = min(100, score + (len(positive_indicators) * 5))
        
        # Extract key findings
        key_findings = []
        if positive_indicators:
            key_findings.extend(positive_indicators[:2])
        if red_flags:
            key_findings.extend([f'Concern: {flag}' for flag in red_flags[:2]])
        if 'positive' in market_sentiment.lower():
            key_findings.append('Positive market sentiment')
        if regulatory_issues:
            key_findings.append('Regulatory concerns identified')
        
        # Generate explanation
        explanation = await self._generate_factor_explanation(
            'external_intelligence',
            score,
            {
                'news_summary': news_summary,
                'red_flags': red_flags,
                'positive_indicators': positive_indicators,
                'key_findings': key_findings
            }
        )
        
        return RiskFactorScore(
            factor_name='external_intelligence',
            score=round(score, 2),
            weight=self.WEIGHTS['external_intelligence'],
            explanation=explanation,
            key_findings=key_findings[:5]
        )
    
    def _determine_recommendation(self, overall_score: float) -> CreditRecommendation:
        """
        Determine credit recommendation based on score thresholds.
        
        Args:
            overall_score: Overall credit score (0-100)
        
        Returns:
            CreditRecommendation enum value
        
        Requirements: 6.4, 6.5, 6.6
        """
        if overall_score >= self.THRESHOLD_APPROVE:
            return CreditRecommendation.APPROVE
        elif overall_score >= self.THRESHOLD_CONDITIONAL:
            return CreditRecommendation.APPROVE_WITH_CONDITIONS
        else:
            return CreditRecommendation.REJECT
    
    async def _ai_score_qualitative_factor(
        self,
        factor_name: str,
        factor_data: Dict[str, Any]
    ) -> float:
        """
        Use AI to score qualitative factors.
        
        Args:
            factor_name: Name of the factor
            factor_data: Data for the factor
        
        Returns:
            Score from 0-100
        """
        prompt = f"""Analyze the following {factor_name} information and provide a risk score from 0-100.

**Data:**
{json.dumps(factor_data, indent=2)}

**Scoring Guidelines:**
- 80-100: Excellent - Strong positive indicators, minimal risks
- 60-79: Good - Generally positive with minor concerns
- 40-59: Moderate - Mixed signals, some concerns
- 20-39: Poor - Significant concerns, limited positives
- 0-19: Very Poor - Major red flags, high risk

Return ONLY a JSON object with:
{{
  "score": <number between 0-100>,
  "reasoning": "<brief explanation>"
}}
"""
        
        try:
            response = await self.openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a credit risk analyst. Provide objective risk scores based on the provided information."
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
            score = result.get('score', 50.0)
            
            # Ensure score is within bounds
            return max(0, min(100, float(score)))
        
        except Exception as e:
            print(f"Error in AI scoring for {factor_name}: {str(e)}")
            # Return neutral score on error
            return 50.0
    
    async def _generate_factor_explanation(
        self,
        factor_name: str,
        score: float,
        context: Dict[str, Any]
    ) -> str:
        """
        Generate detailed explanation for a risk factor score.
        
        Args:
            factor_name: Name of the risk factor
            score: Calculated score
            context: Context data for explanation
        
        Returns:
            Detailed explanation text
        
        Requirements: 6.3, 6.7
        """
        prompt = f"""Generate a concise explanation for the {factor_name.replace('_', ' ')} risk factor score of {score:.1f}/100.

**Context:**
{json.dumps(context, indent=2, default=str)}

Provide a 2-3 sentence explanation that:
1. Summarizes the key factors contributing to this score
2. Highlights the most important positive or negative aspects
3. Is clear and actionable for credit decision-making

Return ONLY the explanation text, no JSON or formatting.
"""
        
        try:
            response = await self.openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a credit analyst. Provide clear, concise explanations of risk scores."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=200
            )
            
            explanation = response.choices[0].message.content.strip()
            return explanation
        
        except Exception as e:
            print(f"Error generating explanation for {factor_name}: {str(e)}")
            # Return fallback explanation
            return self._generate_fallback_explanation(factor_name, score, context)
    
    def _generate_fallback_explanation(
        self,
        factor_name: str,
        score: float,
        context: Dict[str, Any]
    ) -> str:
        """Generate a rule-based explanation as fallback."""
        key_findings = context.get('key_findings', [])
        
        if score >= 70:
            level = "strong"
        elif score >= 50:
            level = "moderate"
        else:
            level = "weak"
        
        explanation = f"The {factor_name.replace('_', ' ')} score of {score:.1f} indicates {level} performance. "
        
        if key_findings:
            explanation += f"Key factors include: {', '.join(key_findings[:3])}."
        
        return explanation
    
    async def _generate_summary(
        self,
        overall_score: float,
        recommendation: CreditRecommendation,
        financial_health: RiskFactorScore,
        cash_flow: RiskFactorScore,
        industry: RiskFactorScore,
        promoter: RiskFactorScore,
        external_intelligence: RiskFactorScore
    ) -> str:
        """
        Generate overall risk assessment summary.
        
        Args:
            overall_score: Overall credit score
            recommendation: Credit recommendation
            financial_health: Financial health factor score
            cash_flow: Cash flow factor score
            industry: Industry factor score
            promoter: Promoter factor score
            external_intelligence: External intelligence factor score
        
        Returns:
            Comprehensive summary text
        
        Requirements: 6.7
        """
        prompt = f"""Generate a comprehensive credit risk assessment summary.

**Overall Credit Score:** {overall_score:.1f}/100
**Recommendation:** {recommendation.value}

**Risk Factor Scores:**
- Financial Health ({financial_health.weight*100:.0f}%): {financial_health.score:.1f}/100
- Cash Flow ({cash_flow.weight*100:.0f}%): {cash_flow.score:.1f}/100
- Industry ({industry.weight*100:.0f}%): {industry.score:.1f}/100
- Promoter ({promoter.weight*100:.0f}%): {promoter.score:.1f}/100
- External Intelligence ({external_intelligence.weight*100:.0f}%): {external_intelligence.score:.1f}/100

**Key Findings:**
Financial Health: {', '.join(financial_health.key_findings[:2])}
Cash Flow: {', '.join(cash_flow.key_findings[:2])}
Industry: {', '.join(industry.key_findings[:2])}
Promoter: {', '.join(promoter.key_findings[:2])}
External Intelligence: {', '.join(external_intelligence.key_findings[:2])}

Provide a 3-4 sentence executive summary that:
1. States the overall credit assessment and recommendation
2. Highlights the strongest and weakest factors
3. Identifies key risks or opportunities
4. Provides actionable guidance for the credit decision

Return ONLY the summary text, no JSON or formatting.
"""
        
        try:
            response = await self.openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a senior credit analyst. Provide clear, actionable credit risk summaries for decision-makers."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=300
            )
            
            summary = response.choices[0].message.content.strip()
            return summary
        
        except Exception as e:
            print(f"Error generating summary: {str(e)}")
            # Return fallback summary
            return self._generate_fallback_summary(
                overall_score,
                recommendation,
                financial_health,
                cash_flow,
                industry,
                promoter,
                external_intelligence
            )
    
    def _generate_fallback_summary(
        self,
        overall_score: float,
        recommendation: CreditRecommendation,
        financial_health: RiskFactorScore,
        cash_flow: RiskFactorScore,
        industry: RiskFactorScore,
        promoter: RiskFactorScore,
        external_intelligence: RiskFactorScore
    ) -> str:
        """Generate a rule-based summary as fallback."""
        # Determine overall assessment
        if overall_score >= 70:
            assessment = "strong creditworthiness"
        elif overall_score >= 50:
            assessment = "moderate creditworthiness"
        else:
            assessment = "weak creditworthiness"
        
        # Find strongest and weakest factors
        factors = [
            ('Financial Health', financial_health.score),
            ('Cash Flow', cash_flow.score),
            ('Industry', industry.score),
            ('Promoter', promoter.score),
            ('External Intelligence', external_intelligence.score)
        ]
        factors.sort(key=lambda x: x[1], reverse=True)
        strongest = factors[0][0]
        weakest = factors[-1][0]
        
        # Build summary
        summary = f"The overall credit score of {overall_score:.1f} indicates {assessment}, "
        summary += f"leading to a recommendation to {recommendation.value.replace('_', ' ')}. "
        summary += f"The assessment is supported by strong {strongest} "
        summary += f"but is tempered by concerns in {weakest}. "
        
        if recommendation == CreditRecommendation.APPROVE_WITH_CONDITIONS:
            summary += "Approval should be conditional on addressing identified risk factors and implementing appropriate monitoring."
        elif recommendation == CreditRecommendation.REJECT:
            summary += "The identified risks outweigh the positive factors, making this application unsuitable for approval at this time."
        else:
            summary += "The company demonstrates solid fundamentals across all risk factors."
        
        return summary
