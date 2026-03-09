# Real News API Integration Guide

## Overview

The Company Insights feature now fetches **real company news** from NewsAPI, one of the world's largest news aggregation services with access to 80,000+ sources worldwide.

## Features

### 1. Real-Time News Fetching
- Fetches actual news articles from 80,000+ sources
- Searches for company-specific news from the last 30 days
- Sorts by relevancy to ensure most pertinent articles appear first
- Supports multiple languages (currently configured for English)

### 2. AI-Powered Sentiment Analysis
- Each article is analyzed using OpenAI GPT-4
- Sentiment score ranges from -1 (very negative) to +1 (very positive)
- Includes detailed reasoning for the sentiment classification
- Considers financial impact, market perception, and business implications

### 3. Detailed Article Information
Each news item includes:
- **Title**: Article headline
- **Full Description**: Complete article description (2-3 sentences)
- **Summary**: Truncated version for quick reading
- **Date**: Publication date
- **Source**: News outlet name (e.g., Bloomberg, Reuters, CNBC)
- **Author**: Article author (when available)
- **URL**: Direct link to the original article
- **Image URL**: Article thumbnail image
- **Sentiment Score**: Numerical sentiment (-1 to 1)
- **Sentiment Label**: positive/negative/neutral
- **Sentiment Reasoning**: AI explanation of why the sentiment was assigned

### 4. Intelligent Fallback System
- If NewsAPI is unavailable or returns no results, the system automatically falls back to AI-generated news
- Ensures users always see relevant information
- Clearly indicates the news source (Real API vs AI Generated)

## Setup Instructions

### Step 1: Get Your NewsAPI Key

