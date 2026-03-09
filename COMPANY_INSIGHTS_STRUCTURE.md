# Company Insights Tab - Complete Structure

## Overview
The Company Insights tab already contains both Legal Cases and News Insights sections, providing a comprehensive view of company information in one place.

## Current Structure

### Section 1: Company Profile
**Icon**: Building (🏢)
**Content**:
- Company name
- Industry
- Description
- Key Strengths (with checkmarks)
- Potential Risks (with warning icons)
- Documents analyzed count

**Purpose**: Quick overview of company basics

---

### Section 2: Credit Score Analysis
**Icon**: Bar Chart (📊)
**Content**:
- Overall credit score (large display with /100)
- Recommendation (approve/review/reject)
- Credit factors breakdown:
  - Financial Health (35% weight)
  - Business Stability (25% weight)
  - Industry Outlook (20% weight)
  - Management Quality (10% weight)
  - Debt Capacity (10% weight)
- Each factor shows:
  - Score out of 100
  - Status (good/fair/poor)
  - Description
  - Progress bar
  - Weight percentage

**Purpose**: Detailed credit scoring breakdown

---

### Section 3: Legal & Compliance Status ✅
**Icon**: Alert Circle (⚠️)
**Content**:
- **Legal Risk Assessment Summary**
  - Overall risk level (Low/Medium/High/Critical)
  - Summary text
  - Credit impact indicator

- **Ongoing Legal Cases**
  - Case type (civil/criminal/regulatory/insolvency)
  - Severity level (low/medium/high/critical)
  - Description
  - Financial impact
  - Credit risk impact
  - Estimated year

- **Past Legal Cases**
  - Case type
  - Description
  - Outcome
  - Year

- **Regulatory Actions**
  - Authority name
  - Action description
  - Severity level
  - Year

- **Risk Assessment Details**
  - Key Concerns (red card)
  - Mitigating Factors (green card)

- **Recommendation for Lenders**
  - Actionable advice

- **Recommended Due Diligence**
  - Checklist of verification steps

- **Data Quality Notice**
  - Manual verification warning
  - Data source information

**Purpose**: Complete legal and compliance risk assessment

---

### Section 4: Company News & Sentiment ✅
**Icon**: Newspaper (📰)
**Content**:
- **Two-Column Layout**:
  - Left: Positive News
  - Right: Negative News

- **Each News Item Shows**:
  - Title
  - Summary/Description
  - AI Analysis reasoning
  - Source and author
  - Publication date
  - Sentiment score (visual progress bar)
  - Percentage indicator
  - Click for detailed analysis

- **Detailed News Modal** (on click):
  - Executive Summary
  - Key Points
  - Financial Implications
    - Short-term impact
    - Long-term impact
    - Revenue impact
    - Cost impact
    - Market position
  - Stakeholder Impact
    - Investors
    - Creditors
    - Customers
    - Employees
  - Risk Assessment
    - Credit risk
    - Operational risk
    - Market risk
    - Reputational risk
  - Opportunities
  - Threats
  - Recommendations
    - For lenders
    - For investors
    - Monitoring points
  - Comparable Events
  - Overall Sentiment
  - Confidence Level
  - Key Metrics to Watch

- **News Source Attribution**
  - Powered by NewsAPI or AI Generated
  - Last updated timestamp

**Purpose**: Monitor company reputation and market sentiment

---

## Visual Layout

