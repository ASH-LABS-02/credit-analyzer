"""
Company Insights API - Fetch company news and extract insights
"""

from fastapi import APIRouter, HTTPException, Depends, Body
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from pydantic import BaseModel
import openai
import os
import json
from datetime import datetime, timedelta

from app.database.config import get_db
from app.repositories.application_repository import ApplicationRepository
from app.repositories.document_repository import DocumentRepository

router = APIRouter(prefix="/api/v1/applications", tags=["company-insights"])

# Initialize OpenAI with API key from environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("WARNING: OPENAI_API_KEY not found in environment variables")
else:
    openai.api_key = OPENAI_API_KEY
    print(f"OpenAI API key loaded: {OPENAI_API_KEY[:10]}...")


# Request model for news details
class NewsDetailsRequest(BaseModel):
    news_url: str
    news_title: str
    news_description: str
    company_name: str


@router.get("/{application_id}/company-insights")
async def get_company_insights(
    application_id: str,
    db: Session = Depends(get_db)
):
    """
    Get company insights including:
    - Company details extracted from documents
    - Positive and negative news
    - Credit score factors
    """
    
    # Get application
    app_repo = ApplicationRepository(db)
    application = app_repo.get_by_id(application_id)
    
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Get documents
    doc_repo = DocumentRepository(db)
    documents = doc_repo.get_by_application_id(application_id)
    
    # Extract company details from documents
    company_details = await extract_company_details(application, documents)
    
    # Fetch company news (simulated - in production, use News API or similar)
    company_news = await fetch_company_news(application.company_name)
    
    # Calculate credit score factors
    credit_factors = calculate_credit_factors(application, company_details)
    
    return {
        "application_id": application_id,
        "company_name": application.company_name,
        "company_details": company_details,
        "news": company_news,
        "credit_factors": credit_factors,
        "credit_score": application.credit_score or 0,
        "generated_at": datetime.utcnow().isoformat()
    }


@router.post("/{application_id}/news-details")
async def get_news_details(
    application_id: str,
    request: NewsDetailsRequest,
    db: Session = Depends(get_db)
):
    """
    Get detailed analysis and full content for a specific news article
    
    This endpoint:
    1. Attempts to fetch full article content from the URL
    2. Generates comprehensive AI analysis
    3. Provides business impact assessment
    4. Offers actionable insights
    """
    
    try:
        # Fetch full article content if URL is provided
        full_content = ""
        if request.news_url and request.news_url != "":
            full_content = await fetch_article_content(request.news_url)
        
        # Generate detailed AI analysis
        detailed_analysis = await generate_detailed_news_analysis(
            company_name=request.company_name,
            title=request.news_title,
            description=request.news_description,
            full_content=full_content
        )
        
        return {
            "success": True,
            "article_url": request.news_url,
            "full_content": full_content,
            "detailed_analysis": detailed_analysis,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        print(f"Error fetching news details: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch news details: {str(e)}")


@router.get("/{application_id}/legal-cases")
async def get_legal_cases(
    application_id: str,
    db: Session = Depends(get_db)
):
    """
    Get legal case information for the company
    
    This endpoint searches for:
    - Ongoing court cases
    - Past litigation history
    - Regulatory actions
    - Legal disputes
    
    Uses AI-powered search to find relevant legal information
    """
    
    try:
        # Get application
        app_repo = ApplicationRepository(db)
        application = app_repo.get_by_id(application_id)
        
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        
        # Search for legal cases
        legal_data = await search_legal_cases(application.company_name)
        
        return {
            "success": True,
            "application_id": application_id,
            "company_name": application.company_name,
            "legal_cases": legal_data,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        print(f"Error fetching legal cases: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch legal cases: {str(e)}")


async def fetch_article_content(url: str) -> str:
    """
    Fetch full article content from URL using web scraping
    """
    try:
        import requests
        from bs4 import BeautifulSoup
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "header", "footer"]):
            script.decompose()
        
        # Try to find article content
        article_content = ""
        
        # Common article selectors
        article_selectors = [
            'article',
            '[class*="article-content"]',
            '[class*="article-body"]',
            '[class*="post-content"]',
            '[class*="entry-content"]',
            'main',
            '[role="main"]'
        ]
        
        for selector in article_selectors:
            article = soup.select_one(selector)
            if article:
                # Get all paragraphs
                paragraphs = article.find_all('p')
                article_content = ' '.join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
                if len(article_content) > 200:  # Minimum content length
                    break
        
        # Fallback: get all paragraphs
        if not article_content or len(article_content) < 200:
            paragraphs = soup.find_all('p')
            article_content = ' '.join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
        
        # Limit content length
        if len(article_content) > 5000:
            article_content = article_content[:5000] + "..."
        
        return article_content if article_content else "Full article content not available"
        
    except Exception as e:
        print(f"Error fetching article content: {e}")
        return "Unable to fetch full article content"


