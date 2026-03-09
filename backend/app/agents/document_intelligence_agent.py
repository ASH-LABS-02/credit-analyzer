"""
Document Intelligence Agent

This agent uses OpenAI API to extract structured financial data from documents.
It identifies financial metrics, tracks source pages, and flags ambiguous data.

Requirements: 2.1, 2.2, 2.3, 2.5
"""

import json
import re
from typing import Dict, List, Optional, Any
from openai import AsyncOpenAI

from app.core.config import settings
from app.core.retry import retry_with_backoff, RetryConfig
from app.core.audit_logger import AuditLogger
from app.models.domain import Document
from app.repositories.document_repository import DocumentRepository
from app.services.document_processor import DocumentProcessor


class DocumentIntelligenceAgent:
    """
    AI agent for extracting structured financial data from documents.
    
    Uses OpenAI GPT-4 to:
    - Extract financial metrics (revenue, profit, debt, cash flow, ratios)
    - Structure data in standardized format
    - Track source pages for traceability
    - Flag ambiguous or unclear data
    
    Requirements: 2.1, 2.2, 2.3, 2.5
    """
    
    def __init__(
        self,
        document_repository: DocumentRepository,
        document_processor: DocumentProcessor,
        audit_logger: Optional[AuditLogger] = None
    ):
        """
        Initialize the Document Intelligence Agent.
        
        Args:
            document_repository: Repository for document data access
            document_processor: Service for document text extraction
            audit_logger: Optional audit logger for AI decision logging
        """
        self.openai = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.document_repository = document_repository
        self.document_processor = document_processor
        self.audit_logger = audit_logger
    
    async def extract(self, application_id: str) -> Dict[str, Any]:
        """
        Extract structured financial data from all documents in an application.
        
        Args:
            application_id: The application ID to process documents for
            
        Returns:
            Dictionary containing:
                - financial_data: Extracted financial metrics
                - source_tracking: Mapping of data to source documents/pages
                - ambiguous_flags: List of flagged ambiguous data
                - documents_processed: Number of documents processed
        
        Requirements: 2.1, 2.2, 2.3, 2.5
        """
        # Get all documents for the application
        documents = await self.document_repository.get_by_application(application_id)
        
        if not documents:
            return {
                "financial_data": {},
                "source_tracking": {},
                "ambiguous_flags": [],
                "documents_processed": 0
            }
        
        # Extract data from each document
        all_extracted_data = []
        for doc in documents:
            try:
                extracted = await self._extract_from_document(doc)
                all_extracted_data.append(extracted)
            except Exception as e:
                # Log error but continue processing other documents
                print(f"Error processing document {doc.id}: {str(e)}")
                continue
        
        # Merge data from all documents
        merged_data = self._merge_extracted_data(all_extracted_data)
        
        # Log AI decision
        if self.audit_logger:
            try:
                await self.audit_logger.log_ai_decision(
                    agent_name='DocumentIntelligenceAgent',
                    application_id=application_id,
                    decision=f"Extracted financial data from {merged_data['documents_processed']} documents",
                    reasoning=f"Processed {len(documents)} documents, successfully extracted data from {merged_data['documents_processed']}. "
                             f"Identified {len(merged_data['ambiguous_flags'])} ambiguous data points requiring review.",
                    data_sources=[doc.id for doc in documents],
                    additional_details={
                        'documents_processed': merged_data['documents_processed'],
                        'ambiguous_flags_count': len(merged_data['ambiguous_flags']),
                        'metrics_extracted': list(merged_data['financial_data'].keys()),
                        'source_tracking_count': len(merged_data['source_tracking'])
                    }
                )
            except Exception as e:
                # Log error but don't fail the extraction
                print(f"Error logging AI decision: {str(e)}")
        
        return merged_data
    
    async def _extract_from_document(self, document: Document) -> Dict[str, Any]:
        """
        Extract structured data from a single document.
        
        Args:
            document: Document object with metadata
            
        Returns:
            Dictionary with extracted data, source pages, and ambiguous flags
        """
        # Get document text (from storage or extract if needed)
        # For now, we'll assume the document content needs to be fetched
        # In production, this would fetch from Firebase Storage
        text = document.extracted_data.get("text", "") if document.extracted_data else ""
        
        if not text:
            # If no text available, return empty result
            return {
                "document_id": document.id,
                "data": {},
                "source_pages": {},
                "ambiguous_flags": []
            }
        
        # Build extraction prompt
        prompt = self._build_extraction_prompt(text)
        
        # Call OpenAI API for structured extraction with retry logic
        # Configure retry for OpenAI API calls (transient failures, rate limits, etc.)
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
                    "content": "You are a financial data extraction expert. Extract structured financial information from documents accurately."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            response_format={"type": "json_object"},
            temperature=0.1,  # Low temperature for consistent extraction
            config=retry_config
        )
        
        # Parse the response
        structured_data = json.loads(response.choices[0].message.content)
        
        # Identify source pages for extracted data
        source_pages = self._identify_source_pages(text, structured_data)
        
        # Flag ambiguous data
        ambiguous_flags = self._flag_ambiguous_data(structured_data)
        
        return {
            "document_id": document.id,
            "data": structured_data,
            "source_pages": source_pages,
            "ambiguous_flags": ambiguous_flags
        }
    
    def _build_extraction_prompt(self, text: str) -> str:
        """
        Build the extraction prompt for OpenAI.
        
        Args:
            text: Document text to extract from
            
        Returns:
            Formatted prompt string
        """
        prompt = f"""Extract financial data from the following document text. 

Return a JSON object with the following structure:
{{
    "company_info": {{
        "company_name": "string or null",
        "industry": "string or null",
        "fiscal_year": "string or null"
    }},
    "financial_metrics": {{
        "revenue": {{
            "values": [list of numbers for multiple years],
            "years": [corresponding years],
            "currency": "string",
            "confidence": "high/medium/low"
        }},
        "profit": {{
            "values": [list of numbers],
            "years": [corresponding years],
            "currency": "string",
            "confidence": "high/medium/low"
        }},
        "debt": {{
            "values": [list of numbers],
            "years": [corresponding years],
            "currency": "string",
            "confidence": "high/medium/low"
        }},
        "cash_flow": {{
            "values": [list of numbers],
            "years": [corresponding years],
            "currency": "string",
            "confidence": "high/medium/low"
        }},
        "current_assets": {{
            "value": number or null,
            "year": "string",
            "confidence": "high/medium/low"
        }},
        "current_liabilities": {{
            "value": number or null,
            "year": "string",
            "confidence": "high/medium/low"
        }},
        "total_assets": {{
            "value": number or null,
            "year": "string",
            "confidence": "high/medium/low"
        }},
        "total_equity": {{
            "value": number or null,
            "year": "string",
            "confidence": "high/medium/low"
        }},
        "total_debt": {{
            "value": number or null,
            "year": "string",
            "confidence": "high/medium/low"
        }}
    }},
    "financial_ratios": {{
        "current_ratio": {{
            "value": number or null,
            "confidence": "high/medium/low"
        }},
        "debt_to_equity": {{
            "value": number or null,
            "confidence": "high/medium/low"
        }},
        "net_profit_margin": {{
            "value": number or null,
            "confidence": "high/medium/low"
        }},
        "roe": {{
            "value": number or null,
            "confidence": "high/medium/low"
        }}
    }},
    "notes": [
        "List any ambiguities, unclear data, or assumptions made during extraction"
    ]
}}

Important:
- Extract all numerical values without currency symbols or commas
- If data is unclear or ambiguous, set confidence to "low" and add a note
- If data is not found, use null
- For multi-year data, ensure values and years arrays have the same length
- Include page references in notes when possible (e.g., "Revenue from page 3")

Document text:
{text[:8000]}  # Limit to first 8000 characters to stay within token limits
"""
        return prompt
    
    def _identify_source_pages(
        self, 
        text: str, 
        structured_data: Dict[str, Any]
    ) -> Dict[str, int]:
        """
        Identify source pages for extracted data fields.
        
        Args:
            text: Original document text with page markers
            structured_data: Extracted structured data
            
        Returns:
            Dictionary mapping data field paths to page numbers
        
        Requirements: 2.5
        """
        source_pages = {}
        
        # Extract page markers from text
        page_pattern = r'\[Page (\d+)\]'
        page_markers = list(re.finditer(page_pattern, text))
        
        if not page_markers:
            # No page markers found, return empty mapping
            return source_pages
        
        # For each financial metric, try to find which page it came from
        financial_metrics = structured_data.get("financial_metrics", {})
        
        for metric_name, metric_data in financial_metrics.items():
            if isinstance(metric_data, dict):
                # Try to find the metric name or values in the text
                search_terms = [metric_name]
                
                # Add values to search terms
                if "value" in metric_data and metric_data["value"]:
                    search_terms.append(str(metric_data["value"]))
                elif "values" in metric_data and metric_data["values"]:
                    search_terms.extend([str(v) for v in metric_data["values"][:2]])
                
                # Find the page where this metric appears
                for term in search_terms:
                    term_lower = term.lower().replace("_", " ")
                    text_lower = text.lower()
                    
                    if term_lower in text_lower:
                        term_pos = text_lower.index(term_lower)
                        
                        # Find the closest preceding page marker
                        page_num = 1  # Default to page 1
                        for marker in page_markers:
                            if marker.start() <= term_pos:
                                page_num = int(marker.group(1))
                            else:
                                break
                        
                        source_pages[f"financial_metrics.{metric_name}"] = page_num
                        break
        
        # Do the same for ratios
        financial_ratios = structured_data.get("financial_ratios", {})
        for ratio_name, ratio_data in financial_ratios.items():
            if isinstance(ratio_data, dict) and ratio_data.get("value"):
                ratio_lower = ratio_name.lower().replace("_", " ")
                text_lower = text.lower()
                
                if ratio_lower in text_lower:
                    ratio_pos = text_lower.index(ratio_lower)
                    
                    page_num = 1
                    for marker in page_markers:
                        if marker.start() <= ratio_pos:
                            page_num = int(marker.group(1))
                        else:
                            break
                    
                    source_pages[f"financial_ratios.{ratio_name}"] = page_num
        
        return source_pages
    
    def _flag_ambiguous_data(self, structured_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Flag ambiguous or unclear data for user review.
        
        Args:
            structured_data: Extracted structured data
            
        Returns:
            List of ambiguous data flags with field name, reason, and value
        
        Requirements: 2.3
        """
        ambiguous_flags = []
        
        # Check for low confidence extractions
        financial_metrics = structured_data.get("financial_metrics", {})
        for metric_name, metric_data in financial_metrics.items():
            if isinstance(metric_data, dict):
                confidence = metric_data.get("confidence", "high")
                if confidence == "low":
                    ambiguous_flags.append({
                        "field": f"financial_metrics.{metric_name}",
                        "reason": "Low confidence extraction",
                        "value": str(metric_data.get("value") or metric_data.get("values")),
                        "severity": "medium"
                    })
        
        # Check for missing critical data
        critical_metrics = ["revenue", "profit", "total_assets", "total_equity"]
        for metric in critical_metrics:
            metric_data = financial_metrics.get(metric, {})
            if isinstance(metric_data, dict):
                value = metric_data.get("value") or metric_data.get("values")
                if not value or (isinstance(value, list) and not any(value)):
                    ambiguous_flags.append({
                        "field": f"financial_metrics.{metric}",
                        "reason": "Critical metric not found in document",
                        "value": "null",
                        "severity": "high"
                    })
        
        # Check notes for ambiguities
        notes = structured_data.get("notes", [])
        for note in notes:
            if any(keyword in note.lower() for keyword in ["unclear", "ambiguous", "assumption", "uncertain"]):
                ambiguous_flags.append({
                    "field": "general",
                    "reason": note,
                    "value": "",
                    "severity": "low"
                })
        
        return ambiguous_flags
    
    def _merge_extracted_data(
        self, 
        extracted_data_list: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Merge extracted data from multiple documents.
        
        Args:
            extracted_data_list: List of extraction results from individual documents
            
        Returns:
            Merged data with combined financial metrics and source tracking
        """
        if not extracted_data_list:
            return {
                "financial_data": {},
                "source_tracking": {},
                "ambiguous_flags": [],
                "documents_processed": 0
            }
        
        merged_financial_data = {}
        merged_source_tracking = {}
        all_ambiguous_flags = []
        
        # Merge data from all documents
        for extraction in extracted_data_list:
            doc_id = extraction["document_id"]
            data = extraction["data"]
            source_pages = extraction["source_pages"]
            ambiguous_flags = extraction["ambiguous_flags"]
            
            # Merge financial metrics
            if "financial_metrics" in data:
                for metric_name, metric_data in data["financial_metrics"].items():
                    if metric_name not in merged_financial_data:
                        merged_financial_data[metric_name] = metric_data
                    else:
                        # If metric exists, prefer higher confidence data
                        existing_confidence = merged_financial_data[metric_name].get("confidence", "low")
                        new_confidence = metric_data.get("confidence", "low")
                        
                        confidence_order = {"high": 3, "medium": 2, "low": 1}
                        if confidence_order.get(new_confidence, 0) > confidence_order.get(existing_confidence, 0):
                            merged_financial_data[metric_name] = metric_data
            
            # Merge financial ratios
            if "financial_ratios" in data:
                if "financial_ratios" not in merged_financial_data:
                    merged_financial_data["financial_ratios"] = {}
                
                for ratio_name, ratio_data in data["financial_ratios"].items():
                    if ratio_name not in merged_financial_data["financial_ratios"]:
                        merged_financial_data["financial_ratios"][ratio_name] = ratio_data
                    else:
                        # Prefer higher confidence
                        existing_confidence = merged_financial_data["financial_ratios"][ratio_name].get("confidence", "low")
                        new_confidence = ratio_data.get("confidence", "low")
                        
                        confidence_order = {"high": 3, "medium": 2, "low": 1}
                        if confidence_order.get(new_confidence, 0) > confidence_order.get(existing_confidence, 0):
                            merged_financial_data["financial_ratios"][ratio_name] = ratio_data
            
            # Merge company info
            if "company_info" in data:
                if "company_info" not in merged_financial_data:
                    merged_financial_data["company_info"] = data["company_info"]
            
            # Add source tracking with document ID
            for field_path, page_num in source_pages.items():
                merged_source_tracking[field_path] = {
                    "document_id": doc_id,
                    "page": page_num
                }
            
            # Collect all ambiguous flags
            for flag in ambiguous_flags:
                flag["document_id"] = doc_id
                all_ambiguous_flags.append(flag)
        
        return {
            "financial_data": merged_financial_data,
            "source_tracking": merged_source_tracking,
            "ambiguous_flags": all_ambiguous_flags,
            "documents_processed": len(extracted_data_list)
        }