```
┌─────────────────────────────────────────────────────────────┐
│                    COMPANY INSIGHTS TAB                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  🏢 Company Profile                                         │
│  ├─ Company Name & Industry                                 │
│  ├─ Description                                             │
│  ├─ ✓ Key Strengths                                         │
│  └─ ⚠ Potential Risks                                       │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  📊 Credit Score Analysis                                   │
│  ├─ Overall Score: XX/100                                   │
│  ├─ Recommendation: [Approve/Review/Reject]                 │
│  └─ Factor Breakdown (5 factors with progress bars)         │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ⚠️ Legal & Compliance Status                               │
│  ├─ Risk Assessment Summary                                 │
│  ├─ Ongoing Cases (if any)                                  │
│  ├─ Past Cases (if any)                                     │
│  ├─ Regulatory Actions (if any)                             │
│  ├─ Key Concerns & Mitigating Factors                       │
│  ├─ Recommendations                                         │
│  └─ Due Diligence Checklist                                 │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  📰 Company News & Sentiment                                │
│  ├─ Positive News (left column)                             │
│  │   ├─ News Item 1 [Click for details]                     │
│  │   ├─ News Item 2 [Click for details]                     │
│  │   └─ News Item 3 [Click for details]                     │
│  │                                                           │
│  └─ Negative News (right column)                            │
│      ├─ News Item 1 [Click for details]                     │
│      ├─ News Item 2 [Click for details]                     │
│      └─ News Item 3 [Click for details]                     │
│                                                              │
│  News Source: NewsAPI | Last Updated: [timestamp]           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow

### On Component Mount
1. Fetch company insights (profile, credit score, news)
2. Fetch legal cases separately
3. Display loading states
4. Render all sections when data arrives

### API Calls
- `GET /api/v1/applications/{id}/company-insights`
  - Returns: company details, credit factors, news
- `GET /api/v1/applications/{id}/legal-cases`
  - Returns: legal cases, risk assessment
- `POST /api/v1/applications/{id}/news-details` (on news click)
  - Returns: detailed AI analysis of news article

## Features

### Interactive Elements
- **News Cards**: Click to open detailed analysis modal
- **Progress Bars**: Animated on load
- **Expandable Sections**: Smooth animations
- **Color Coding**: Risk levels and sentiment scores

### Loading States
- Spinner for main content
- Separate spinner for legal cases
- Modal loading for news details

### Error Handling
- Graceful fallbacks
- Retry buttons
- User-friendly error messages

## Color Scheme

### Legal Cases
- **Low Risk**: Green (emerald-50 to teal-50)
- **Medium Risk**: Yellow (amber-50 to orange-50)
- **High Risk**: Red (rose-50 to red-50)
- **Critical**: Dark Red (red-600)

### News Sentiment
- **Highly Positive**: Green (emerald)
- **Positive**: Blue (blue)
- **Slightly Negative**: Yellow (amber)
- **Negative**: Red (rose)

### General
- **Headers**: Black backgrounds with white text
- **Cards**: White with gray borders
- **Accents**: Indigo/Purple for recommendations

## Responsive Design

### Desktop (> 1024px)
- Two-column news layout
- Full-width legal cases
- All details visible

### Tablet (640px - 1024px)
- Two-column news layout
- Stacked legal cases
- Optimized spacing

### Mobile (< 640px)
- Single column news
- Stacked sections
- Touch-friendly cards
- Scrollable content

## User Workflows

### Quick Review
1. Scroll to Legal & Compliance
2. Check risk level
3. Review ongoing cases
4. Scroll to News
5. Check sentiment

### Detailed Analysis
1. Read company profile
2. Review credit score factors
3. Examine each legal case
4. Click news items for detailed analysis
5. Read recommendations

### Due Diligence
1. Check legal cases thoroughly
2. Review regulatory actions
3. Read all news articles
4. Follow due diligence checklist
5. Verify through official sources

## Benefits of Combined View

### Advantages
✅ All information in one place
✅ Easy to cross-reference
✅ Comprehensive overview
✅ Single page load
✅ Contextual understanding

### Use Cases
- Quick application review
- Comprehensive due diligence
- Risk assessment
- Credit decision making
- Compliance verification

## Comparison with Separate Tabs

| Feature | Company Insights (Combined) | Separate Tabs |
|---------|----------------------------|---------------|
| Navigation | Single page, scroll | Multiple clicks |
| Context | All info together | Isolated views |
| Loading | One load | Multiple loads |
| Cross-reference | Easy | Requires switching |
| Detail Level | Summary + Details | Full details |
| Best For | Quick review | Deep dive |

## Recommendations

### When to Use Company Insights Tab
- Initial application review
- Quick risk assessment
- Comprehensive overview
- Time-sensitive decisions
- Cross-referencing information

### When to Use Separate Tabs
- Deep dive into legal cases
- Detailed news analysis
- Focused investigation
- Specific area review
- Detailed documentation

## Current Status

✅ **Company Profile** - Implemented
✅ **Credit Score Analysis** - Implemented
✅ **Legal & Compliance Status** - Implemented and Integrated
✅ **Company News & Sentiment** - Implemented and Integrated

**All sections are live and functional in the Company Insights tab!**

## Files

**Component**: `frontend/src/components/CompanyInsightsTab.tsx`
**Lines**: ~900+ lines
**Sections**: 4 major sections
**API Calls**: 3 endpoints

---

**Last Updated**: March 8, 2026
**Status**: ✅ Complete - Both Legal Cases and News Insights are integrated
**Version**: 2.0 (with legal cases and news insights sections)
