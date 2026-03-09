# Legal Case Tracking Feature

## Overview
Added comprehensive legal case tracking to evaluate companies' litigation history, ongoing court cases, and regulatory actions as part of credit risk assessment.

## Implementation Date
March 8, 2026

## Features Implemented

### Backend API (`backend/app/api/company_insights.py`)

#### New Endpoint
- **GET** `/api/v1/applications/{application_id}/legal-cases`
  - Searches for legal cases involving the company
  - Returns structured legal risk assessment
  - Uses AI-powered analysis

#### Core Functions

1. **`search_legal_cases(company_name)`**
   - Performs web search for court cases, litigation, and regulatory actions
   - Searches multiple query patterns:
     - Court cases in India
     - Litigation and legal disputes
     - NCLT insolvency cases
     - Regulatory actions and penalties
   - Extracts search result snippets for analysis

2. **`analyze_legal_findings(company_name, findings)`**
   - Uses OpenAI GPT-4 to analyze search results
   - Extracts structured information:
     - Ongoing cases with severity levels
     - Past cases with outcomes
     - Regulatory actions
     - Risk assessment
     - Credit impact evaluation
   - Returns comprehensive JSON analysis

3. **`generate_legal_risk_assessment(company_name)`**
   - Fallback function when no search results available
   - Provides baseline risk assessment
   - Recommends manual verification steps
   - Lists typical industry legal issues

### Frontend Display (`frontend/src/components/CompanyInsightsTab.tsx`)

#### New Section: Legal & Compliance Status

**Visual Design:**
- Premium gradient header with red/rose colors
- Risk-level color coding:
  - Green: Low/Unknown risk
  - Yellow: Medium risk
  - Red: High/Critical risk

**Components:**

1. **Legal Risk Assessment Card**
   - Summary of legal situation
   - Overall risk level badge
   - Credit impact indicator
   - Color-coded based on risk level

2. **Ongoing Legal Cases**
   - Red-themed cards for active cases
   - Case type badges (civil/criminal/regulatory/insolvency)
   - Severity indicators (low/medium/high/critical)
   - Financial impact description
   - Credit risk impact explanation
   - Estimated year

3. **Past Legal Cases**
   - Gray-themed cards for resolved cases
   - Case type and year
   - Outcome information
   - Historical context

4. **Regulatory Actions**
   - Orange-themed cards
   - Regulatory authority name
   - Action description
   - Severity level
   - Year of action

5. **Risk Assessment Details**
   - **Key Concerns** (red card)
     - List of legal risk factors
     - Warning icons
   - **Mitigating Factors** (green card)
     - Positive factors that reduce risk
     - Checkmark icons

6. **Recommendation for Lenders**
   - Indigo/purple gradient card
   - Actionable advice for credit decisions
   - Based on AI analysis

7. **Recommended Due Diligence**
   - Blue-themed card
   - Checklist of verification steps
   - Links to official resources

8. **Data Quality Notice**
   - Yellow warning card
   - Manual verification reminder
   - Disclaimer about automated search

## Data Structure

### Legal Cases Response Format
```json
{
  "summary": "Overview of legal situation",
  "ongoing_cases": [
    {
      "case_type": "civil|criminal|regulatory|insolvency",
      "description": "Case description",
      "severity": "low|medium|high|critical",
      "estimated_year": "2024",
      "status": "ongoing|resolved|unknown",
      "financial_impact": "Potential financial impact",
      "credit_risk_impact": "How this affects creditworthiness"
    }
  ],
  "past_cases": [
    {
      "case_type": "Type of case",
      "description": "Description",
      "outcome": "Resolution",
      "year": "Year"
    }
  ],
  "regulatory_actions": [
    {
      "authority": "Regulatory body",
      "action": "Action taken",
      "severity": "low|medium|high",
      "year": "Year"
    }
  ],
  "risk_assessment": {
    "overall_risk_level": "low|medium|high|critical",
    "credit_impact": "positive|neutral|negative|severe",
    "key_concerns": ["Concern 1", "Concern 2"],
    "mitigating_factors": ["Factor 1", "Factor 2"],
    "recommendation": "Recommendation for lenders"
  },
  "recommended_checks": ["Check 1", "Check 2"],
  "data_quality": "high|medium|low|none",
  "requires_manual_verification": true|false,
  "data_source": "web_search_with_ai_analysis|ai_baseline_assessment|fallback",
  "search_results_count": 0,
  "last_checked": "2026-03-08"
}
```

## AI Analysis Approach

### Search Strategy
1. Multiple targeted search queries
2. Extract top 3 results per query
3. Compile findings for AI analysis

### AI Processing
- **Model**: GPT-4
- **Temperature**: 0.2 (conservative, factual)
- **Max Tokens**: 2000
- **Approach**: Objective and conservative assessment
- **Uncertainty Handling**: Explicitly indicates when information is unclear

### Fallback Mechanism
- If search fails: Generate baseline assessment
- If AI fails: Return structured fallback with manual verification instructions
- Always provides actionable information

## Integration with Credit Assessment

