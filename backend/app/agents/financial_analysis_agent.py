"""
Financial Analysis Agent

This agent analyzes extracted financial data, calculates ratios, identifies trends,
and compares against industry benchmarks. It provides comprehensive financial analysis
with metadata and definitions for all calculated metrics.

Requirements: 4.1, 4.2, 4.5
"""

from typing import Dict, List, Optional, Any
from openai import AsyncOpenAI

from app.core.config import settings
from app.core.audit_logger import AuditLogger
from app.services.financial_calculator import FinancialCalculator, TimeSeriesAnalyzer, TrendDirection


class FinancialAnalysisAgent:
    """
    AI agent for comprehensive financial analysis.
    
    Analyzes extracted financial data to:
    - Calculate key financial ratios (liquidity, leverage, profitability, efficiency)
    - Identify trends and patterns in historical data
    - Compare metrics against industry benchmarks
    - Provide definitions and context for all calculated metrics
    
    Requirements: 4.1, 4.2, 4.5
    """
    
    # Industry benchmark data (simplified - in production, this would come from a database)
    INDUSTRY_BENCHMARKS = {
        "default": {
            "current_ratio": {"good": 2.0, "acceptable": 1.5, "poor": 1.0},
            "quick_ratio": {"good": 1.5, "acceptable": 1.0, "poor": 0.5},
            "debt_to_equity": {"good": 0.5, "acceptable": 1.0, "poor": 2.0},
            "debt_ratio": {"good": 0.3, "acceptable": 0.5, "poor": 0.7},
            "net_profit_margin": {"good": 0.15, "acceptable": 0.10, "poor": 0.05},
            "roe": {"good": 0.15, "acceptable": 0.10, "poor": 0.05},
            "roa": {"good": 0.10, "acceptable": 0.05, "poor": 0.02},
            "asset_turnover": {"good": 1.5, "acceptable": 1.0, "poor": 0.5}
        }
    }
    
    # Metric definitions for user understanding
    METRIC_DEFINITIONS = {
        "current_ratio": {
            "name": "Current Ratio",
            "formula": "Current Assets / Current Liabilities",
            "description": "Measures a company's ability to pay short-term obligations with current assets. A ratio above 1.0 indicates the company has more current assets than current liabilities.",
            "interpretation": "Higher is generally better, but very high ratios may indicate inefficient use of assets."
        },
        "quick_ratio": {
            "name": "Quick Ratio (Acid-Test Ratio)",
            "formula": "(Current Assets - Inventory) / Current Liabilities",
            "description": "Measures a company's ability to meet short-term obligations with its most liquid assets, excluding inventory.",
            "interpretation": "A ratio above 1.0 is generally considered healthy, indicating sufficient liquid assets to cover short-term liabilities."
        },
        "debt_to_equity": {
            "name": "Debt-to-Equity Ratio",
            "formula": "Total Debt / Total Equity",
            "description": "Measures the degree of financial leverage by comparing total debt to shareholders' equity.",
            "interpretation": "Lower ratios indicate less financial risk. Ratios above 2.0 may indicate high leverage and financial risk."
        },
        "debt_ratio": {
            "name": "Debt Ratio",
            "formula": "Total Debt / Total Assets",
            "description": "Measures the proportion of a company's assets that are financed by debt.",
            "interpretation": "Lower ratios indicate less reliance on debt financing. Ratios above 0.7 may indicate high financial risk."
        },
        "net_profit_margin": {
            "name": "Net Profit Margin",
            "formula": "Net Income / Revenue",
            "description": "Measures how much profit is generated from each dollar of revenue after all expenses.",
            "interpretation": "Higher margins indicate better profitability. Industry averages vary significantly."
        },
        "roe": {
            "name": "Return on Equity (ROE)",
            "formula": "Net Income / Total Equity",
            "description": "Measures profitability relative to shareholders' equity, indicating how efficiently equity is used to generate profit.",
            "interpretation": "Higher ROE indicates better returns for shareholders. ROE above 15% is generally considered good."
        },
        "roa": {
            "name": "Return on Assets (ROA)",
            "formula": "Net Income / Total Assets",
            "description": "Measures how efficiently a company uses its assets to generate profit.",
            "interpretation": "Higher ROA indicates more efficient asset utilization. ROA above 5% is generally considered good."
        },
        "asset_turnover": {
            "name": "Asset Turnover Ratio",
            "formula": "Revenue / Total Assets",
            "description": "Measures how efficiently a company uses its assets to generate revenue.",
            "interpretation": "Higher ratios indicate more efficient use of assets. Varies significantly by industry."
        },
        "inventory_turnover": {
            "name": "Inventory Turnover Ratio",
            "formula": "Cost of Goods Sold / Average Inventory",
            "description": "Measures how many times inventory is sold and replaced over a period.",
            "interpretation": "Higher ratios indicate faster inventory turnover, which is generally positive but varies by industry."
        }
    }
    
    def __init__(self, audit_logger: Optional[AuditLogger] = None):
        """
        Initialize the Financial Analysis Agent.
        
        Args:
            audit_logger: Optional audit logger for AI decision logging
        """
        self.openai = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.calculator = FinancialCalculator()
        self.time_series_analyzer = TimeSeriesAnalyzer()
        self.audit_logger = audit_logger
    
    async def analyze(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform comprehensive financial analysis on extracted data.
        
        Args:
            extracted_data: Dictionary containing extracted financial data from
                          DocumentIntelligenceAgent, including financial_data,
                          source_tracking, and ambiguous_flags
        
        Returns:
            Dictionary containing:
                - ratios: Calculated financial ratios with metadata
                - trends: Trend analysis for time-series metrics
                - benchmarks: Industry benchmark comparisons
                - summary: AI-generated analysis summary
                - definitions: Definitions for all calculated metrics
        
        Requirements: 4.1, 4.2, 4.5
        """
        financial_data = extracted_data.get("financial_data", {})
        
        if not financial_data:
            return {
                "ratios": {},
                "trends": {},
                "benchmarks": {},
                "summary": "Insufficient financial data for analysis.",
                "definitions": {}
            }
        
        # Step 1: Calculate financial ratios
        ratios = await self._calculate_ratios(financial_data)
        
        # Step 2: Analyze trends in time-series data
        trends = await self._analyze_trends(financial_data)
        
        # Step 3: Compare against industry benchmarks
        benchmarks = await self._compare_benchmarks(ratios, financial_data)
        
        # Step 4: Generate AI-powered analysis summary
        summary = await self._generate_summary(ratios, trends, benchmarks, financial_data)
        
        # Step 5: Provide definitions for all calculated metrics
        definitions = self._get_metric_definitions(ratios, trends)
        
        # Log AI decision
        if self.audit_logger:
            try:
                application_id = extracted_data.get('application_id', 'unknown')
                await self.audit_logger.log_ai_decision(
                    agent_name='FinancialAnalysisAgent',
                    application_id=application_id,
                    decision=f"Completed financial analysis with {len(ratios)} ratios and {len(trends)} trend analyses",
                    reasoning=f"Calculated financial ratios, analyzed trends, compared against industry benchmarks. "
                             f"Overall assessment: {summary[:200]}...",
                    data_sources=['extracted_financial_data', 'industry_benchmarks'],
                    additional_details={
                        'ratios_calculated': list(ratios.keys()),
                        'trends_analyzed': list(trends.keys()),
                        'benchmarks_compared': list(benchmarks.keys()),
                        'definitions_provided': len(definitions)
                    }
                )
            except Exception as e:
                print(f"Error logging AI decision: {str(e)}")
        
        return {
            "ratios": ratios,
            "trends": trends,
            "benchmarks": benchmarks,
            "summary": summary,
            "definitions": definitions
        }
    
    async def _calculate_ratios(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate all available financial ratios from the extracted data.
        
        Args:
            financial_data: Extracted financial data
        
        Returns:
            Dictionary of calculated ratios with values and metadata
        
        Requirements: 4.1
        """
        ratios = {}
        
        # Extract financial metrics from the nested structure
        financial_metrics = financial_data.get("financial_metrics", {})
        
        # Prepare data for ratio calculation
        ratio_input = {}
        
        # Extract single-point values
        for key in ["current_assets", "current_liabilities", "total_assets", 
                    "total_equity", "total_debt", "inventory", "cost_of_goods_sold", 
                    "average_inventory"]:
            if key in financial_metrics:
                metric_data = financial_metrics[key]
                if isinstance(metric_data, dict) and "value" in metric_data:
                    ratio_input[key] = metric_data["value"]
                elif isinstance(metric_data, (int, float)):
                    ratio_input[key] = metric_data
        
        # Extract most recent values from time series
        for key in ["revenue", "profit", "net_income"]:
            if key in financial_metrics:
                metric_data = financial_metrics[key]
                if isinstance(metric_data, dict) and "values" in metric_data:
                    values = metric_data["values"]
                    if values and len(values) > 0:
                        # Use most recent value
                        ratio_input[key] = values[-1]
                elif isinstance(metric_data, list) and len(metric_data) > 0:
                    ratio_input[key] = metric_data[-1]
        
        # Handle net_income alias for profit
        if "net_income" not in ratio_input and "profit" in ratio_input:
            ratio_input["net_income"] = ratio_input["profit"]
        
        # Calculate ratios using FinancialCalculator
        calculated_ratios = self.calculator.calculate_ratios(ratio_input)
        
        # Enrich ratios with metadata
        for ratio_name, ratio_value in calculated_ratios.items():
            ratios[ratio_name] = {
                "value": ratio_value,
                "formatted_value": self._format_ratio_value(ratio_name, ratio_value),
                "definition": self.METRIC_DEFINITIONS.get(ratio_name, {}).get("description", ""),
                "formula": self.METRIC_DEFINITIONS.get(ratio_name, {}).get("formula", "")
            }
        
        return ratios
    
    async def _analyze_trends(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze trends in time-series financial data.
        
        Args:
            financial_data: Extracted financial data
        
        Returns:
            Dictionary of trend analyses for each time-series metric
        
        Requirements: 4.2
        """
        trends = {}
        
        financial_metrics = financial_data.get("financial_metrics", {})
        
        # Analyze trends for key time-series metrics
        time_series_metrics = ["revenue", "profit", "debt", "cash_flow"]
        
        for metric_name in time_series_metrics:
            if metric_name in financial_metrics:
                metric_data = financial_metrics[metric_name]
                
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
                
                # Calculate CAGR if we have enough data
                cagr = None
                if len(values) >= 2:
                    cagr = self.time_series_analyzer.calculate_cagr(
                        values[0],
                        values[-1],
                        len(values) - 1
                    )
                
                # Analyze trend direction
                trend_direction = self.time_series_analyzer.analyze_trend(values)
                
                # Perform multi-year comparison
                comparison = self.time_series_analyzer.compare_multi_year(values, years)
                
                trends[metric_name] = {
                    "values": values,
                    "years": years if years else [f"Year {i+1}" for i in range(len(values))],
                    "growth_rates": growth_rates,
                    "cagr": cagr,
                    "trend_direction": trend_direction.value,
                    "comparison": comparison,
                    "interpretation": self._interpret_trend(metric_name, trend_direction, cagr)
                }
        
        return trends
    
    async def _compare_benchmarks(
        self, 
        ratios: Dict[str, Any], 
        financial_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compare calculated ratios against industry benchmarks.
        
        Args:
            ratios: Calculated financial ratios
            financial_data: Original financial data (may contain industry info)
        
        Returns:
            Dictionary of benchmark comparisons for each ratio
        
        Requirements: 4.5
        """
        benchmarks = {}
        
        # Determine industry (default to "default" if not specified)
        company_info = financial_data.get("company_info", {})
        industry = company_info.get("industry", "default") if isinstance(company_info, dict) else "default"
        
        # Get industry benchmarks (use default if specific industry not available)
        industry_benchmarks = self.INDUSTRY_BENCHMARKS.get(
            industry.lower() if industry else "default",
            self.INDUSTRY_BENCHMARKS["default"]
        )
        
        # Compare each ratio against benchmarks
        for ratio_name, ratio_data in ratios.items():
            if ratio_name in industry_benchmarks:
                ratio_value = ratio_data["value"]
                benchmark = industry_benchmarks[ratio_name]
                
                # Determine performance level
                performance = self._assess_performance(ratio_name, ratio_value, benchmark)
                
                benchmarks[ratio_name] = {
                    "value": ratio_value,
                    "benchmark_good": benchmark["good"],
                    "benchmark_acceptable": benchmark["acceptable"],
                    "benchmark_poor": benchmark["poor"],
                    "performance": performance,
                    "comparison": self._generate_benchmark_comparison(
                        ratio_name, ratio_value, benchmark, performance
                    )
                }
        
        return benchmarks
    
    async def _generate_summary(
        self,
        ratios: Dict[str, Any],
        trends: Dict[str, Any],
        benchmarks: Dict[str, Any],
        financial_data: Dict[str, Any]
    ) -> str:
        """
        Generate AI-powered analysis summary using OpenAI.
        
        Args:
            ratios: Calculated ratios
            trends: Trend analysis
            benchmarks: Benchmark comparisons
            financial_data: Original financial data
        
        Returns:
            Comprehensive analysis summary text
        """
        # Build prompt for OpenAI
        prompt = self._build_summary_prompt(ratios, trends, benchmarks, financial_data)
        
        try:
            response = await self.openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a financial analyst expert. Provide clear, concise analysis of financial data for credit decision-making."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # Low temperature for consistent analysis
                max_tokens=1000
            )
            
            summary = response.choices[0].message.content
            return summary
        
        except Exception as e:
            # Fallback to rule-based summary if OpenAI fails
            return self._generate_fallback_summary(ratios, trends, benchmarks)
    
    def _build_summary_prompt(
        self,
        ratios: Dict[str, Any],
        trends: Dict[str, Any],
        benchmarks: Dict[str, Any],
        financial_data: Dict[str, Any]
    ) -> str:
        """Build the prompt for AI summary generation."""
        company_info = financial_data.get("company_info", {})
        company_name = company_info.get("company_name", "the company") if isinstance(company_info, dict) else "the company"
        
        prompt = f"""Analyze the following financial data for {company_name} and provide a comprehensive summary for credit decision-making.

**Financial Ratios:**
"""
        
        for ratio_name, ratio_data in ratios.items():
            prompt += f"- {ratio_data.get('definition', ratio_name)}: {ratio_data['formatted_value']}\n"
        
        prompt += "\n**Trends:**\n"
        for metric_name, trend_data in trends.items():
            prompt += f"- {metric_name.replace('_', ' ').title()}: {trend_data['trend_direction']} trend"
            if trend_data.get('cagr'):
                prompt += f" (CAGR: {trend_data['cagr']:.2f}%)"
            prompt += "\n"
        
        prompt += "\n**Industry Benchmark Comparisons:**\n"
        for ratio_name, benchmark_data in benchmarks.items():
            prompt += f"- {ratio_name.replace('_', ' ').title()}: {benchmark_data['performance']}\n"
        
        prompt += """
Please provide:
1. Overall financial health assessment (2-3 sentences)
2. Key strengths (2-3 bullet points)
3. Key concerns or risks (2-3 bullet points)
4. Trend analysis summary (1-2 sentences)

Keep the analysis concise, professional, and focused on credit risk assessment.
"""
        
        return prompt
    
    def _generate_fallback_summary(
        self,
        ratios: Dict[str, Any],
        trends: Dict[str, Any],
        benchmarks: Dict[str, Any]
    ) -> str:
        """Generate a rule-based summary as fallback."""
        summary_parts = []
        
        # Assess overall financial health based on benchmarks
        good_count = sum(1 for b in benchmarks.values() if b["performance"] == "good")
        total_count = len(benchmarks)
        
        if total_count > 0:
            health_pct = (good_count / total_count) * 100
            if health_pct >= 70:
                summary_parts.append("The company demonstrates strong financial health with most ratios performing well against industry benchmarks.")
            elif health_pct >= 40:
                summary_parts.append("The company shows moderate financial health with mixed performance across key ratios.")
            else:
                summary_parts.append("The company exhibits concerning financial health with several ratios underperforming industry benchmarks.")
        
        # Summarize trends
        positive_trends = sum(1 for t in trends.values() if t["trend_direction"] in ["increasing", "stable"])
        if positive_trends > len(trends) / 2:
            summary_parts.append("Historical trends show positive or stable growth in key financial metrics.")
        else:
            summary_parts.append("Historical trends indicate declining performance in several key metrics.")
        
        # Highlight specific concerns
        concerns = []
        for ratio_name, benchmark_data in benchmarks.items():
            if benchmark_data["performance"] == "poor":
                concerns.append(f"weak {ratio_name.replace('_', ' ')}")
        
        if concerns:
            summary_parts.append(f"Key concerns include: {', '.join(concerns)}.")
        
        return " ".join(summary_parts)
    
    def _get_metric_definitions(
        self,
        ratios: Dict[str, Any],
        trends: Dict[str, Any]
    ) -> Dict[str, Dict[str, str]]:
        """
        Get definitions for all calculated metrics.
        
        Args:
            ratios: Calculated ratios
            trends: Trend analysis
        
        Returns:
            Dictionary mapping metric names to their definitions
        
        Requirements: 4.5
        """
        definitions = {}
        
        # Add ratio definitions
        for ratio_name in ratios.keys():
            if ratio_name in self.METRIC_DEFINITIONS:
                definitions[ratio_name] = self.METRIC_DEFINITIONS[ratio_name]
        
        # Add trend metric definitions
        trend_definitions = {
            "growth_rate": {
                "name": "Year-over-Year Growth Rate",
                "formula": "((Current Year - Previous Year) / Previous Year) × 100",
                "description": "Measures the percentage change in a metric from one year to the next.",
                "interpretation": "Positive growth rates indicate increasing values, while negative rates indicate decline."
            },
            "cagr": {
                "name": "Compound Annual Growth Rate (CAGR)",
                "formula": "((Final Value / Initial Value)^(1 / Number of Years) - 1) × 100",
                "description": "Measures the mean annual growth rate over a specified period longer than one year.",
                "interpretation": "Provides a smoothed annual growth rate that accounts for compounding effects."
            },
            "trend_direction": {
                "name": "Trend Direction",
                "formula": "Statistical analysis of time-series data",
                "description": "Classifies the overall direction of a metric over time as increasing, decreasing, stable, or volatile.",
                "interpretation": "Helps identify long-term patterns and trajectory of financial performance."
            }
        }
        
        for metric_name in trends.keys():
            definitions[f"{metric_name}_trend"] = trend_definitions["trend_direction"]
            definitions[f"{metric_name}_growth"] = trend_definitions["growth_rate"]
            if trends[metric_name].get("cagr") is not None:
                definitions[f"{metric_name}_cagr"] = trend_definitions["cagr"]
        
        return definitions
    
    def _format_ratio_value(self, ratio_name: str, value: float) -> str:
        """Format ratio value for display."""
        # Ratios that are typically shown as percentages
        percentage_ratios = ["net_profit_margin", "roe", "roa"]
        
        if ratio_name in percentage_ratios:
            return f"{value * 100:.2f}%"
        else:
            return f"{value:.2f}"
    
    def _assess_performance(
        self,
        ratio_name: str,
        value: float,
        benchmark: Dict[str, float]
    ) -> str:
        """
        Assess performance level based on benchmark comparison.
        
        Args:
            ratio_name: Name of the ratio
            value: Calculated ratio value
            benchmark: Benchmark thresholds
        
        Returns:
            Performance level: "good", "acceptable", or "poor"
        """
        # For debt ratios, lower is better
        inverse_ratios = ["debt_to_equity", "debt_ratio"]
        
        if ratio_name in inverse_ratios:
            if value <= benchmark["good"]:
                return "good"
            elif value <= benchmark["acceptable"]:
                return "acceptable"
            else:
                return "poor"
        else:
            # For most ratios, higher is better
            if value >= benchmark["good"]:
                return "good"
            elif value >= benchmark["acceptable"]:
                return "acceptable"
            else:
                return "poor"
    
    def _generate_benchmark_comparison(
        self,
        ratio_name: str,
        value: float,
        benchmark: Dict[str, float],
        performance: str
    ) -> str:
        """Generate human-readable benchmark comparison text."""
        formatted_value = self._format_ratio_value(ratio_name, value)
        
        if performance == "good":
            return f"{formatted_value} exceeds industry benchmarks, indicating strong performance."
        elif performance == "acceptable":
            return f"{formatted_value} meets acceptable industry standards."
        else:
            return f"{formatted_value} falls below industry benchmarks, indicating potential concern."
    
    def _interpret_trend(
        self,
        metric_name: str,
        trend_direction: TrendDirection,
        cagr: Optional[float]
    ) -> str:
        """Generate interpretation of trend analysis."""
        metric_display = metric_name.replace("_", " ").title()
        
        if trend_direction == TrendDirection.INCREASING:
            interpretation = f"{metric_display} shows a positive upward trend"
            if cagr:
                interpretation += f" with a compound annual growth rate of {cagr:.2f}%"
            interpretation += ", indicating improving performance."
        elif trend_direction == TrendDirection.DECREASING:
            interpretation = f"{metric_display} shows a declining trend"
            if cagr:
                interpretation += f" with a compound annual decline of {abs(cagr):.2f}%"
            interpretation += ", which may indicate deteriorating performance."
        elif trend_direction == TrendDirection.STABLE:
            interpretation = f"{metric_display} remains relatively stable over the period, showing consistent performance."
        elif trend_direction == TrendDirection.VOLATILE:
            interpretation = f"{metric_display} exhibits high volatility with significant fluctuations, indicating inconsistent performance."
        else:
            interpretation = f"Insufficient data to determine trend for {metric_display}."
        
        return interpretation