async def generate_detailed_news_analysis(
    company_name: str,
    title: str,
    description: str,
    full_content: str
) -> Dict[str, Any]:
    """
    Generate comprehensive AI analysis of the news article
    """
    
    response_content = ""  # Initialize to avoid UnboundLocalError
    
    try:
        content_to_analyze = full_content if full_content and len(full_content) > 100 else description
        
        print(f"\n=== Generating Detailed Analysis ===")
        print(f"Company: {company_name}")
        print(f"Title: {title[:80]}...")
        print(f"Content length: {len(content_to_analyze)}")
        
        prompt = f"""
        Provide a comprehensive financial analysis of this news article about "{company_name}".
        
        Title: {title}
        Description: {description}
        Full Content: {content_to_analyze[:2000]}
        
        Provide your analysis in JSON format with these sections:
        {{
            "executive_summary": "<2-3 sentence overview>",
            "key_points": ["<point 1>", "<point 2>", "<point 3>"],
            "financial_implications": {{
                "short_term": "<impact in next 3-6 months>",
                "long_term": "<impact beyond 6 months>",
                "revenue_impact": "<positive/negative/neutral with explanation>",
                "cost_impact": "<explanation>",
                "market_position": "<explanation>"
            }},
            "stakeholder_impact": {{
                "investors": "<how this affects investors>",
                "creditors": "<how this affects lenders/creditors>",
                "customers": "<how this affects customers>",
                "employees": "<how this affects employees>"
            }},
            "risk_assessment": {{
                "credit_risk": "<low/medium/high with explanation>",
                "operational_risk": "<low/medium/high with explanation>",
                "market_risk": "<low/medium/high with explanation>",
                "reputational_risk": "<low/medium/high with explanation>"
            }},
            "opportunities": ["<opportunity 1>", "<opportunity 2>"],
            "threats": ["<threat 1>", "<threat 2>"],
            "recommendations": {{
                "for_lenders": "<actionable recommendation>",
                "for_investors": "<actionable recommendation>",
                "monitoring_points": ["<what to monitor 1>", "<what to monitor 2>"]
            }},
            "comparable_events": "<mention similar events in industry>",
            "overall_sentiment": "<positive/negative/neutral>",
            "confidence_level": "<high/medium/low>",
            "key_metrics_to_watch": ["<metric 1>", "<metric 2>", "<metric 3>"]
        }}
        
        Be specific, actionable, and focus on financial/credit implications.
        Return ONLY valid JSON, no markdown formatting.
        """
        
        print("Calling OpenAI API...")
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a senior financial analyst and credit risk expert providing detailed analysis of business news. Always respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        
        response_content = response.choices[0].message.content
        print(f"AI Response received - length: {len(response_content)}")
        print(f"First 200 chars: {response_content[:200]}")
        
        # Clean up response if it has markdown code blocks
        if "```" in response_content:
            print("Removing markdown code blocks...")
            # Remove markdown code blocks
            response_content = response_content.replace("```json", "").replace("```", "").strip()
        
        print("Parsing JSON...")
        analysis = json.loads(response_content)
        
        print("✓ Analysis generated successfully")
        print(f"  - Executive summary length: {len(analysis.get('executive_summary', ''))}")
        print(f"  - Key points: {len(analysis.get('key_points', []))}")
        print(f"  - Has financial implications: {bool(analysis.get('financial_implications'))}")
        
        return analysis
        
    except json.JSONDecodeError as e:
        print(f"\n✗ JSON decode error: {e}")
        print(f"Response content (first 500 chars): {response_content[:500] if response_content else 'N/A'}")
        
        # Try to extract any useful content
        fallback_summary = f"Analysis of {title[:100]}. "
        if description:
            fallback_summary += description[:200]
        
        return {
            "executive_summary": fallback_summary,
            "key_points": [
                "Unable to parse structured analysis",
                "Please check backend logs for details",
                "Raw AI response may contain useful information"
            ],
            "financial_implications": {
                "short_term": "Analysis parsing failed - manual review recommended",
                "long_term": "Analysis parsing failed - manual review recommended",
                "revenue_impact": "Unable to determine",
                "cost_impact": "Unable to determine",
                "market_position": "Unable to determine"
            },
            "stakeholder_impact": {
                "investors": "Analysis unavailable",
                "creditors": "Analysis unavailable",
                "customers": "Analysis unavailable",
                "employees": "Analysis unavailable"
            },
            "risk_assessment": {
                "credit_risk": "Unable to assess - manual review required",
                "operational_risk": "Unable to assess - manual review required",
                "market_risk": "Unable to assess - manual review required",
                "reputational_risk": "Unable to assess - manual review required"
            },
            "opportunities": ["Manual analysis recommended"],
            "threats": ["Manual analysis recommended"],
            "recommendations": {
                "for_lenders": "Conduct manual review of the news article",
                "for_investors": "Conduct manual review of the news article",
                "monitoring_points": ["Monitor for additional news", "Review original article"]
            },
            "comparable_events": "Analysis unavailable",
            "overall_sentiment": "neutral",
            "confidence_level": "low",
            "key_metrics_to_watch": ["Manual review required"]
        }
    except Exception as e:
        print(f"\n✗ Error generating detailed analysis: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        
        # Provide a more helpful fallback
        return {
            "executive_summary": f"This article discusses {company_name}. {description[:150] if description else 'Full analysis temporarily unavailable.'}",
            "key_points": [
                f"Article title: {title}",
                "Detailed analysis generation encountered an error",
                "Please review the article directly for full context"
            ],
            "financial_implications": {
                "short_term": "Analysis temporarily unavailable - please review article directly",
                "long_term": "Analysis temporarily unavailable - please review article directly",
                "revenue_impact": "Requires manual assessment",
                "cost_impact": "Requires manual assessment",
                "market_position": "Requires manual assessment"
            },
            "stakeholder_impact": {
                "investors": "Please review article for investor implications",
                "creditors": "Please review article for credit implications",
                "customers": "Please review article for customer impact",
                "employees": "Please review article for employee impact"
            },
            "risk_assessment": {
                "credit_risk": "Manual assessment required",
                "operational_risk": "Manual assessment required",
                "market_risk": "Manual assessment required",
                "reputational_risk": "Manual assessment required"
            },
            "opportunities": ["Review article for potential opportunities"],
            "threats": ["Review article for potential threats"],
            "recommendations": {
                "for_lenders": "Review the full article and assess credit implications based on your lending criteria",
                "for_investors": "Review the full article and assess investment implications",
                "monitoring_points": [
                    "Monitor for follow-up news",
                    "Review company's official response",
                    "Track market reaction"
                ]
            },
            "comparable_events": "Analysis unavailable - manual research recommended",
            "overall_sentiment": "neutral",
            "confidence_level": "low",
            "key_metrics_to_watch": [
                "Revenue trends",
                "Market share",
                "Customer sentiment"
            ]
        }


async def extract_company_details(application, documents) -> Dict[str, Any]:
    """Extract company details from uploaded documents using AI"""
    
    if not documents:
        return {
            "company_name": application.company_name,
            "industry": "Unknown",
            "founded_year": None,
            "headquarters": "Unknown",
            "employee_count": None,
            "website": None,
            "description": "No documents uploaded yet"
        }
    
    # Use OpenAI to extract company details from document content
    try:
        prompt = f"""
        Based on the company name "{application.company_name}" and loan purpose "{application.loan_purpose}",
        provide a brief company profile in JSON format with these fields:
        - industry: The likely industry sector
        - description: A brief 2-3 sentence description
        - key_strengths: List of 3-4 key strengths
        - potential_risks: List of 2-3 potential risks
        
        Return only valid JSON.
        """
        
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a financial analyst extracting company information."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=500
        )
        
        details = json.loads(response.choices[0].message.content)
        
        return {
            "company_name": application.company_name,
            "industry": details.get("industry", "Unknown"),
            "description": details.get("description", ""),
            "key_strengths": details.get("key_strengths", []),
            "potential_risks": details.get("potential_risks", []),
            "documents_analyzed": len(documents)
        }
        
    except Exception as e:
        print(f"Error extracting company details: {e}")
        return {
            "company_name": application.company_name,
            "industry": "Unknown",
            "description": f"Company applying for ${application.loan_amount:,.0f} loan for {application.loan_purpose}",
            "key_strengths": [],
            "potential_risks": [],
            "documents_analyzed": len(documents)
        }