1. Visit [https://newsapi.org/register](https://newsapi.org/register)
2. Sign up for a free account
3. Free tier includes:
   - 100 requests per day
   - Access to 80,000+ sources
   - 30 days of historical data
   - Perfect for development and small-scale production

### Step 2: Add API Key to Environment

Open `backend/.env` and add your API key:

```env
# News API Configuration
NEWS_API_KEY=your_actual_api_key_here
```

### Step 3: Install Dependencies

```bash
cd backend
pip install requests==2.31.0
```

Or install all requirements:

```bash
pip install -r requirements.txt
```

### Step 4: Restart the Backend

```bash
python -m uvicorn app.main:app --reload
```

## How It Works

### 1. News Fetching Process

```python
# The system searches for company-specific news
params = {
    "q": f'"{company_name}"',  # Exact phrase search
    "from": "2024-02-08",       # Last 30 days
    "to": "2024-03-08",         # Today
    "language": "en",           # English only
    "sortBy": "relevancy",      # Most relevant first
    "pageSize": 20,             # Get 20 articles
    "apiKey": news_api_key
}
```

### 2. Sentiment Analysis

For each article, the system:
1. Sends the title and description to OpenAI GPT-4
2. Asks for financial/business sentiment analysis
3. Receives:
   - Numerical score (-1 to 1)
   - Label (positive/negative/neutral)
   - Reasoning (1-sentence explanation)

Example sentiment analysis:

```json
{
  "score": 0.75,
  "label": "positive",
  "reasoning": "Strong revenue growth and market expansion indicate positive business momentum"
}
```

### 3. Article Categorization

Articles are automatically categorized:
- **Positive News**: sentiment_score > 0
- **Negative News**: sentiment_score ≤ 0

Each category shows the top 5 most relevant articles.

### 4. Fallback Mechanism

If NewsAPI fails or returns no results:
1. System automatically switches to AI-generated news
2. Uses OpenAI to create realistic, contextual news items
3. Maintains the same data structure
4. Clearly indicates "AI Generated" source

## API Response Structure

```json
{
  "application_id": "uuid",
  "company_name": "Acme Corporation",
  "company_details": {
    "industry": "Technology",
    "description": "...",
    "key_strengths": ["...", "..."],
    "potential_risks": ["...", "..."]
  },
  "news": {
    "positive": [
      {
        "title": "Acme Corp Reports Record Revenue",
        "summary": "Company exceeds expectations...",
        "full_description": "Detailed description...",
        "date": "2024-03-01",
        "source": "Bloomberg",
        "url": "https://...",
        "author": "John Smith",
        "sentiment_score": 0.85,
        "sentiment_label": "positive",
        "sentiment_reasoning": "Strong financial performance..."
      }
    ],
    "negative": [...],
    "total_count": 10,
    "last_updated": "2024-03-08T10:30:00",
    "source": "NewsAPI",
    "api_status": "success"
  },
  "credit_factors": {...}
}
```

## UI Features

### Enhanced News Display

1. **Clickable Links**: Each article has a "Read →" link to the original source
2. **Sentiment Visualization**: Progress bars show sentiment strength
3. **Detailed Analysis**: AI reasoning is displayed for each article
4. **Author Attribution**: Shows article author when available
5. **Source Badges**: Clear indication of news source
6. **Hover Effects**: Cards expand on hover for better UX
7. **Source Attribution**: Footer shows whether news is from API or AI-generated

### Visual Indicators

- **Green cards**: Positive news (sentiment > 0.5)
- **Blue cards**: Slightly positive (0 < sentiment ≤ 0.5)
- **Yellow cards**: Slightly negative (-0.5 < sentiment ≤ 0)
- **Red cards**: Negative news (sentiment ≤ -0.5)

## NewsAPI Pricing Tiers

### Free Tier (Developer)
- **Cost**: $0/month
- **Requests**: 100/day
- **Sources**: 80,000+
- **History**: 30 days
- **Best for**: Development, testing, small projects

### Business Tier
- **Cost**: $449/month
- **Requests**: 250,000/month
- **Sources**: 80,000+
- **History**: Full archive
- **Best for**: Production applications

### Enterprise Tier
- **Cost**: Custom pricing
- **Requests**: Unlimited
- **Sources**: 80,000+
- **History**: Full archive
- **Support**: Dedicated account manager

## Alternative News APIs

If you need different features, consider these alternatives:

### 1. **Bing News Search API** (Microsoft Azure)
- **Pros**: Excellent coverage, reliable, part of Azure ecosystem
- **Pricing**: $3-$7 per 1,000 transactions
- **Best for**: Enterprise applications

### 2. **Google News API** (via SerpAPI)
- **Pros**: Google's news aggregation, very comprehensive
- **Pricing**: $50/month for 5,000 searches
- **Best for**: High-quality news aggregation

### 3. **Finnhub** (Financial News)
- **Pros**: Specialized in financial/stock market news
- **Pricing**: Free tier available, $59/month for premium
- **Best for**: Financial applications

### 4. **Alpha Vantage** (Financial Data + News)
- **Pros**: Combines market data with news
- **Pricing**: Free tier, $49.99/month premium
- **Best for**: Trading/investment platforms

## Troubleshooting

### Issue: "No news found"
**Solution**: 
- Check if company name is spelled correctly
- Try a more well-known company for testing
- System will automatically use AI-generated fallback

### Issue: "API key invalid"
**Solution**:
- Verify API key in `.env` file
- Ensure no extra spaces or quotes
- Check if key is active on NewsAPI dashboard

### Issue: "Rate limit exceeded"
**Solution**:
- Free tier has 100 requests/day limit
- Wait 24 hours or upgrade to paid tier
- System will use AI-generated fallback

### Issue: "Request timeout"
**Solution**:
- Check internet connection
- NewsAPI might be experiencing issues
- System will automatically use fallback

## Best Practices

1. **Cache Results**: Consider caching news for 1-6 hours to reduce API calls
2. **Monitor Usage**: Track API usage to avoid hitting rate limits
3. **Error Handling**: Always have fallback mechanisms
4. **User Feedback**: Show users whether news is real or AI-generated
5. **Update Frequency**: Refresh news daily or when user requests

## Security Considerations

1. **API Key Protection**: Never commit API keys to version control
2. **Environment Variables**: Always use `.env` files
3. **Rate Limiting**: Implement rate limiting on your endpoints
4. **Input Validation**: Sanitize company names before API calls
5. **HTTPS Only**: Always use HTTPS for API requests

## Performance Optimization

1. **Parallel Processing**: Sentiment analysis runs in parallel for multiple articles
2. **Timeout Handling**: 10-second timeout prevents hanging requests
3. **Result Limiting**: Only processes top 10 articles to save time
4. **Caching**: Consider implementing Redis cache for frequently requested companies
5. **Async Operations**: All API calls are asynchronous

## Future Enhancements

Potential improvements:
1. **News Filtering**: Filter by specific topics (earnings, acquisitions, etc.)
2. **Trend Analysis**: Track sentiment changes over time
3. **Competitor News**: Show news about competitors
4. **Custom Sources**: Allow users to select preferred news sources
5. **Email Alerts**: Notify users of significant news
6. **News Summary**: AI-generated executive summary of all news
7. **Multilingual Support**: Support news in multiple languages

## Support

For issues or questions:
- NewsAPI Documentation: https://newsapi.org/docs
- NewsAPI Support: support@newsapi.org
- OpenAI Documentation: https://platform.openai.com/docs

## License

NewsAPI Terms: https://newsapi.org/terms
Ensure compliance with NewsAPI's terms of service when using in production.