### Risk Factors Considered
1. **Ongoing Litigation**
   - Active court cases
   - Severity and potential outcomes
   - Financial exposure

2. **Past Legal History**
   - Previous cases and outcomes
   - Pattern of litigation
   - Resolution track record

3. **Regulatory Compliance**
   - Actions by regulatory bodies
   - Penalties and fines
   - Compliance track record

4. **Credit Impact**
   - Direct effect on creditworthiness
   - Potential financial liabilities
   - Reputational risk

## User Experience

### Loading States
- Animated spinner while searching
- "Searching legal records..." message
- Smooth transitions

### Empty States
- Clear message when no data available
- Guidance on next steps

### Error Handling
- Graceful degradation
- Always provides some information
- Clear manual verification instructions

## Data Sources

### Current Implementation
- Web search (Google)
- AI-powered analysis
- Automated extraction

### Recommended Upgrades (Future)
- **eCourts India API** - Official court records
- **NCLT/NCLAT API** - Insolvency cases
- **MCA API** - Company legal disclosures
- **Vakeel360 API** - Comprehensive legal data
- **QiLegal API** - Judicial data access

## Security & Privacy

### Data Handling
- No storage of legal case data
- Real-time search and analysis
- User authentication required

### Disclaimers
- Automated search limitations clearly stated
- Manual verification always recommended
- Data quality indicators provided

## Testing Recommendations

1. **Test with known companies**
   - Companies with public litigation
   - Companies with clean records
   - Companies with regulatory actions

2. **Verify AI analysis quality**
   - Check for hallucinations
   - Validate severity assessments
   - Confirm recommendations are reasonable

3. **Test error scenarios**
   - Network failures
   - API timeouts
   - Invalid company names

4. **Performance testing**
   - Search response time
   - AI analysis latency
   - Frontend rendering

## Future Enhancements

### Short Term
1. Cache legal case results (24-hour TTL)
2. Add export to PDF functionality
3. Email alerts for new cases

### Medium Term
1. Integrate paid legal case APIs
2. Add case document viewer
3. Timeline visualization of legal history
4. Comparison with industry peers

### Long Term
1. Predictive legal risk scoring
2. Automated case outcome prediction
3. Integration with credit scoring model
4. Real-time case status updates

## Files Modified

### Backend
- `backend/app/api/company_insights.py`
  - Added `/legal-cases` endpoint
  - Added `search_legal_cases()` function
  - Added `analyze_legal_findings()` function
  - Added `generate_legal_risk_assessment()` function

### Frontend
- `frontend/src/components/CompanyInsightsTab.tsx`
  - Added legal cases state management
  - Added `fetchLegalCases()` function
  - Added comprehensive legal cases display section
  - Added risk-level color coding
  - Added multiple card components for different case types

## Dependencies

### Backend
- `openai` - AI analysis
- `requests` - Web search
- `beautifulsoup4` - HTML parsing

### Frontend
- `framer-motion` - Animations
- `lucide-react` - Icons

## Configuration

### Environment Variables
- `OPENAI_API_KEY` - Required for AI analysis
- No additional API keys needed for basic functionality

## Usage

### For Lenders
1. Navigate to Company Insights tab
2. Scroll to "Legal & Compliance Status" section
3. Review risk assessment summary
4. Check ongoing cases for active litigation
5. Review past cases for patterns
6. Read recommendations
7. Follow due diligence checklist
8. Verify through official sources

### For Developers
```python
# Backend API call
GET /api/v1/applications/{application_id}/legal-cases
Authorization: Bearer {token}

# Response
{
  "success": true,
  "application_id": "...",
  "company_name": "...",
  "legal_cases": { ... },
  "generated_at": "2026-03-08T..."
}
```

```typescript
// Frontend usage
const fetchLegalCases = async () => {
  const response = await fetch(
    `http://localhost:8000/api/v1/applications/${applicationId}/legal-cases`,
    {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    }
  );
  const data = await response.json();
  setLegalCases(data.legal_cases);
};
```

## Known Limitations

1. **Search Accuracy**
   - Depends on public web data availability
   - May miss cases not indexed by search engines
   - Requires manual verification

2. **AI Analysis**
   - Conservative approach may underestimate risks
   - Limited by search result quality
   - Cannot access paywalled legal databases

3. **Real-time Updates**
   - No automatic case status updates
   - Requires manual refresh
   - No push notifications

4. **Coverage**
   - Limited to publicly available information
   - May not include all court levels
   - International cases may be missed

## Compliance Notes

- This feature provides preliminary screening only
- Not a substitute for professional legal due diligence
- Users must verify through official court records
- Automated analysis has inherent limitations
- Always consult legal counsel for final decisions

## Support & Maintenance

### Monitoring
- Track API success rates
- Monitor AI analysis quality
- Log search failures

### Updates
- Keep AI prompts current
- Update search patterns as needed
- Refine risk assessment criteria

### Documentation
- Maintain this document
- Update as features evolve
- Document API changes

---

**Status**: ✅ Implemented and Ready for Testing
**Priority**: High - Critical for credit risk assessment
**Impact**: Significant improvement in due diligence capabilities
