# Tab Navigation Guide

## Application Detail Page - Tab Structure

### Visual Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│  ← Back to Dashboard                                                │
│                                                                      │
│  Company Name                                      [Export CAM]     │
│  Application ID: xxx...    Loan Amount: $XXX,XXX                   │
│  Status: XXX              Created: XX/XX/XXXX                       │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ [📄 Overview] [✓ Documents] [💡 Insights] [⚖️ Legal] [📰 News]     │
│ [📈 Financial] [⚠️ Risk] [📄 CAM]                                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│                     TAB CONTENT AREA                                │
│                                                                      │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## Tab Descriptions

### 1. 📄 Overview
**Purpose**: Application summary and quick actions
**Content**:
- Application status
- Key metrics
- Quick actions (Run Analysis, etc.)
- Summary cards

**When to use**: First view, getting overview of application

---

### 2. ✓ Documents
**Purpose**: Document management
**Content**:
- Document upload interface
- List of uploaded documents
- Document search
- Download/delete actions

**When to use**: Uploading or managing documents

---

### 3. 💡 Company Insights (Legacy)
**Purpose**: Combined company information
**Content**:
- Company profile
- Credit score factors
- News and legal cases (combined)

**When to use**: Quick overview of all company info

**Note**: This is the old combined view. Use Legal and News tabs for detailed views.

---

### 4. ⚖️ Legal Cases (NEW)
**Purpose**: Dedicated legal and compliance page
**Content**:
- Legal risk assessment summary
- Ongoing legal cases
- Past cases with outcomes
- Regulatory actions
- Key concerns and mitigating factors
- Recommendations for lenders
- Due diligence checklist

**When to use**: 
- Evaluating legal risks
- Checking litigation history
- Compliance verification
- Due diligence

**Features**:
- Color-coded risk levels
- Severity indicators
- Detailed case information
- Manual verification warnings

---

### 5. 📰 News Insights (NEW)
**Purpose**: Dedicated news and sentiment analysis page
**Content**:
- Positive news (left column)
- Negative news (right column)
- Sentiment scores and analysis
- AI-powered reasoning
- Detailed analysis modal

**When to use**:
- Monitoring company reputation
- Assessing market sentiment
- Understanding recent developments
- Credit risk evaluation

**Features**:
- Click any news item for detailed analysis
- Executive summaries
- Financial implications
- Risk assessments
- Recommendations

---

### 6. 📈 Financial Analysis
**Purpose**: Financial metrics and ratios
**Content**:
- Key financial metrics
- Financial ratios
- Trend analysis
- Page number references

**When to use**: Analyzing financial health

---

### 7. ⚠️ Risk Assessment
**Purpose**: Credit risk evaluation
**Content**:
- Credit score
- Risk factors
- Risk assessment details
- Recommendations

**When to use**: Making credit decisions

---

### 8. 📄 CAM Report
**Purpose**: Credit appraisal memorandum
**Content**:
- Complete CAM report
- Executive summary
- Detailed analysis
- Recommendations

**When to use**: Final credit decision, documentation

---

## Navigation Tips

### Quick Access
- Click any tab to switch instantly
- Active tab is highlighted in black
- Hover over tabs for visual feedback

### Keyboard Shortcuts
- `Tab` key to navigate between tabs
- `Enter` or `Space` to activate tab
- `Esc` to close modals

### Mobile Navigation
- Swipe left/right between tabs (if implemented)
- Tap tab icons (labels hidden on small screens)
- Full content scrollable

### Best Practices
1. Start with **Overview** to understand application status
2. Check **Documents** to ensure all files are uploaded
3. Review **Legal Cases** for compliance issues
4. Check **News Insights** for recent developments
5. Analyze **Financial** data for creditworthiness
6. Review **Risk Assessment** for decision factors
7. Generate **CAM Report** for final documentation

## Tab States

### Active Tab
- Black background
- White text
- No hover effect

### Inactive Tab
- White/gray background
- Gray text
- Hover: slight lift animation
- Hover: darker text

### Loading State
- Spinner animation
- "Loading..." message
- Disabled interaction

### Error State
- Error icon
- Error message
- "Try Again" button

## Data Flow

```
User clicks tab
    ↓
Tab state updates
    ↓
Component renders
    ↓
API call (if needed)
    ↓
Loading state
    ↓
Data received
    ↓
Content displays
```

## Common Workflows

### New Application Review
1. Overview → Check status
2. Documents → Verify uploads
3. Financial → Analyze metrics
4. Risk → Review assessment
5. Legal → Check compliance
6. News → Monitor sentiment
7. CAM → Generate report

### Due Diligence
1. Legal Cases → Check litigation
2. News Insights → Monitor reputation
3. Financial Analysis → Verify numbers
4. Risk Assessment → Evaluate factors
5. Documents → Review supporting docs

### Quick Check
1. Overview → Status check
2. Risk → Score review
3. Legal → Compliance check
4. News → Recent developments

## Troubleshooting

### Tab Not Loading
- Check internet connection
- Verify authentication
- Refresh page
- Check console for errors

### Content Not Displaying
- Ensure documents are uploaded
- Check application status
- Verify API endpoints
- Clear browser cache

### Slow Performance
- Close unused tabs
- Clear browser cache
- Check network speed
- Reduce open applications

## Feature Comparison

| Feature | Company Insights | Legal Cases | News Insights |
|---------|-----------------|-------------|---------------|
| Legal Cases | ✓ Basic | ✓ Detailed | ✗ |
| News | ✓ Basic | ✗ | ✓ Detailed |
| Sentiment Analysis | ✓ Basic | ✗ | ✓ Advanced |
| Risk Assessment | ✓ Basic | ✓ Legal Risk | ✗ |
| Recommendations | ✓ General | ✓ Legal | ✓ Financial |
| Detailed Analysis | ✗ | ✓ | ✓ |
| Modal View | ✗ | ✗ | ✓ |

## Recommendations

### For Analysts
- Use **Legal Cases** for thorough compliance review
- Use **News Insights** for market intelligence
- Cross-reference with **Financial Analysis**

### For Managers
- Start with **Overview** for quick status
- Review **Risk Assessment** for decisions
- Check **Legal Cases** for red flags

### For Compliance Officers
- Focus on **Legal Cases** tab
- Review **Documents** for completeness
- Check **News Insights** for reputational risks

---

**Last Updated**: March 8, 2026
**Version**: 2.0 (with separate Legal and News tabs)
