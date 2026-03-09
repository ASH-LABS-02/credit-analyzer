# Legal Case API Integration Guide

## Overview
Guide to integrate real legal case APIs for fetching actual court case data instead of mock data.

## Recommended APIs

### Option 1: eCourts India API (FREE - Official)

**Best for**: Government data, free access, official records

**Endpoints**:
```
Base URL: https://services.ecourts.gov.in/ecourtindia_v6/

1. Case Status by CNR
   GET /case_status_cnr.php?cnr={cnr_number}

2. Case Status by Party Name
   POST /case_status_party.php
   Body: {
     "state_code": "string",
     "dist_code": "string", 
     "court_code": "string",
     "party_name": "string"
   }

3. Cause List
   GET /cause_list.php?court_code={code}&date={YYYY-MM-DD}
```

**Registration**: No API key required for basic access

**Rate Limits**: Not officially documented

---

### Option 2: Vakeel360 API (PAID - Recommended)

**Best for**: Commercial use, comprehensive coverage, reliable

**Pricing**: 
- Starter: ₹2,999/month
- Professional: ₹9,999/month
- Enterprise: Custom pricing

**Coverage**:
- District Courts
- High Courts
- Supreme Court
- NCLT (23 benches)
- ITAT (23 benches)
- CESTAT (10 benches)
- CAT, RERA, and more

**Endpoints**:
```
Base URL: https://api.vakeel360.com/v1/

1. Search Cases by Company Name
   POST /search/cases
   Headers: {
     "Authorization": "Bearer {api_key}",
     "Content-Type": "application/json"
   }
   Body: {
     "query": "company_name",
     "court_type": "all",
     "status": "all"
   }

2. Get Case Details
   GET /cases/{case_id}
   Headers: {
     "Authorization": "Bearer {api_key}"
   }

3. Search by CNR
   GET /cases/cnr/{cnr_number}
   Headers: {
     "Authorization": "Bearer {api_key}"
   }
```

**Registration**: https://vakeel360.com/api/register

---

### Option 3: QiLegal API (PAID - Enterprise)

**Best for**: Large-scale operations, comprehensive data

**Pricing**: Contact for quote (enterprise pricing)

**Coverage**:
- 21.5 crore case records
- Supreme Court to District Level
- 23.8 lakh lawyer profiles
- Real-time cause lists

**Endpoints**:
```
Base URL: https://api.qilegal.com/v1/

1. Search Cases
   POST /search/cases
   Headers: {
     "X-API-Key": "{api_key}",
     "Content-Type": "application/json"
   }
   Body: {
     "party_name": "company_name",
     "court_type": ["district", "high", "supreme"],
     "from_date": "YYYY-MM-DD",
     "to_date": "YYYY-MM-DD"
   }

2. Get Case by ID
   GET /cases/{case_id}
   Headers: {
     "X-API-Key": "{api_key}"
   }
```

**Registration**: https://qilegal.com/contact

---

## Implementation Steps

### Step 1: Choose API Provider

**For Testing/Development**: Use eCourts India API (free)
**For Production**: Use Vakeel360 or QiLegal (paid, reliable)

### Step 2: Get API Credentials

**eCourts**: No registration needed
**Vakeel360**: Register at https://vakeel360.com/api/register
**QiLegal**: Contact sales team

### Step 3: Add API Key to Environment

Add to `backend/.env`:
```env
# Legal Case API Configuration
LEGAL_API_PROVIDER=vakeel360  # or ecourts, qilegal
VAKEEL360_API_KEY=your_api_key_here
QILEGAL_API_KEY=your_api_key_here

# Optional: API Configuration
LEGAL_API_TIMEOUT=30
LEGAL_API_MAX_RETRIES=3
```

### Step 4: Update Backend Code

The backend code in `backend/app/api/company_insights.py` needs to be updated to use the real API.

---

## Code Implementation

### For Vakeel360 API (Recommended)

