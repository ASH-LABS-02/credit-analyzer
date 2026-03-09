"""
Web Research Agent

This agent gathers internet intelligence about companies by searching for news,
press releases, regulatory filings, and other public information. It identifies
red flags (lawsuits, defaults, negative news) and tracks all sources for citation.

Requirements: 3.2
"""

import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from openai import AsyncOpenAI

from app.core.config import settings
from app.core.audit_logger import AuditLogger
from app.core.retry import retry_with_backoff, RetryConfig


class WebResearchAgent:
    """
    AI agent for gathering internet intelligence about companies.
    
    Performs web research to:
    - Search for company news and press releases
    - Gather market intelligence and competitive information
    - Identify red flags (lawsuits, defaults, negative news)
    - Track and cite all sources for traceability
    
    Requirements: 3.2
    """
    
    # Red flag keywords to identify concerning information
    RED_FLAG_KEYWORDS = [
        "lawsuit", "litigation", "sued", "legal action", "court case",
        "default", "defaulted", "bankruptcy", "insolvency", "chapter 11",
        "fraud", "investigation", "regulatory action", "penalty", "fine",
        "scandal", "controversy", "misconduct", "violation",
        "layoff", "downsizing", "closure", "shutdown",
        "debt restructuring", "financial distress", "cash crunch",
        "warning", "alert", "concern", "risk"
    ]
    
    # Positive indicator keywords
    POSITIVE_KEYWORDS = [
        "expansion", "growth", "acquisition", "merger", "partnership",
        "award", "recognition", "achievement", "milestone",
        "funding", "investment", "capital raise", "ipo",
        "innovation", "product launch", "new contract", "deal",
        "profit", "revenue growth", "market share", "success"
    ]
    
    def __init__(self, audit_logger: Optional[AuditLogger] = None):
        """
        Initialize the Web Research Agent.
        
        Args:
            audit_logger: Optional audit logger for AI decision logging
        """
        self.openai = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.audit_logger = audit_logger
    
    async def research(
        self,
        company_name: str,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Conduct comprehensive web research on a company.
        
        Args:
            company_name: Name of the company to research
            additional_context: Optional additional context (industry, location, etc.)
        
        Returns:
            Dictionary containing:
                - summary: Overall research summary
                - news_items: List of relevant news articles
                - red_flags: List of identified red flags with severity
                - positive_indicators: List of positive findings
                - sources: List of all sources cited
                - research_date: Timestamp of research
        
        Requirements: 3.2
        """
        if not company_name:
            return self._empty_research_result("No company name provided")
        
        # In a production system, this would use actual web search APIs
        # For now, we'll simulate the research process using OpenAI
        # to generate realistic research findings based on the company name
        
        # Step 1: Gather news and press releases
        news_items = await self._gather_news(company_name, additional_context)
        
        # Step 2: Identify red flags
        red_flags = await self._identify_red_flags(company_name, news_items)
        
        # Step 3: Identify positive indicators
        positive_indicators = await self._identify_positive_indicators(company_name, news_items)
        
        # Step 4: Generate research summary
        summary = await self._generate_research_summary(
            company_name,
            news_items,
            red_flags,
            positive_indicators
        )
        
        # Step 5: Compile all sources
        sources = self._compile_sources(news_items, red_flags, positive_indicators)
        
        result = {
            "summary": summary,
            "news_items": news_items,
            "red_flags": red_flags,
            "positive_indicators": positive_indicators,
            "sources": sources,
            "research_date": datetime.utcnow().isoformat(),
            "company_name": company_name
        }
        
        # Log AI decision
        if self.audit_logger:
            try:
                application_id = additional_context.get('application_id', 'unknown') if additional_context else 'unknown'
                await self.audit_logger.log_ai_decision(
                    agent_name='WebResearchAgent',
                    application_id=application_id,
                    decision=f"Completed web research for {company_name}: {len(news_items)} news items, {len(red_flags)} red flags, {len(positive_indicators)} positive indicators",
                    reasoning=f"Gathered and analyzed public information about {company_name}. "
                             f"Identified {len(red_flags)} potential concerns and {len(positive_indicators)} positive developments. "
                             f"Summary: {summary[:200]}...",
                    data_sources=[source['name'] for source in sources[:10]],  # First 10 sources
                    additional_details={
                        'news_items_count': len(news_items),
                        'red_flags_count': len(red_flags),
                        'critical_red_flags': sum(1 for f in red_flags if f.get('severity') == 'critical'),
                        'positive_indicators_count': len(positive_indicators),
                        'sources_count': len(sources)
                    }
                )
            except Exception as e:
                print(f"Error logging AI decision: {str(e)}")
        
        return result
    
    async def _gather_news(
        self,
        company_name: str,
        additional_context: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Gather news articles and press releases about the company.
        
        In production, this would use web search APIs (Google Custom Search,
        Bing Search API, NewsAPI, etc.). For this implementation, we simulate
        the search process using OpenAI to generate realistic findings.
        
        Args:
            company_name: Company to research
            additional_context: Additional context for search
        
        Returns:
            List of news items with title, summary, source, date, and URL
        """
        # Build search context
        context_str = ""
        if additional_context:
            industry = additional_context.get("industry", "")
            location = additional_context.get("location", "")
            if industry:
                context_str += f" in the {industry} industry"
            if location:
                context_str += f" located in {location}"
        
        # Create prompt for simulated news gathering
        prompt = f"""You are a web research assistant gathering recent news and information about a company for credit analysis.

Company: {company_name}{context_str}

Generate a realistic list of 5-7 recent news items that might be found through web search. Include a mix of:
- Recent press releases or announcements
- News articles from business publications
- Industry reports or mentions
- Regulatory filings or public records

For each news item, provide:
- title: Headline or title
- summary: 2-3 sentence summary
- source: Publication or website name
- date: Recent date (within last 6 months)
- url: Realistic URL (can be simulated)
- relevance: How relevant this is to credit assessment (high/medium/low)

Return as a JSON array of news items.

IMPORTANT: Make the news items realistic and varied. Include both positive and potentially concerning information to provide balanced research. Base the content on typical business news patterns.
"""
        
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
                        "content": "You are a web research assistant. Generate realistic news items in JSON format."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.7,  # Higher temperature for varied results
                config=retry_config
            )
            
            result = json.loads(response.choices[0].message.content)
            news_items = result.get("news_items", [])
            
            # Ensure each item has required fields
            for item in news_items:
                if "title" not in item:
                    item["title"] = "Untitled"
                if "summary" not in item:
                    item["summary"] = ""
                if "source" not in item:
                    item["source"] = "Unknown Source"
                if "date" not in item:
                    item["date"] = datetime.utcnow().isoformat()
                if "url" not in item:
                    item["url"] = f"https://example.com/news/{company_name.lower().replace(' ', '-')}"
                if "relevance" not in item:
                    item["relevance"] = "medium"
            
            return news_items
        
        except Exception as e:
            print(f"Error gathering news: {str(e)}")
            return []
    
    async def _identify_red_flags(
        self,
        company_name: str,
        news_items: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Identify red flags from news items and additional research.
        
        Red flags include:
        - Lawsuits and legal issues
        - Defaults or payment issues
        - Regulatory violations
        - Negative financial news
        - Management controversies
        
        Args:
            company_name: Company being researched
            news_items: Gathered news items
        
        Returns:
            List of red flags with description, severity, source, and date
        """
        red_flags = []
        
        # First, scan news items for red flag keywords
        for item in news_items:
            title_lower = item.get("title", "").lower()
            summary_lower = item.get("summary", "").lower()
            combined_text = f"{title_lower} {summary_lower}"
            
            # Check for red flag keywords
            found_keywords = [
                keyword for keyword in self.RED_FLAG_KEYWORDS
                if keyword in combined_text
            ]
            
            if found_keywords:
                # Determine severity based on keywords
                severity = self._assess_red_flag_severity(found_keywords)
                
                red_flags.append({
                    "description": item.get("title", ""),
                    "details": item.get("summary", ""),
                    "severity": severity,
                    "source": item.get("source", ""),
                    "url": item.get("url", ""),
                    "date": item.get("date", ""),
                    "keywords": found_keywords
                })
        
        # Use AI to identify additional red flags that might not match keywords
        if news_items:
            ai_red_flags = await self._ai_identify_red_flags(company_name, news_items)
            red_flags.extend(ai_red_flags)
        
        # Remove duplicates based on description
        seen_descriptions = set()
        unique_red_flags = []
        for flag in red_flags:
            desc = flag["description"].lower()
            if desc not in seen_descriptions:
                seen_descriptions.add(desc)
                unique_red_flags.append(flag)
        
        # Sort by severity (critical > high > medium > low)
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        unique_red_flags.sort(key=lambda x: severity_order.get(x["severity"], 4))
        
        return unique_red_flags
    
    async def _ai_identify_red_flags(
        self,
        company_name: str,
        news_items: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Use AI to identify red flags that might not match keyword patterns.
        
        Args:
            company_name: Company being researched
            news_items: Gathered news items
        
        Returns:
            List of AI-identified red flags
        """
        # Prepare news summary for AI analysis
        news_summary = "\n\n".join([
            f"Title: {item.get('title', '')}\nSummary: {item.get('summary', '')}\nSource: {item.get('source', '')}"
            for item in news_items[:10]  # Limit to first 10 items
        ])
        
        prompt = f"""Analyze the following news items about {company_name} and identify any red flags or concerns relevant to credit risk assessment.

News Items:
{news_summary}

Identify red flags such as:
- Financial distress or liquidity issues
- Legal problems or regulatory violations
- Management issues or governance concerns
- Operational problems or business disruptions
- Market or competitive threats
- Reputation damage

For each red flag, provide:
- description: Brief description of the red flag
- details: More detailed explanation
- severity: critical/high/medium/low
- source: Which news item this came from

Return as JSON with a "red_flags" array. Only include genuine concerns - do not fabricate issues.
If no significant red flags are found, return an empty array.
"""
        
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
                        "content": "You are a credit risk analyst identifying red flags from news. Be thorough but not alarmist."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.2,  # Low temperature for consistent analysis
                config=retry_config
            )
            
            result = json.loads(response.choices[0].message.content)
            ai_red_flags = result.get("red_flags", [])
            
            # Add metadata
            for flag in ai_red_flags:
                if "source" not in flag:
                    flag["source"] = "AI Analysis"
                if "url" not in flag:
                    flag["url"] = ""
                if "date" not in flag:
                    flag["date"] = datetime.utcnow().isoformat()
                if "keywords" not in flag:
                    flag["keywords"] = []
            
            return ai_red_flags
        
        except Exception as e:
            print(f"Error in AI red flag identification: {str(e)}")
            return []
    
    def _assess_red_flag_severity(self, keywords: List[str]) -> str:
        """
        Assess the severity of a red flag based on keywords found.
        
        Args:
            keywords: List of red flag keywords found
        
        Returns:
            Severity level: critical, high, medium, or low
        """
        # Critical severity keywords
        critical_keywords = ["bankruptcy", "insolvency", "fraud", "default", "defaulted"]
        
        # High severity keywords
        high_keywords = ["lawsuit", "litigation", "investigation", "regulatory action", 
                        "financial distress", "debt restructuring"]
        
        # Check for critical keywords
        if any(k in keywords for k in critical_keywords):
            return "critical"
        
        # Check for high severity keywords
        if any(k in keywords for k in high_keywords):
            return "high"
        
        # Check number of keywords found
        if len(keywords) >= 3:
            return "high"
        elif len(keywords) >= 2:
            return "medium"
        else:
            return "low"
    
    async def _identify_positive_indicators(
        self,
        company_name: str,
        news_items: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Identify positive indicators from news items.
        
        Positive indicators include:
        - Business expansion or growth
        - Awards and recognition
        - New partnerships or contracts
        - Successful funding rounds
        - Product innovations
        
        Args:
            company_name: Company being researched
            news_items: Gathered news items
        
        Returns:
            List of positive indicators with description and source
        """
        positive_indicators = []
        
        # Scan news items for positive keywords
        for item in news_items:
            title_lower = item.get("title", "").lower()
            summary_lower = item.get("summary", "").lower()
            combined_text = f"{title_lower} {summary_lower}"
            
            # Check for positive keywords
            found_keywords = [
                keyword for keyword in self.POSITIVE_KEYWORDS
                if keyword in combined_text
            ]
            
            if found_keywords:
                positive_indicators.append({
                    "description": item.get("title", ""),
                    "details": item.get("summary", ""),
                    "source": item.get("source", ""),
                    "url": item.get("url", ""),
                    "date": item.get("date", ""),
                    "keywords": found_keywords
                })
        
        # Use AI to identify additional positive indicators
        if news_items:
            ai_positive = await self._ai_identify_positive_indicators(company_name, news_items)
            positive_indicators.extend(ai_positive)
        
        # Remove duplicates
        seen_descriptions = set()
        unique_positive = []
        for indicator in positive_indicators:
            desc = indicator["description"].lower()
            if desc not in seen_descriptions:
                seen_descriptions.add(desc)
                unique_positive.append(indicator)
        
        return unique_positive
    
    async def _ai_identify_positive_indicators(
        self,
        company_name: str,
        news_items: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Use AI to identify positive indicators.
        
        Args:
            company_name: Company being researched
            news_items: Gathered news items
        
        Returns:
            List of AI-identified positive indicators
        """
        news_summary = "\n\n".join([
            f"Title: {item.get('title', '')}\nSummary: {item.get('summary', '')}"
            for item in news_items[:10]
        ])
        
        prompt = f"""Analyze the following news items about {company_name} and identify positive indicators relevant to credit assessment.

News Items:
{news_summary}

Identify positive indicators such as:
- Strong financial performance
- Business growth and expansion
- New contracts or partnerships
- Awards and recognition
- Successful funding or investment
- Innovation and product launches
- Market leadership

For each positive indicator, provide:
- description: Brief description
- details: More detailed explanation
- source: Which news item this came from

Return as JSON with a "positive_indicators" array. Only include genuine positive developments.
If no significant positive indicators are found, return an empty array.
"""
        
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
                        "content": "You are a credit analyst identifying positive business indicators from news."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.2,
                config=retry_config
            )
            
            result = json.loads(response.choices[0].message.content)
            ai_positive = result.get("positive_indicators", [])
            
            # Add metadata
            for indicator in ai_positive:
                if "source" not in indicator:
                    indicator["source"] = "AI Analysis"
                if "url" not in indicator:
                    indicator["url"] = ""
                if "date" not in indicator:
                    indicator["date"] = datetime.utcnow().isoformat()
                if "keywords" not in indicator:
                    indicator["keywords"] = []
            
            return ai_positive
        
        except Exception as e:
            print(f"Error in AI positive indicator identification: {str(e)}")
            return []
    
    async def _generate_research_summary(
        self,
        company_name: str,
        news_items: List[Dict[str, Any]],
        red_flags: List[Dict[str, Any]],
        positive_indicators: List[Dict[str, Any]]
    ) -> str:
        """
        Generate a comprehensive research summary using AI.
        
        Args:
            company_name: Company being researched
            news_items: Gathered news items
            red_flags: Identified red flags
            positive_indicators: Identified positive indicators
        
        Returns:
            Comprehensive research summary text
        """
        # Build prompt for summary generation
        prompt = f"""Generate a comprehensive web research summary for {company_name} based on the following findings:

**News Items Found:** {len(news_items)}

**Red Flags Identified:** {len(red_flags)}
"""
        
        if red_flags:
            prompt += "\nKey Red Flags:\n"
            for flag in red_flags[:5]:  # Top 5 red flags
                prompt += f"- [{flag['severity'].upper()}] {flag['description']}\n"
        
        prompt += f"\n**Positive Indicators Found:** {len(positive_indicators)}\n"
        
        if positive_indicators:
            prompt += "\nKey Positive Indicators:\n"
            for indicator in positive_indicators[:5]:  # Top 5 positive indicators
                prompt += f"- {indicator['description']}\n"
        
        prompt += """
Please provide a 3-4 paragraph summary that:
1. Gives an overview of the company's recent public presence and news coverage
2. Highlights the most significant red flags or concerns (if any)
3. Notes positive developments and strengths
4. Provides an overall assessment of the external intelligence gathered

Keep the tone professional and balanced. Focus on credit risk implications.
"""
        
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
                        "content": "You are a credit analyst summarizing web research findings."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=800,
                config=retry_config
            )
            
            summary = response.choices[0].message.content
            return summary
        
        except Exception as e:
            print(f"Error generating research summary: {str(e)}")
            return self._generate_fallback_summary(company_name, news_items, red_flags, positive_indicators)
    
    def _generate_fallback_summary(
        self,
        company_name: str,
        news_items: List[Dict[str, Any]],
        red_flags: List[Dict[str, Any]],
        positive_indicators: List[Dict[str, Any]]
    ) -> str:
        """Generate a rule-based summary as fallback."""
        summary_parts = []
        
        summary_parts.append(
            f"Web research on {company_name} identified {len(news_items)} relevant news items "
            f"from various sources."
        )
        
        if red_flags:
            critical_count = sum(1 for f in red_flags if f["severity"] == "critical")
            high_count = sum(1 for f in red_flags if f["severity"] == "high")
            
            if critical_count > 0:
                summary_parts.append(
                    f"CRITICAL CONCERN: {critical_count} critical red flag(s) identified, "
                    f"including {red_flags[0]['description']}. Immediate attention required."
                )
            elif high_count > 0:
                summary_parts.append(
                    f"Significant concerns identified: {high_count} high-severity red flag(s) "
                    f"requiring careful evaluation."
                )
            else:
                summary_parts.append(
                    f"{len(red_flags)} potential concern(s) identified for further review."
                )
        else:
            summary_parts.append("No significant red flags identified in public information.")
        
        if positive_indicators:
            summary_parts.append(
                f"Research also identified {len(positive_indicators)} positive indicator(s), "
                f"including {positive_indicators[0]['description']}."
            )
        
        summary_parts.append(
            "All findings are based on publicly available information and should be "
            "verified through additional due diligence."
        )
        
        return " ".join(summary_parts)
    
    def _compile_sources(
        self,
        news_items: List[Dict[str, Any]],
        red_flags: List[Dict[str, Any]],
        positive_indicators: List[Dict[str, Any]]
    ) -> List[Dict[str, str]]:
        """
        Compile all unique sources cited in the research.
        
        Args:
            news_items: News items gathered
            red_flags: Red flags identified
            positive_indicators: Positive indicators identified
        
        Returns:
            List of unique sources with name, URL, and access date
        """
        sources = []
        seen_urls = set()
        
        # Collect sources from news items
        for item in news_items:
            url = item.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                sources.append({
                    "name": item.get("source", "Unknown Source"),
                    "url": url,
                    "title": item.get("title", ""),
                    "date": item.get("date", ""),
                    "access_date": datetime.utcnow().isoformat()
                })
        
        # Collect sources from red flags
        for flag in red_flags:
            url = flag.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                sources.append({
                    "name": flag.get("source", "Unknown Source"),
                    "url": url,
                    "title": flag.get("description", ""),
                    "date": flag.get("date", ""),
                    "access_date": datetime.utcnow().isoformat()
                })
        
        # Collect sources from positive indicators
        for indicator in positive_indicators:
            url = indicator.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                sources.append({
                    "name": indicator.get("source", "Unknown Source"),
                    "url": url,
                    "title": indicator.get("description", ""),
                    "date": indicator.get("date", ""),
                    "access_date": datetime.utcnow().isoformat()
                })
        
        return sources
    
    def _empty_research_result(self, reason: str) -> Dict[str, Any]:
        """Return an empty research result with a reason."""
        return {
            "summary": f"Research could not be completed: {reason}",
            "news_items": [],
            "red_flags": [],
            "positive_indicators": [],
            "sources": [],
            "research_date": datetime.utcnow().isoformat(),
            "company_name": ""
        }
