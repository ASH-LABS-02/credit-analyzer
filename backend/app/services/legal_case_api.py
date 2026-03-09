"""
Legal Case API Integration Service
Supports multiple legal case API providers for India
"""

import os
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime
import json


class LegalCaseAPIService:
    """
    Service to fetch legal cases from various API providers
    """
    
    def __init__(self):
        self.provider = os.getenv("LEGAL_API_PROVIDER", "web_search")  # vakeel360, ecourts, qilegal, web_search
        self.vakeel360_key = os.getenv("VAKEEL360_API_KEY")
        self.qilegal_key = os.getenv("QILEGAL_API_KEY")
        self.timeout = int(os.getenv("LEGAL_API_TIMEOUT", "30"))
        self.max_retries = int(os.getenv("LEGAL_API_MAX_RETRIES", "3"))
        
    async def search_cases(self, company_name: str) -> Dict[str, Any]:
        """
        Search for legal cases using configured provider
        """
        
        if self.provider == "vakeel360" and self.vakeel360_key:
            return await self._search_vakeel360(company_name)
        elif self.provider == "ecourts":
            return await self._search_ecourts(company_name)
        elif self.provider == "qilegal" and self.qilegal_key:
            return await self._search_qilegal(company_name)
        else:
            # Fallback to web search + AI
            return await self._search_web_fallback(company_name)
    
    async def _search_vakeel360(self, company_name: str) -> Dict[str, Any]:
        """
        Search using Vakeel360 API
        """
        
        try:
            headers = {
                "Authorization": f"Bearer {self.vakeel360_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "query": company_name,
                "court_type": "all",
                "status": "all",
                "limit": 50
            }
            
            response = requests.post(
                "https://api.vakeel360.com/v1/search/cases",
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            data = response.json()
            
            return self._parse_vakeel360_response(company_name, data)
            
        except requests.exceptions.RequestException as e:
            print(f"Vakeel360 API error: {e}")
            return await self._search_web_fallback(company_name)
        except Exception as e:
            print(f"Error in Vakeel360 search: {e}")
            return await self._search_web_fallback(company_name)
    
    async def _search_ecourts(self, company_name: str) -> Dict[str, Any]:
        """
        Search using eCourts India API
        """
        
        try:
            # eCourts requires state, district, and court codes
            # For company search, we'll try multiple jurisdictions
            
            jurisdictions = [
                {"state_code": "07", "dist_code": "01", "court_code": "001"},  # Mumbai
                {"state_code": "24", "dist_code": "01", "court_code": "001"},  # Delhi
                {"state_code": "20", "dist_code": "01", "court_code": "001"},  # Bangalore
            ]
            
            all_cases = []
            
            for jurisdiction in jurisdictions:
                try:
                    payload = {
                        **jurisdiction,
                        "party_name": company_name
                    }
                    
                    response = requests.post(
                        "https://services.ecourts.gov.in/ecourtindia_v6/case_status_party.php",
                        data=payload,
                        timeout=self.timeout
                    )
                    
                    if response.status_code == 200:
                        cases = response.json().get("cases", [])
                        all_cases.extend(cases)
                        
                except Exception as e:
                    print(f"Error searching jurisdiction {jurisdiction}: {e}")
                    continue
            
            return self._parse_ecourts_response(company_name, all_cases)
            
        except Exception as e:
            print(f"eCourts API error: {e}")
            return await self._search_web_fallback(company_name)
    
    async def _search_qilegal(self, company_name: str) -> Dict[str, Any]:
        """
        Search using QiLegal API
        """
        
        try:
            headers = {
                "X-API-Key": self.qilegal_key,
                "Content-Type": "application/json"
            }
            
            payload = {
                "party_name": company_name,
                "court_type": ["district", "high", "supreme"],
                "limit": 50
            }
            
            response = requests.post(
                "https://api.qilegal.com/v1/search/cases",
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            data = response.json()
            
            return self._parse_qilegal_response(company_name, data)
            
        except Exception as e:
            print(f"QiLegal API error: {e}")
            return await self._search_web_fallback(company_name)
    
    async def _search_web_fallback(self, company_name: str) -> Dict[str, Any]:
        """
        Fallback to web search + AI analysis
        """
        # Import here to avoid circular dependency
        from app.api.company_insights import generate_legal_risk_assessment
        return await generate_legal_risk_assessment(company_name)
    
    def _parse_vakeel360_response(self, company_name: str, data: Dict) -> Dict[str, Any]:
        """
        Parse Vakeel360 API response
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
                "description": case.get("case_title", "No description"),
                "case_number": case.get("case_number", "N/A"),
                "filing_date": case.get("filing_date", ""),
                "court_name": case.get("court_name", ""),
                "estimated_year": case.get("filing_date", "")[:4] if case.get("filing_date") else "unknown"
            }
            
            if case_status in ["pending", "ongoing", "active"]:
                severity = self._assess_case_severity(case)
                
                ongoing_cases.append({
                    **case_info,
                    "severity": severity,
                    "status": "ongoing",
                    "financial_impact": f"Claim amount: {case.get('claim_amount', 'Not specified')}",
                    "credit_risk_impact": f"Ongoing {case_type} case may impact creditworthiness",
                    "next_hearing": case.get("next_hearing_date", "Not scheduled")
                })
            else:
                past_cases.append({
                    **case_info,
                    "outcome": case.get("judgment", "Case concluded"),
                    "year": case.get("filing_date", "")[:4] if case.get("filing_date") else "unknown"
                })
        
        risk_level = self._calculate_risk_level(ongoing_cases, past_cases)
        
        return {
            "summary": f"Found {len(cases)} legal cases for {company_name} through Vakeel360 API.",
            "ongoing_cases": ongoing_cases[:10],
            "past_cases": past_cases[:10],
            "regulatory_actions": regulatory_actions,
            "risk_assessment": {
                "overall_risk_level": risk_level,
                "credit_impact": "negative" if len(ongoing_cases) > 3 else "neutral" if len(ongoing_cases) > 0 else "positive",
                "key_concerns": self._generate_concerns(ongoing_cases),
                "mitigating_factors": self._generate_mitigating_factors(past_cases, ongoing_cases),
                "recommendation": self._generate_recommendation(risk_level, ongoing_cases)
            },
            "data_source": "vakeel360_api",
            "search_results_count": len(cases),
            "last_checked": datetime.utcnow().strftime('%Y-%m-%d'),
            "requires_manual_verification": False,
            "api_status": "success"
        }
    
    def _parse_ecourts_response(self, company_name: str, cases: List) -> Dict[str, Any]:
        """
        Parse eCourts API response
        """
        
        ongoing_cases = []
        past_cases = []
        
        for case in cases:
            case_status = case.get("case_status", "").lower()
            
            case_info = {
                "case_type": case.get("case_type", "civil"),
                "description": case.get("case_title", "No description"),
                "case_number": case.get("case_number", "N/A"),
                "filing_date": case.get("date_of_filing", ""),
                "court_name": case.get("court_name", ""),
                "estimated_year": case.get("date_of_filing", "")[:4] if case.get("date_of_filing") else "unknown"
            }
            
            if "disposed" not in case_status and "closed" not in case_status:
                ongoing_cases.append({
                    **case_info,
                    "severity": "medium",
                    "status": "ongoing",
                    "financial_impact": "Not specified",
                    "credit_risk_impact": "Ongoing case may impact creditworthiness"
                })
            else:
                past_cases.append({
                    **case_info,
                    "outcome": case.get("disposal_nature", "Disposed"),
                    "year": case.get("date_of_filing", "")[:4] if case.get("date_of_filing") else "unknown"
                })
        
        risk_level = self._calculate_risk_level(ongoing_cases, past_cases)
        
        return {
            "summary": f"Found {len(cases)} legal cases for {company_name} through eCourts India API.",
            "ongoing_cases": ongoing_cases[:10],
            "past_cases": past_cases[:10],
            "regulatory_actions": [],
            "risk_assessment": {
                "overall_risk_level": risk_level,
                "credit_impact": "negative" if len(ongoing_cases) > 3 else "neutral" if len(ongoing_cases) > 0 else "positive",
                "key_concerns": self._generate_concerns(ongoing_cases),
                "mitigating_factors": self._generate_mitigating_factors(past_cases, ongoing_cases),
                "recommendation": self._generate_recommendation(risk_level, ongoing_cases)
            },
            "data_source": "ecourts_api",
            "search_results_count": len(cases),
            "last_checked": datetime.utcnow().strftime('%Y-%m-%d'),
            "requires_manual_verification": True,
            "note": "eCourts data may be incomplete. Please verify through official portal.",
            "api_status": "success"
        }
    
    def _parse_qilegal_response(self, company_name: str, data: Dict) -> Dict[str, Any]:
        """
        Parse QiLegal API response
        """
        # Similar to Vakeel360 parsing
        return self._parse_vakeel360_response(company_name, data)
    
    def _assess_case_severity(self, case: Dict) -> str:
        """
        Assess severity of a legal case
        """
        case_type = case.get("case_type", "").lower()
        claim_amount_str = str(case.get("claim_amount", "0"))
        
        # Try to extract numeric value
        try:
            claim_amount = float(''.join(filter(str.isdigit, claim_amount_str)))
        except:
            claim_amount = 0
        
        # Criminal cases are high severity
        if "criminal" in case_type:
            return "high"
        
        # Check claim amount
        if claim_amount > 10000000:  # > 1 crore
            return "critical"
        elif claim_amount > 1000000:  # > 10 lakhs
            return "high"
        elif claim_amount > 100000:  # > 1 lakh
            return "medium"
        
        return "medium" if "civil" in case_type else "low"
    
    def _calculate_risk_level(self, ongoing: List, past: List) -> str:
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
            high_severity = sum(1 for c in ongoing if c.get("severity") in ["high", "critical"])
            if high_severity >= 2:
                return "high"
            elif high_severity >= 1:
                return "medium"
        
        return "low"
    
    def _generate_concerns(self, ongoing_cases: List) -> List[str]:
        """
        Generate key concerns from ongoing cases
        """
        if not ongoing_cases:
            return []
        
        concerns = []
        
        if len(ongoing_cases) > 5:
            concerns.append(f"High volume of ongoing cases ({len(ongoing_cases)} active cases)")
        
        high_severity = [c for c in ongoing_cases if c.get("severity") in ["high", "critical"]]
        if high_severity:
            concerns.append(f"{len(high_severity)} high-severity cases requiring attention")
        
        criminal_cases = [c for c in ongoing_cases if "criminal" in c.get("case_type", "").lower()]
        if criminal_cases:
            concerns.append(f"{len(criminal_cases)} criminal cases may impact reputation")
        
        if not concerns:
            concerns.append("Multiple ongoing legal proceedings")
        
        return concerns[:5]
    
    def _generate_mitigating_factors(self, past_cases: List, ongoing_cases: List) -> List[str]:
        """
        Generate mitigating factors
        """
        factors = []
        
        if len(ongoing_cases) == 0:
            factors.append("No ongoing legal cases found")
        elif len(ongoing_cases) < 3:
            factors.append("Limited number of active cases")
        
        if past_cases:
            factors.append(f"Track record of {len(past_cases)} resolved cases")
        
        low_severity = [c for c in ongoing_cases if c.get("severity") == "low"]
        if low_severity:
            factors.append(f"{len(low_severity)} cases are low severity")
        
        if not factors:
            factors.append("Company has legal representation")
        
        return factors[:5]
    
    def _generate_recommendation(self, risk_level: str, ongoing_cases: List) -> str:
        """
        Generate recommendation for lenders
        """
        if risk_level == "low":
            return "Legal risk is minimal. Proceed with standard due diligence."
        elif risk_level == "medium":
            return "Moderate legal risk identified. Review ongoing cases and assess potential financial impact before proceeding."
        else:
            return "High legal risk detected. Conduct thorough legal due diligence, consult legal counsel, and consider additional collateral or guarantees."


# Global instance
legal_api_service = LegalCaseAPIService()