```python
import os
import requests
from typing import Dict, Any, List

VAKEEL360_API_KEY = os.getenv("VAKEEL360_API_KEY")
VAKEEL360_BASE_URL = "https://api.vakeel360.com/v1"

async def search_legal_cases_vakeel360(company_name: str) -> Dict[str, Any]:
    """
    Search for legal cases using Vakeel360 API
    """
    
    if not VAKEEL360_API_KEY:
        return await generate_legal_risk_assessment(company_name)
    
    try:
        headers = {
            "Authorization": f"Bearer {VAKEEL360_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Search for cases
        search_payload = {
            "query": company_name,
            "court_type": "all",
            "status": "all",
            "limit": 50
        }
        
        response = requests.post(
            f"{VAKEEL360_BASE_URL}/search/cases",
            headers=headers,
            json=search_payload,
            timeout=30
        )
        
        response.raise_for_status()
        data = response.json()
        
        # Parse and structure the response
        return parse_vakeel360_response(company_name, data)
        
    except Exception as e:
        print(f"Error fetching from Vakeel360: {e}")
        return await generate_legal_risk_assessment(company_name)


def parse_vakeel360_response(company_name: str, data: Dict) -> Dict[str, Any]:
    """
    Parse Vakeel360 API response into our standard format
    """
    
    cases = data.get("cases", [])
    
    ongoing_cases = []
    past_cases = []
    regulatory_actions = []
    
    for case in cases:
        case_status = case.get("status", "").lower()
        case_type = case.get("case_type", "civil")
        
        case_info = {
            "case_type": case_type,
            "description": case.get("case_title", ""),
            "case_number": case.get("case_number", ""),
            "filing_date": case.get("filing_date", ""),
            "court_name": case.get("court_name", ""),
            "estimated_year": case.get("filing_date", "")[:4] if case.get("filing_date") else "unknown"
        }
        
        # Categorize cases
        if case_status in ["pending", "ongoing", "active"]:
            # Assess severity based on case type and amount
            severity = assess_case_severity(case)
            
            ongoing_cases.append({
                **case_info,
                "severity": severity,
                "status": "ongoing",
                "financial_impact": case.get("claim_amount", "Not specified"),
                "credit_risk_impact": f"Ongoing {case_type} case may impact creditworthiness",
                "next_hearing": case.get("next_hearing_date", "Not scheduled")
            })
        else:
            past_cases.append({
                **case_info,
                "outcome": case.get("judgment", "Case concluded"),
                "year": case.get("filing_date", "")[:4] if case.get("filing_date") else "unknown"
            })
    
    # Calculate risk assessment
    risk_level = calculate_risk_level(ongoing_cases, past_cases)
    
    return {
        "summary": f"Found {len(cases)} legal cases for {company_name} through Vakeel360 API.",
        "ongoing_cases": ongoing_cases[:10],  # Limit to 10 most recent
        "past_cases": past_cases[:10],
        "regulatory_actions": regulatory_actions,
        "risk_assessment": {
            "overall_risk_level": risk_level,
            "credit_impact": "negative" if len(ongoing_cases) > 3 else "neutral",
            "key_concerns": generate_concerns(ongoing_cases),
            "mitigating_factors": generate_mitigating_factors(past_cases),
            "recommendation": generate_recommendation(risk_level, ongoing_cases)
        },
        "data_source": "vakeel360_api",
        "search_results_count": len(cases),
        "last_checked": datetime.utcnow().strftime('%Y-%m-%d'),
        "requires_manual_verification": False,
        "api_status": "success"
    }


def assess_case_severity(case: Dict) -> str:
    """
    Assess severity of a legal case
    """
    case_type = case.get("case_type", "").lower()
    claim_amount = case.get("claim_amount", 0)
    
    # Criminal cases are high severity
    if "criminal" in case_type:
        return "high"
    
    # Check claim amount
    if isinstance(claim_amount, (int, float)):
        if claim_amount > 10000000:  # > 1 crore
            return "critical"
        elif claim_amount > 1000000:  # > 10 lakhs
            return "high"
        elif claim_amount > 100000:  # > 1 lakh
            return "medium"
    
    # Default
    return "medium" if "civil" in case_type else "low"


def calculate_risk_level(ongoing: List, past: List) -> str:
    """
    Calculate overall risk level
    """
    if len(ongoing) == 0:
        return "low"
    elif len(ongoing) >= 5:
        return "high"
    elif len(ongoing) >= 3:
        return "medium"
    else:
        # Check severity
        high_severity = sum(1 for c in ongoing if c.get("severity") in ["high", "critical"])
        if high_severity >= 2:
            return "high"
        elif high_severity >= 1:
            return "medium"
    
    return "low"
```

---

## Testing

### Test with eCourts API (Free)

```python
# Test search
import requests

# Search by party name
url = "https://services.ecourts.gov.in/ecourtindia_v6/case_status_party.php"
data = {
    "state_code": "07",  # Maharashtra
    "dist_code": "01",   # Mumbai
    "court_code": "001",
    "party_name": "Infosys"
}

response = requests.post(url, data=data)
print(response.json())
```

### Test with Vakeel360 API (Paid)

```python
import requests

headers = {
    "Authorization": "Bearer YOUR_API_KEY",
    "Content-Type": "application/json"
}

payload = {
    "query": "Infosys Limited",
    "court_type": "all",
    "status": "all"
}

response = requests.post(
    "https://api.vakeel360.com/v1/search/cases",
    headers=headers,
    json=payload
)

print(response.json())
```

---

## Cost Comparison

| Provider | Setup Cost | Monthly Cost | Per-Call Cost | Best For |
|----------|-----------|--------------|---------------|----------|
| eCourts | Free | Free | Free | Testing, Basic |
| Vakeel360 | Free | ₹2,999+ | Included | Production |
| QiLegal | Contact | Custom | Included | Enterprise |

---

## Recommendation

**For Your Use Case:**

1. **Start with**: Vakeel360 API (₹2,999/month)
   - Reliable and affordable
   - Good coverage
   - Fixed pricing
   - No per-call charges

2. **Alternative**: eCourts API (Free)
   - For testing
   - Limited features
   - May have reliability issues

3. **Enterprise**: QiLegal API
   - If you need massive scale
   - Custom pricing
   - Most comprehensive data

---

## Next Steps

1. **Sign up** for Vakeel360 API: https://vakeel360.com/api/register
2. **Get API key** from dashboard
3. **Add to .env** file
4. **Update backend code** (I can help with this)
5. **Test integration**
6. **Deploy to production**

Would you like me to:
1. Update the backend code to use Vakeel360 API?
2. Help you sign up for an API key?
3. Create test scripts for the API?

Let me know which API provider you'd like to use!
