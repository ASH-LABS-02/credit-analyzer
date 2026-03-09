"""
Forecasting Agent

This agent generates 3-year financial projections using historical trends,
industry growth rates, and economic indicators. It provides confidence intervals
and documents all assumptions used in the forecasting process.

Requirements: 5.1, 5.2, 5.3, 5.5
"""

import json
from typing import Dict, List, Optional, Any
from openai import AsyncOpenAI

from app.core.config import settings
from app.core.audit_logger import AuditLogger
from app.core.retry import retry_with_backoff, RetryConfig
from app.services.financial_calculator import TimeSeriesAnalyzer


class ForecastingAgent:
    """
    AI agent for generating financial forecasts.
    
    Generates 3-year projections for:
    - Revenue
    - Profit
    - Cash flow
    - Debt levels
    
    Uses:
    - Historical trends and growth rates
    - Industry growth rates and benchmarks
    - Economic indicators
    - AI-powered analysis for intelligent forecasting
    
    Requirements: 5.1, 5.2, 5.3, 5.5
    """
    
    # Default industry growth rates (simplified - in production, this would come from a database)
    DEFAULT_INDUSTRY_GROWTH_RATES = {
        "default": {
            "revenue_growth": 5.0,  # 5% annual growth
            "profit_growth": 4.0,   # 4% annual growth
            "economic_growth": 3.0  # 3% GDP growth assumption
        },
        "technology": {
            "revenue_growth": 15.0,
            "profit_growth": 12.0,
            "economic_growth": 3.0
        },
        "manufacturing": {
            "revenue_growth": 4.0,
            "profit_growth": 3.5,
            "economic_growth": 3.0
        },
        "retail": {
            "revenue_growth": 3.5,
            "profit_growth": 3.0,
            "economic_growth": 3.0
        },
        "financial_services": {
            "revenue_growth": 6.0,
            "profit_growth": 5.5,
            "economic_growth": 3.0
        }
    }
    
    def __init__(self, audit_logger: Optional[AuditLogger] = None):
        """
        Initialize the Forecasting Agent.
        
        Args:
            audit_logger: Optional audit logger for AI decision logging
        """
        self.openai = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.time_series_analyzer = TimeSeriesAnalyzer()
        self.audit_logger = audit_logger
    
    async def predict(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate 3-year financial forecasts.
        
        Args:
            financial_data: Dictionary containing:
                - historical: Historical financial data with time series
                - industry: Industry classification (optional)
                - company_info: Company information (optional)
                - financial_analysis: Results from FinancialAnalysisAgent (optional)
        
        Returns:
            Dictionary containing:
                - forecasts: Dict of metric forecasts (revenue, profit, cash_flow, debt)
                - assumptions: List of assumptions used in forecasting
                - methodology: Description of forecasting methodology
                - confidence_level: Overall confidence in forecasts (0-100)
                - generated_at: Timestamp of forecast generation
        
        Requirements: 5.1, 5.2, 5.3, 5.5
        """
        if not financial_data:
            return self._empty_forecast_result("No financial data provided")
        
        historical = financial_data.get("historical", {})
        if not historical:
            # Try to extract from financial_data directly
            historical = financial_data
        
        # Extract industry information
        industry = self._extract_industry(financial_data)
        
        # Get industry growth rates
        industry_growth_rates = self._get_industry_growth_rates(industry)
        
        # Step 1: Analyze historical data and calculate growth rates
        historical_analysis = await self._analyze_historical_data(historical)
        
        # Step 2: Generate forecasts for each metric
        forecasts = {}
        
        # Forecast revenue
        if historical_analysis.get("revenue"):
            forecasts["revenue"] = await self._forecast_metric(
                metric_name="revenue",
                historical_data=historical_analysis["revenue"],
                industry_growth=industry_growth_rates.get("revenue_growth", 5.0),
                financial_data=financial_data
            )
        
        # Forecast profit
        if historical_analysis.get("profit"):
            forecasts["profit"] = await self._forecast_metric(
                metric_name="profit",
                historical_data=historical_analysis["profit"],
                industry_growth=industry_growth_rates.get("profit_growth", 4.0),
                financial_data=financial_data
            )
        
        # Forecast cash flow
        if historical_analysis.get("cash_flow"):
            forecasts["cash_flow"] = await self._forecast_metric(
                metric_name="cash_flow",
                historical_data=historical_analysis["cash_flow"],
                industry_growth=industry_growth_rates.get("revenue_growth", 5.0) * 0.8,  # Typically lower than revenue
                financial_data=financial_data
            )
        
        # Forecast debt
        if historical_analysis.get("debt"):
            forecasts["debt"] = await self._forecast_metric(
                metric_name="debt",
                historical_data=historical_analysis["debt"],
                industry_growth=0.0,  # Debt growth depends on company strategy, not industry
                financial_data=financial_data
            )
        
        # Step 3: Use AI to refine forecasts and generate comprehensive analysis
        ai_enhanced_forecasts = await self._ai_enhance_forecasts(
            forecasts,
            historical_analysis,
            industry_growth_rates,
            financial_data
        )
        
        # Step 4: Calculate overall confidence level
        confidence_level = self._calculate_confidence_level(
            historical_analysis,
            forecasts
        )
        
        # Step 5: Document assumptions
        assumptions = self._document_assumptions(
            historical_analysis,
            industry_growth_rates,
            financial_data
        )
        
        # Step 6: Document methodology
        methodology = self._document_methodology()
        
        from datetime import datetime
        
        result = {
            "forecasts": ai_enhanced_forecasts if ai_enhanced_forecasts else forecasts,
            "assumptions": assumptions,
            "methodology": methodology,
            "confidence_level": confidence_level,
            "generated_at": datetime.utcnow().isoformat(),
            "industry": industry,
            "industry_growth_rates": industry_growth_rates
        }
        
        # Log AI decision
        if self.audit_logger:
            try:
                application_id = financial_data.get('application_id', 'unknown')
                forecast_metrics = list(forecasts.keys())
                await self.audit_logger.log_ai_decision(
                    agent_name='ForecastingAgent',
                    application_id=application_id,
                    decision=f"Generated 3-year forecasts for {len(forecast_metrics)} metrics with {confidence_level:.1f}% confidence",
                    reasoning=f"Analyzed historical trends and applied industry growth rates for {industry}. "
                             f"Forecasted metrics: {', '.join(forecast_metrics)}. "
                             f"Methodology: {methodology[:150]}...",
                    data_sources=['historical_financial_data', 'industry_growth_rates', 'economic_indicators'],
                    additional_details={
                        'forecasted_metrics': forecast_metrics,
                        'confidence_level': confidence_level,
                        'industry': industry,
                        'assumptions_count': len(assumptions),
                        'industry_growth_rates': industry_growth_rates
                    }
                )
            except Exception as e:
                print(f"Error logging AI decision: {str(e)}")
        
        return result
    
    async def _analyze_historical_data(
        self,
        historical: Dict[str, Any]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Analyze historical data to extract trends and patterns.
        
        Args:
            historical: Historical financial data
        
        Returns:
            Dictionary mapping metric names to their historical analysis
        """
        analysis = {}
        
        # Metrics to analyze
        metrics = ["revenue", "profit", "cash_flow", "debt"]
        
        for metric_name in metrics:
            if metric_name in historical:
                metric_data = historical[metric_name]
                
                # Extract values and years
                values = []
                years = []
                
                if isinstance(metric_data, dict):
                    values = metric_data.get("values", [])
                    years = metric_data.get("years", [])
                elif isinstance(metric_data, list):
                    values = metric_data
                
                if not values or len(values) < 2:
                    continue
                
                # Calculate growth rates
                growth_rates = self.time_series_analyzer.calculate_growth_rates(values)
                
                # Calculate CAGR
                cagr = None
                if len(values) >= 2:
                    cagr = self.time_series_analyzer.calculate_cagr(
                        values[0],
                        values[-1],
                        len(values) - 1
                    )
                
                # Analyze trend
                trend = self.time_series_analyzer.analyze_trend(values)
                
                # Calculate average growth rate (excluding None values)
                valid_growth_rates = [gr for gr in growth_rates if gr is not None]
                avg_growth_rate = sum(valid_growth_rates) / len(valid_growth_rates) if valid_growth_rates else 0.0
                
                analysis[metric_name] = {
                    "values": values,
                    "years": years if years else [f"Year {i+1}" for i in range(len(values))],
                    "growth_rates": growth_rates,
                    "cagr": cagr,
                    "trend": trend.value,
                    "avg_growth_rate": avg_growth_rate,
                    "latest_value": values[-1] if values else 0
                }
        
        return analysis
    
    async def _forecast_metric(
        self,
        metric_name: str,
        historical_data: Dict[str, Any],
        industry_growth: float,
        financial_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate forecast for a single metric.
        
        Args:
            metric_name: Name of the metric to forecast
            historical_data: Historical analysis for this metric
            industry_growth: Industry growth rate for this metric
            financial_data: Full financial data context
        
        Returns:
            Dictionary containing forecast details
        """
        latest_value = historical_data.get("latest_value", 0)
        cagr = historical_data.get("cagr", 0)
        avg_growth_rate = historical_data.get("avg_growth_rate", 0)
        
        # Determine forecast growth rate
        # Blend historical growth with industry growth (weighted average)
        # Give more weight to historical if we have good data
        historical_weight = 0.7 if len(historical_data.get("values", [])) >= 3 else 0.5
        industry_weight = 1.0 - historical_weight
        
        # Use CAGR if available, otherwise use average growth rate
        historical_growth = cagr if cagr is not None else avg_growth_rate
        
        forecast_growth_rate = (historical_growth * historical_weight) + (industry_growth * industry_weight)
        
        # Generate 3-year projections
        projections = []
        current_value = latest_value
        
        for year in range(1, 4):  # Years 1, 2, 3
            # Apply growth rate
            projected_value = current_value * (1 + forecast_growth_rate / 100)
            projections.append(projected_value)
            current_value = projected_value
        
        # Calculate confidence intervals (simplified approach)
        # In production, this would use more sophisticated statistical methods
        confidence_intervals = self._calculate_confidence_intervals(
            projections,
            historical_data,
            forecast_growth_rate
        )
        
        return {
            "metric_name": metric_name,
            "historical_values": historical_data.get("values", []),
            "historical_years": historical_data.get("years", []),
            "projected_values": projections,
            "projected_years": ["Year 1", "Year 2", "Year 3"],
            "forecast_growth_rate": forecast_growth_rate,
            "confidence_intervals": confidence_intervals,
            "methodology": f"Blended forecast using {historical_weight*100:.0f}% historical trends and {industry_weight*100:.0f}% industry growth"
        }
    
    def _calculate_confidence_intervals(
        self,
        projections: List[float],
        historical_data: Dict[str, Any],
        forecast_growth_rate: float
    ) -> List[Dict[str, float]]:
        """
        Calculate confidence intervals for projections.
        
        Args:
            projections: Projected values
            historical_data: Historical data analysis
            forecast_growth_rate: Growth rate used for forecast
        
        Returns:
            List of confidence intervals for each projection
        """
        confidence_intervals = []
        
        # Calculate volatility from historical growth rates
        growth_rates = historical_data.get("growth_rates", [])
        valid_growth_rates = [gr for gr in growth_rates if gr is not None]
        
        if len(valid_growth_rates) > 1:
            # Calculate standard deviation of growth rates
            avg_growth = sum(valid_growth_rates) / len(valid_growth_rates)
            variance = sum((gr - avg_growth) ** 2 for gr in valid_growth_rates) / len(valid_growth_rates)
            std_dev = variance ** 0.5
        else:
            # Default to 10% standard deviation if insufficient data
            std_dev = 10.0
        
        # Generate confidence intervals for each projection
        # Uncertainty increases with forecast horizon
        for i, projected_value in enumerate(projections):
            year_multiplier = i + 1  # 1, 2, 3
            
            # Confidence interval widens with time
            # Ensure minimum interval width of 5% to avoid zero-width intervals
            interval_width = max(
                (std_dev * year_multiplier) / 100 * projected_value,
                projected_value * 0.05 * year_multiplier  # Minimum 5%, 10%, 15% for years 1, 2, 3
            )
            
            confidence_intervals.append({
                "lower_bound": projected_value - interval_width,
                "upper_bound": projected_value + interval_width,
                "confidence_level": max(70 - (year_multiplier * 5), 50)  # Decreases from 70% to 60% to 55%
            })
        
        return confidence_intervals
    
    async def _ai_enhance_forecasts(
        self,
        forecasts: Dict[str, Dict[str, Any]],
        historical_analysis: Dict[str, Dict[str, Any]],
        industry_growth_rates: Dict[str, float],
        financial_data: Dict[str, Any]
    ) -> Optional[Dict[str, Dict[str, Any]]]:
        """
        Use AI to enhance and refine forecasts with intelligent analysis.
        
        Args:
            forecasts: Initial forecasts generated
            historical_analysis: Historical data analysis
            industry_growth_rates: Industry growth rates
            financial_data: Full financial data context
        
        Returns:
            Enhanced forecasts or None if AI enhancement fails
        """
        # Build prompt for AI enhancement
        prompt = self._build_forecast_enhancement_prompt(
            forecasts,
            historical_analysis,
            industry_growth_rates,
            financial_data
        )
        
        try:
            # Configure retry for OpenAI API calls
            retry_config = RetryConfig(
                max_retries=3,
                base_delay=1.0,
                max_delay=30.0,
                exponential_base=2.0,
                jitter=True
            )
            
            response = await retry_with_backoff(
                self.openai.chat.completions.create,
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a financial forecasting expert. Analyze the provided forecasts and suggest refinements based on trends, industry dynamics, and financial health indicators."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.3,  # Low temperature for consistent analysis
                config=retry_config
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Extract enhanced forecasts and insights
            enhanced_forecasts = result.get("enhanced_forecasts", {})
            insights = result.get("insights", "")
            
            # Merge AI insights into forecasts
            for metric_name, forecast in forecasts.items():
                if metric_name in enhanced_forecasts:
                    ai_forecast = enhanced_forecasts[metric_name]
                    
                    # Update projections if AI provides them
                    if "projected_values" in ai_forecast:
                        forecast["ai_adjusted_values"] = ai_forecast["projected_values"]
                    
                    # Add AI insights
                    if "insights" in ai_forecast:
                        forecast["ai_insights"] = ai_forecast["insights"]
            
            # Add overall insights
            if insights:
                for forecast in forecasts.values():
                    if "ai_insights" not in forecast:
                        forecast["ai_insights"] = insights
            
            return forecasts
        
        except Exception as e:
            print(f"Error in AI forecast enhancement: {str(e)}")
            # Return original forecasts if AI enhancement fails
            return None
    
    def _build_forecast_enhancement_prompt(
        self,
        forecasts: Dict[str, Dict[str, Any]],
        historical_analysis: Dict[str, Dict[str, Any]],
        industry_growth_rates: Dict[str, float],
        financial_data: Dict[str, Any]
    ) -> str:
        """Build prompt for AI forecast enhancement."""
        company_info = financial_data.get("company_info", {})
        company_name = company_info.get("company_name", "the company") if isinstance(company_info, dict) else "the company"
        
        prompt = f"""Analyze and enhance the following financial forecasts for {company_name}.

**Historical Analysis:**
"""
        
        for metric_name, analysis in historical_analysis.items():
            prompt += f"\n{metric_name.replace('_', ' ').title()}:\n"
            prompt += f"  - Historical values: {analysis.get('values', [])}\n"
            prompt += f"  - Trend: {analysis.get('trend', 'unknown')}\n"
            prompt += f"  - CAGR: {analysis.get('cagr', 'N/A'):.2f}% (if available)\n"
            prompt += f"  - Average growth rate: {analysis.get('avg_growth_rate', 0):.2f}%\n"
        
        prompt += f"\n**Industry Growth Rates:**\n"
        for key, value in industry_growth_rates.items():
            prompt += f"  - {key.replace('_', ' ').title()}: {value:.2f}%\n"
        
        prompt += f"\n**Initial Forecasts:**\n"
        for metric_name, forecast in forecasts.items():
            prompt += f"\n{metric_name.replace('_', ' ').title()}:\n"
            prompt += f"  - Projected values: {forecast.get('projected_values', [])}\n"
            prompt += f"  - Forecast growth rate: {forecast.get('forecast_growth_rate', 0):.2f}%\n"
        
        prompt += """
Please analyze these forecasts and provide:
1. Validation of the forecast assumptions
2. Any recommended adjustments based on:
   - Historical trend consistency
   - Industry dynamics
   - Financial health indicators
   - Economic factors
3. Key insights about the forecast reliability
4. Risk factors that could impact projections

Return as JSON with:
{
  "enhanced_forecasts": {
    "revenue": {
      "projected_values": [adjusted values if needed],
      "insights": "specific insights for this metric"
    },
    ... (for each metric)
  },
  "insights": "overall forecast insights and reliability assessment"
}

Only adjust projections if there's a clear reason. Otherwise, validate the existing forecasts.
"""
        
        return prompt
    
    def _calculate_confidence_level(
        self,
        historical_analysis: Dict[str, Dict[str, Any]],
        forecasts: Dict[str, Dict[str, Any]]
    ) -> float:
        """
        Calculate overall confidence level in forecasts.
        
        Args:
            historical_analysis: Historical data analysis
            forecasts: Generated forecasts
        
        Returns:
            Confidence level from 0-100
        """
        confidence_factors = []
        
        # Factor 1: Data availability (more historical data = higher confidence)
        for metric_name, analysis in historical_analysis.items():
            values = analysis.get("values", [])
            if len(values) >= 5:
                confidence_factors.append(90)
            elif len(values) >= 3:
                confidence_factors.append(75)
            elif len(values) >= 2:
                confidence_factors.append(60)
            else:
                confidence_factors.append(40)
        
        # Factor 2: Trend consistency (stable trends = higher confidence)
        for metric_name, analysis in historical_analysis.items():
            trend = analysis.get("trend", "")
            if trend in ["increasing", "stable"]:
                confidence_factors.append(80)
            elif trend == "decreasing":
                confidence_factors.append(70)
            elif trend == "volatile":
                confidence_factors.append(50)
            else:
                confidence_factors.append(40)
        
        # Factor 3: Growth rate stability (consistent growth = higher confidence)
        for metric_name, analysis in historical_analysis.items():
            growth_rates = analysis.get("growth_rates", [])
            valid_growth_rates = [gr for gr in growth_rates if gr is not None]
            
            if len(valid_growth_rates) > 1:
                # Calculate coefficient of variation
                avg_growth = sum(valid_growth_rates) / len(valid_growth_rates)
                if avg_growth != 0:
                    variance = sum((gr - avg_growth) ** 2 for gr in valid_growth_rates) / len(valid_growth_rates)
                    std_dev = variance ** 0.5
                    cv = abs(std_dev / avg_growth) if avg_growth != 0 else 1.0
                    
                    # Lower CV = higher confidence
                    if cv < 0.2:
                        confidence_factors.append(85)
                    elif cv < 0.5:
                        confidence_factors.append(70)
                    else:
                        confidence_factors.append(55)
        
        # Calculate overall confidence as average of factors
        if confidence_factors:
            overall_confidence = sum(confidence_factors) / len(confidence_factors)
        else:
            overall_confidence = 50.0  # Default moderate confidence
        
        return round(overall_confidence, 1)
    
    def _document_assumptions(
        self,
        historical_analysis: Dict[str, Dict[str, Any]],
        industry_growth_rates: Dict[str, float],
        financial_data: Dict[str, Any]
    ) -> List[str]:
        """
        Document all assumptions used in forecasting.
        
        Args:
            historical_analysis: Historical data analysis
            industry_growth_rates: Industry growth rates used
            financial_data: Full financial data context
        
        Returns:
            List of assumption statements
        
        Requirements: 5.5
        """
        assumptions = []
        
        # Assumption 1: Historical trends continue
        assumptions.append(
            "Historical financial trends will continue with adjustments for industry dynamics and economic conditions."
        )
        
        # Assumption 2: Industry growth rates
        industry = self._extract_industry(financial_data)
        assumptions.append(
            f"Industry growth rates for {industry} sector are applied: "
            f"revenue growth {industry_growth_rates.get('revenue_growth', 5.0):.1f}%, "
            f"profit growth {industry_growth_rates.get('profit_growth', 4.0):.1f}%."
        )
        
        # Assumption 3: Economic conditions
        assumptions.append(
            f"Economic growth rate of {industry_growth_rates.get('economic_growth', 3.0):.1f}% is assumed "
            "based on current economic indicators."
        )
        
        # Assumption 4: No major disruptions
        assumptions.append(
            "No major business disruptions, regulatory changes, or market shocks are anticipated "
            "during the forecast period."
        )
        
        # Assumption 5: Company maintains current strategy
        assumptions.append(
            "The company maintains its current business strategy, operational model, and market positioning."
        )
        
        # Assumption 6: Data quality
        data_years = 0
        for analysis in historical_analysis.values():
            data_years = max(data_years, len(analysis.get("values", [])))
        
        assumptions.append(
            f"Forecasts are based on {data_years} years of historical data. "
            f"Confidence decreases with forecast horizon due to increasing uncertainty."
        )
        
        # Assumption 7: Blended methodology
        assumptions.append(
            "Forecasts use a blended methodology combining historical trends (weighted 50-70%) "
            "with industry benchmarks (weighted 30-50%) depending on data availability."
        )
        
        return assumptions
    
    def _document_methodology(self) -> str:
        """
        Document the forecasting methodology.
        
        Returns:
            Description of methodology used
        
        Requirements: 5.5
        """
        methodology = """
**Forecasting Methodology:**

This forecast uses a hybrid approach combining quantitative analysis with AI-enhanced insights:

1. **Historical Trend Analysis**: Calculate growth rates, CAGR, and trend direction from historical data
2. **Industry Benchmarking**: Incorporate industry-specific growth rates and economic indicators
3. **Blended Forecasting**: Weight historical trends (50-70%) and industry benchmarks (30-50%) based on data quality
4. **AI Enhancement**: Use GPT-4 to validate assumptions and refine projections based on financial health indicators
5. **Confidence Intervals**: Calculate uncertainty ranges that widen with forecast horizon
6. **Assumption Documentation**: Explicitly document all assumptions for transparency

The methodology prioritizes historical data when available (3+ years) and relies more on industry benchmarks when historical data is limited. Confidence levels reflect data quality, trend consistency, and forecast horizon.
"""
        return methodology.strip()
    
    def _extract_industry(self, financial_data: Dict[str, Any]) -> str:
        """Extract industry classification from financial data."""
        company_info = financial_data.get("company_info", {})
        
        if isinstance(company_info, dict):
            industry = company_info.get("industry", "default")
        else:
            industry = "default"
        
        # Normalize industry name
        if industry:
            industry = industry.lower().strip()
        
        return industry if industry else "default"
    
    def _get_industry_growth_rates(self, industry: str) -> Dict[str, float]:
        """
        Get industry-specific growth rates.
        
        Args:
            industry: Industry classification
        
        Returns:
            Dictionary of growth rates for the industry
        """
        # Normalize industry name
        industry_key = industry.lower().replace(" ", "_") if industry else "default"
        
        # Return industry-specific rates or default
        return self.DEFAULT_INDUSTRY_GROWTH_RATES.get(
            industry_key,
            self.DEFAULT_INDUSTRY_GROWTH_RATES["default"]
        )
    
    def _empty_forecast_result(self, reason: str) -> Dict[str, Any]:
        """Return an empty forecast result with a reason."""
        from datetime import datetime
        
        return {
            "forecasts": {},
            "assumptions": [f"Forecast could not be generated: {reason}"],
            "methodology": self._document_methodology(),
            "confidence_level": 0.0,
            "generated_at": datetime.utcnow().isoformat(),
            "industry": "unknown",
            "industry_growth_rates": {}
        }