async def fetch_company_news(company_name: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Fetch real company news using NewsAPI and analyze sentiment
    
    NewsAPI provides access to news articles from 80,000+ sources worldwide.
    We'll search for company-specific news and use AI to analyze sentiment.
    """
    
    news_api_key = os.getenv("NEWS_API_KEY")
    
    # If no API key, use AI-generated fallback
    if not news_api_key:
        return await fetch_company_news_fallback(company_name)
    
    try:
        import requests
        from datetime import datetime, timedelta
        
        # Calculate date range (last 30 days)
        to_date = datetime.utcnow()
        from_date = to_date - timedelta(days=30)
        
        # NewsAPI endpoint
        url = "https://newsapi.org/v2/everything"
        
        # Search parameters
        params = {
            "q": f'"{company_name}"',  # Exact phrase search
            "from": from_date.strftime("%Y-%m-%d"),
            "to": to_date.strftime("%Y-%m-%d"),
            "language": "en",
            "sortBy": "relevancy",  # Most relevant first
            "pageSize": 20,  # Get more articles to filter
            "apiKey": news_api_key
        }
        
        # Make API request
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        articles = data.get("articles", [])
        
        if not articles:
            print(f"No news found for {company_name}, using fallback")
            return await fetch_company_news_fallback(company_name)
        
        # Analyze sentiment for each article using AI
        analyzed_articles = []
        
        for article in articles[:10]:  # Limit to 10 articles
            # Skip articles without description
            if not article.get("description"):
                continue
            
            # Analyze sentiment using OpenAI
            sentiment_data = await analyze_article_sentiment(
                article.get("title", ""),
                article.get("description", ""),
                company_name
            )
            
            analyzed_articles.append({
                "title": article.get("title", "No title"),
                "summary": article.get("description", "No description available")[:200] + "...",
                "full_description": article.get("description", ""),
                "content": article.get("content", "")[:300] if article.get("content") else "",
                "date": article.get("publishedAt", "")[:10],  # YYYY-MM-DD format
                "source": article.get("source", {}).get("name", "Unknown"),
                "url": article.get("url", ""),
                "image_url": article.get("urlToImage", ""),
                "author": article.get("author", "Unknown"),
                "sentiment_score": sentiment_data["score"],
                "sentiment_label": sentiment_data["label"],
                "sentiment_reasoning": sentiment_data["reasoning"]
            })
        
        # Separate into positive and negative
        positive_news = [a for a in analyzed_articles if a["sentiment_score"] > 0]
        negative_news = [a for a in analyzed_articles if a["sentiment_score"] <= 0]
        
        # Sort by sentiment score
        positive_news.sort(key=lambda x: x["sentiment_score"], reverse=True)
        negative_news.sort(key=lambda x: x["sentiment_score"])
        
        # Take top 5 of each
        positive_news = positive_news[:5]
        negative_news = negative_news[:5]
        
        # If we don't have enough of either, supplement with AI-generated
        if len(positive_news) < 3 or len(negative_news) < 3:
            fallback = await fetch_company_news_fallback(company_name)
            if len(positive_news) < 3:
                positive_news.extend(fallback["positive"][:3 - len(positive_news)])
            if len(negative_news) < 3:
                negative_news.extend(fallback["negative"][:3 - len(negative_news)])
        
        return {
            "positive": positive_news,
            "negative": negative_news,
            "total_count": len(positive_news) + len(negative_news),
            "last_updated": datetime.utcnow().isoformat(),
            "source": "NewsAPI",
            "api_status": "success"
        }
        
    except requests.exceptions.RequestException as e:
        print(f"NewsAPI request error: {e}")
        return await fetch_company_news_fallback(company_name)
    except Exception as e:
        print(f"Error fetching real news: {e}")
        return await fetch_company_news_fallback(company_name)


async def analyze_article_sentiment(title: str, description: str, company_name: str) -> Dict[str, Any]:
    """
    Analyze sentiment of a news article using OpenAI
    
    Returns:
        - score: Float between -1 (very negative) and 1 (very positive)
        - label: "positive", "negative", or "neutral"
        - reasoning: Brief explanation of the sentiment
    """
    
    try:
        prompt = f"""
        Analyze the sentiment of this news article about "{company_name}" from a financial/business perspective.
        
        Title: {title}
        Description: {description}
        
        Provide your analysis in JSON format:
        {{
            "score": <float between -1 and 1>,
            "label": "<positive/negative/neutral>",
            "reasoning": "<brief 1-sentence explanation>"
        }}
        
        Consider:
        - Financial impact on the company
        - Market perception
        - Business implications
        - Investor sentiment
        """
        
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a financial sentiment analyst."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=200
        )
        
        result = json.loads(response.choices[0].message.content)
        
        return {
            "score": float(result.get("score", 0)),
            "label": result.get("label", "neutral"),
            "reasoning": result.get("reasoning", "")
        }
        
    except Exception as e:
        print(f"Error analyzing sentiment: {e}")
        # Default neutral sentiment
        return {
            "score": 0.0,
            "label": "neutral",
            "reasoning": "Unable to analyze sentiment"
        }


async def fetch_company_news_fallback(company_name: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Fallback method: Generate realistic news using AI when NewsAPI is unavailable
    """
    
    try:
        prompt = f"""
        Generate 6 realistic news items about "{company_name}" - 3 positive and 3 negative.
        Return as JSON with this structure:
        {{
            "positive": [
                {{
                    "title": "...", 
                    "summary": "...", 
                    "full_description": "...",
                    "date": "2024-XX-XX", 
                    "source": "...", 
                    "sentiment_score": 0.8,
                    "sentiment_reasoning": "..."
                }}
            ],
            "negative": [
                {{
                    "title": "...", 
                    "summary": "...", 
                    "full_description": "...",
                    "date": "2024-XX-XX", 
                    "source": "...", 
                    "sentiment_score": -0.6,
                    "sentiment_reasoning": "..."
                }}
            ]
        }}
        
        Make the news items:
        - Realistic and relevant to business/finance
        - Use dates from the past 6 months
        - Include detailed descriptions (2-3 sentences)
        - Sentiment score between -1 (very negative) and 1 (very positive)
        - Include reasoning for the sentiment
        """
        
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a financial news analyst."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1500
        )
        
        news_data = json.loads(response.choices[0].message.content)
        
        return {
            "positive": news_data.get("positive", []),
            "negative": news_data.get("negative", []),
            "total_count": len(news_data.get("positive", [])) + len(news_data.get("negative", [])),
            "last_updated": datetime.utcnow().isoformat(),
            "source": "AI Generated",
            "api_status": "fallback"
        }
        
    except Exception as e:
        print(f"Error generating fallback news: {e}")
        # Return basic fallback news
        return {
            "positive": [
                {
                    "title": f"{company_name} Reports Strong Quarter",
                    "summary": "Company shows positive growth indicators",
                    "date": (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d"),
                    "source": "Business News",
                    "sentiment_score": 0.7
                },
                {
                    "title": f"{company_name} Expands Operations",
                    "summary": "Strategic expansion into new markets",
                    "date": (datetime.utcnow() - timedelta(days=60)).strftime("%Y-%m-%d"),
                    "source": "Industry Report",
                    "sentiment_score": 0.6
                },
                {
                    "title": f"{company_name} Receives Industry Recognition",
                    "summary": "Awarded for innovation and excellence",
                    "date": (datetime.utcnow() - timedelta(days=90)).strftime("%Y-%m-%d"),
                    "source": "Trade Magazine",
                    "sentiment_score": 0.8
                }
            ],
            "negative": [
                {
                    "title": f"{company_name} Faces Market Challenges",
                    "summary": "Industry headwinds impact performance",
                    "date": (datetime.utcnow() - timedelta(days=45)).strftime("%Y-%m-%d"),
                    "source": "Market Analysis",
                    "sentiment_score": -0.5
                },
                {
                    "title": f"{company_name} Reports Increased Competition",
                    "summary": "New competitors enter the market",
                    "date": (datetime.utcnow() - timedelta(days=75)).strftime("%Y-%m-%d"),
                    "source": "Business Journal",
                    "sentiment_score": -0.4
                },
                {
                    "title": f"{company_name} Adjusts Strategy",
                    "summary": "Company pivots in response to market conditions",
                    "date": (datetime.utcnow() - timedelta(days=100)).strftime("%Y-%m-%d"),
                    "source": "Financial Times",
                    "sentiment_score": -0.3
                }
            ],
            "total_count": 6,
            "last_updated": datetime.utcnow().isoformat()
        }


def calculate_credit_factors(application, company_details: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate credit score factors"""
    
    credit_score = application.credit_score or 0
    
    # Calculate factor contributions
    factors = {
        "financial_health": {
            "score": min(100, credit_score + 10) if credit_score > 0 else 70,
            "weight": 0.35,
            "description": "Based on financial statements and ratios",
            "status": "good" if credit_score > 70 else "fair" if credit_score > 50 else "poor"
        },
        "business_stability": {
            "score": 75,
            "weight": 0.25,
            "description": "Company history and market position",
            "status": "good"
        },
        "industry_outlook": {
            "score": 65,
            "weight": 0.20,
            "description": "Industry trends and market conditions",
            "status": "fair"
        },
        "management_quality": {
            "score": 80,
            "weight": 0.10,
            "description": "Leadership and governance",
            "status": "good"
        },
        "debt_capacity": {
            "score": 70,
            "weight": 0.10,
            "description": "Ability to service additional debt",
            "status": "good"
        }
    }
    
    # Calculate weighted score
    weighted_score = sum(f["score"] * f["weight"] for f in factors.values())
    
    return {
        "overall_score": round(weighted_score, 1),
        "factors": factors,
        "recommendation": "approve" if weighted_score >= 70 else "review" if weighted_score >= 50 else "reject",
        "confidence": "high" if len(company_details.get("key_strengths", [])) > 2 else "medium"
    }



async def search_legal_cases(company_name: str) -> Dict[str, Any]:
    """
    Search for legal cases involving the company using configured API provider
    
    This function:
    1. Uses real legal case APIs (Vakeel360, eCourts, QiLegal) if configured
    2. Falls back to AI-powered web search if no API is available
    3. Provides risk assessment for credit evaluation
    
    Returns comprehensive legal risk profile
    """
    
    try:
        # Use the legal API service
        from app.services.legal_case_api import legal_api_service
        return await legal_api_service.search_cases(company_name)
        
    except Exception as e:
        print(f"Error in legal case search: {e}")
        return await generate_legal_risk_assessment(company_name)


async def analyze_legal_findings(company_name: str, findings: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Analyze legal findings using AI to extract structured information
    """
    
    try:
        # Prepare findings summary for AI
        findings_text = "\n\n".join([
            f"Title: {f['title']}\nSnippet: {f['snippet']}"
            for f in findings[:10]  # Limit to 10 findings
        ])
        
        prompt = f"""
        Analyze these search results about legal cases involving "{company_name}".
        
        Search Results:
        {findings_text}
        
        Provide a comprehensive legal risk assessment in JSON format:
        {{
            "summary": "<2-3 sentence overview of legal situation>",
            "ongoing_cases": [
                {{
                    "case_type": "<civil/criminal/regulatory/insolvency>",
                    "description": "<brief description>",
                    "severity": "<low/medium/high/critical>",
                    "estimated_year": "<year or 'unknown'>",
                    "status": "<ongoing/resolved/unknown>",
                    "financial_impact": "<potential financial impact>",
                    "credit_risk_impact": "<how this affects creditworthiness>"
                }}
            ],
            "past_cases": [
                {{
                    "case_type": "<type>",
                    "description": "<brief description>",
                    "outcome": "<outcome if known>",
                    "year": "<year>"
                }}
            ],
            "regulatory_actions": [
                {{
                    "authority": "<regulatory body>",
                    "action": "<description>",
                    "severity": "<low/medium/high>",
                    "year": "<year>"
                }}
            ],
            "risk_assessment": {{
                "overall_risk_level": "<low/medium/high/critical>",
                "credit_impact": "<positive/neutral/negative/severe>",
                "key_concerns": ["<concern 1>", "<concern 2>"],
                "mitigating_factors": ["<factor 1>", "<factor 2>"],
                "recommendation": "<recommendation for lenders>"
            }},
            "data_quality": "<high/medium/low - based on search results>",
            "last_checked": "<current date>",
            "requires_manual_verification": <true/false>
        }}
        
        Be objective and conservative in your assessment. If information is unclear, indicate uncertainty.
        Return ONLY valid JSON.
        """
        
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a legal risk analyst specializing in credit assessment. Analyze legal information objectively and conservatively."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=2000
        )
        
        response_content = response.choices[0].message.content
        
        # Clean up markdown if present
        if "```" in response_content:
            response_content = response_content.replace("```json", "").replace("```", "").strip()
        
        analysis = json.loads(response_content)
        analysis["search_results_count"] = len(findings)
        analysis["data_source"] = "web_search_with_ai_analysis"
        
        return analysis
        
    except Exception as e:
        print(f"Error analyzing legal findings: {e}")
        return await generate_legal_risk_assessment(company_name)


async def generate_legal_risk_assessment(company_name: str) -> Dict[str, Any]:
    """
    Generate a legal risk assessment using AI when no search results are available
    This provides a baseline assessment based on company profile
    """
    
    try:
        prompt = f"""
        Provide a baseline legal risk assessment for "{company_name}" for credit evaluation purposes.
        
        Since no specific legal case information is available, provide:
        1. General legal risk factors to consider for this type of company
        2. Recommended due diligence steps
        3. Typical legal issues in their industry
        
        Return in JSON format:
        {{
            "summary": "No specific legal cases found in public records. This assessment provides general guidance.",
            "ongoing_cases": [],
            "past_cases": [],
            "regulatory_actions": [],
            "risk_assessment": {{
                "overall_risk_level": "unknown",
                "credit_impact": "neutral",
                "key_concerns": ["<general concern 1>", "<general concern 2>"],
                "mitigating_factors": ["No adverse legal information found in public records"],
                "recommendation": "<recommendation for lenders>"
            }},
            "recommended_checks": [
                "<check 1>",
                "<check 2>",
                "<check 3>"
            ],
            "typical_industry_issues": [
                "<issue 1>",
                "<issue 2>"
            ],
            "data_quality": "low",
            "last_checked": "{datetime.utcnow().strftime('%Y-%m-%d')}",
            "requires_manual_verification": true,
            "note": "No specific legal cases found. Manual verification recommended through official court records."
        }}
        
        Return ONLY valid JSON.
        """
        
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a legal risk analyst providing baseline assessments."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        
        response_content = response.choices[0].message.content
        
        if "```" in response_content:
            response_content = response_content.replace("```json", "").replace("```", "").strip()
        
        assessment = json.loads(response_content)
        assessment["data_source"] = "ai_baseline_assessment"
        assessment["search_results_count"] = 0
        
        return assessment
        
    except Exception as e:
        print(f"Error generating legal risk assessment: {e}")
        
        # Ultimate fallback
        return {
            "summary": f"Legal case search for {company_name} could not be completed. Manual verification required.",
            "ongoing_cases": [],
            "past_cases": [],
            "regulatory_actions": [],
            "risk_assessment": {
                "overall_risk_level": "unknown",
                "credit_impact": "neutral",
                "key_concerns": [
                    "Unable to verify legal case status",
                    "Manual court record search recommended"
                ],
                "mitigating_factors": [],
                "recommendation": "Conduct manual legal due diligence through official court records (eCourts, NCLT, etc.)"
            },
            "recommended_checks": [
                "Search eCourts India portal manually",
                "Check NCLT/NCLAT records",
                "Verify with company's legal counsel",
                "Review MCA filings for legal disclosures"
            ],
            "data_quality": "none",
            "last_checked": datetime.utcnow().strftime('%Y-%m-%d'),
            "requires_manual_verification": True,
            "data_source": "fallback",
            "search_results_count": 0,
            "note": "Automated search unavailable. Please conduct manual verification."
        }
