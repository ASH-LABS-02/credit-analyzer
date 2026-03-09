"""
Orchestrator Agent

This agent coordinates the complete credit analysis workflow across all specialized agents.
It manages task dependencies, executes research agents in parallel, handles errors gracefully,
and aggregates results into a unified analysis.

Requirements: 3.1, 3.5, 15.1
"""

import asyncio
import traceback
from typing import Dict, List, Optional, Any
from datetime import datetime

from app.agents.document_intelligence_agent import DocumentIntelligenceAgent
from app.agents.financial_analysis_agent import FinancialAnalysisAgent
from app.agents.web_research_agent import WebResearchAgent
from app.agents.promoter_intelligence_agent import PromoterIntelligenceAgent
from app.agents.industry_intelligence_agent import IndustryIntelligenceAgent
from app.agents.forecasting_agent import ForecastingAgent
from app.agents.risk_scoring_agent import RiskScoringAgent
from app.agents.cam_generator_agent import CAMGeneratorAgent
from app.repositories.document_repository import DocumentRepository
from app.repositories.application_repository import ApplicationRepository
from app.services.document_processor import DocumentProcessor


class OrchestratorAgent:
    """
    Orchestrator agent that coordinates the complete credit analysis workflow.
    
    Workflow stages:
    1. Document Intelligence: Extract financial data from documents
    2. Parallel Research: Web research, promoter analysis, industry analysis (concurrent)
    3. Financial Analysis: Analyze extracted financial data
    4. Forecasting: Generate 3-year projections
    5. Risk Scoring: Calculate weighted risk score and recommendation
    6. CAM Generation: Compile comprehensive credit appraisal memo
    
    Features:
    - Parallel execution of independent research agents for efficiency
    - Error recovery and graceful degradation
    - Detailed logging of all agent activities
    - Result aggregation and validation
    
    Requirements: 3.1, 3.5, 15.1
    """
    
    def __init__(
        self,
        document_repository: DocumentRepository,
        application_repository: ApplicationRepository,
        document_processor: DocumentProcessor,
        audit_logger: Optional['AuditLogger'] = None
    ):
        """
        Initialize the Orchestrator Agent with all specialized agents.
        
        Args:
            document_repository: Repository for document data access
            application_repository: Repository for application data access
            document_processor: Service for document processing
            audit_logger: Optional audit logger for AI decision logging
        """
        # Initialize all specialized agents with audit logger
        self.document_intelligence = DocumentIntelligenceAgent(
            document_repository,
            document_processor,
            audit_logger
        )
        self.financial_analysis = FinancialAnalysisAgent(audit_logger)
        self.web_research = WebResearchAgent(audit_logger)
        self.promoter_intelligence = PromoterIntelligenceAgent(audit_logger)
        self.industry_intelligence = IndustryIntelligenceAgent(audit_logger)
        self.forecasting = ForecastingAgent(audit_logger)
        self.risk_scoring = RiskScoringAgent(audit_logger)
        self.cam_generator = CAMGeneratorAgent(audit_logger)
        
        # Store repositories for application data access
        self.application_repository = application_repository
        self.document_repository = document_repository
        self.audit_logger = audit_logger
        
        # Error tracking
        self.errors = []
        self.warnings = []
    
    async def process_application(self, application_id: str) -> Dict[str, Any]:
        """
        Orchestrate the complete analysis workflow for an application.
        
        This is the main entry point that coordinates all agents in the correct
        sequence, handles errors gracefully, and aggregates results.
        
        Args:
            application_id: The application ID to process
        
        Returns:
            Dictionary containing:
                - success: Whether the workflow completed successfully
                - application_id: The application ID processed
                - extracted_data: Document intelligence results
                - financial_analysis: Financial analysis results
                - research: Combined research results (web, promoter, industry)
                - forecasts: Financial forecasts
                - risk_assessment: Risk scoring and recommendation
                - cam: Generated CAM document
                - errors: List of errors encountered
                - warnings: List of warnings
                - processing_time: Total processing time in seconds
                - timestamp: Completion timestamp
        
        Requirements: 3.1, 3.5, 15.1
        """
        start_time = datetime.utcnow()
        self.errors = []
        self.warnings = []
        
        try:
            # Get application details
            application = await self.application_repository.get(application_id)
            if not application:
                return self._error_result(
                    application_id,
                    f"Application {application_id} not found",
                    start_time
                )
            
            company_name = application.company_name
            
            # Stage 1: Document Intelligence
            self._log_stage("Document Intelligence")
            extracted_data = await self._execute_with_recovery(
                self.document_intelligence.extract,
                "Document Intelligence",
                application_id
            )
            
            if not extracted_data or not extracted_data.get("financial_data"):
                self.warnings.append(
                    "Document intelligence produced limited results. "
                    "Analysis will proceed with available data."
                )
            
            # Stage 2: Parallel Research (Web, Promoter, Industry)
            self._log_stage("Parallel Research")
            research_results = await self._execute_parallel_research(
                company_name,
                extracted_data
            )
            
            # Stage 3: Financial Analysis
            self._log_stage("Financial Analysis")
            financial_analysis = await self._execute_with_recovery(
                self.financial_analysis.analyze,
                "Financial Analysis",
                extracted_data
            )
            
            if not financial_analysis:
                financial_analysis = {
                    "ratios": {},
                    "trends": {},
                    "benchmarks": {},
                    "summary": "Financial analysis could not be completed due to insufficient data.",
                    "definitions": {}
                }
                self.warnings.append("Financial analysis produced limited results.")
            
            # Stage 4: Forecasting
            self._log_stage("Forecasting")
            forecasts = await self._execute_with_recovery(
                self.forecasting.predict,
                "Forecasting",
                {
                    "historical": extracted_data.get("financial_data", {}),
                    "financial_analysis": financial_analysis,
                    "company_info": extracted_data.get("financial_data", {}).get("company_info", {})
                }
            )
            
            if not forecasts or not forecasts.get("forecasts"):
                forecasts = {
                    "forecasts": {},
                    "assumptions": ["Insufficient data for forecasting"],
                    "methodology": "Forecasting could not be completed",
                    "confidence_level": 0.0
                }
                self.warnings.append("Forecasting produced limited results.")
            
            # Stage 5: Risk Scoring
            self._log_stage("Risk Scoring")
            risk_assessment = await self._execute_with_recovery(
                self.risk_scoring.score,
                "Risk Scoring",
                {
                    "financial": financial_analysis,
                    "forecasts": forecasts,
                    "research": research_results
                }
            )
            
            if not risk_assessment:
                # Create a default risk assessment if scoring fails
                from app.models.domain import RiskAssessment, CreditRecommendation, RiskFactorScore
                risk_assessment = RiskAssessment(
                    overall_score=50.0,
                    recommendation=CreditRecommendation.APPROVE_WITH_CONDITIONS,
                    financial_health=RiskFactorScore(
                        factor_name="financial_health",
                        score=50.0,
                        weight=0.35,
                        explanation="Unable to assess due to errors",
                        key_findings=[]
                    ),
                    cash_flow=RiskFactorScore(
                        factor_name="cash_flow",
                        score=50.0,
                        weight=0.25,
                        explanation="Unable to assess due to errors",
                        key_findings=[]
                    ),
                    industry=RiskFactorScore(
                        factor_name="industry",
                        score=50.0,
                        weight=0.15,
                        explanation="Unable to assess due to errors",
                        key_findings=[]
                    ),
                    promoter=RiskFactorScore(
                        factor_name="promoter",
                        score=50.0,
                        weight=0.15,
                        explanation="Unable to assess due to errors",
                        key_findings=[]
                    ),
                    external_intelligence=RiskFactorScore(
                        factor_name="external_intelligence",
                        score=50.0,
                        weight=0.10,
                        explanation="Unable to assess due to errors",
                        key_findings=[]
                    ),
                    summary="Risk assessment could not be completed due to errors in the analysis pipeline."
                )
                self.errors.append("Risk scoring failed. Using default neutral assessment.")
            
            # Stage 6: CAM Generation
            self._log_stage("CAM Generation")
            cam = await self._execute_with_recovery(
                self.cam_generator.generate,
                "CAM Generation",
                {
                    "application_id": application_id,
                    "company_name": company_name,
                    "loan_amount": application.loan_amount,
                    "loan_purpose": application.loan_purpose,
                    "extracted_data": extracted_data,
                    "financial_analysis": financial_analysis,
                    "forecasts": forecasts,
                    "risk_assessment": risk_assessment,
                    "research": research_results
                }
            )
            
            if not cam:
                cam = {
                    "content": "CAM generation failed. Please review individual analysis components.",
                    "sections": {},
                    "generated_at": datetime.utcnow().isoformat()
                }
                self.errors.append("CAM generation failed.")
            
            # Calculate processing time
            end_time = datetime.utcnow()
            processing_time = (end_time - start_time).total_seconds()
            
            # Aggregate results
            result = {
                "success": len(self.errors) == 0,
                "application_id": application_id,
                "company_name": company_name,
                "extracted_data": extracted_data,
                "financial_analysis": financial_analysis,
                "research": research_results,
                "forecasts": forecasts,
                "risk_assessment": self._serialize_risk_assessment(risk_assessment),
                "cam": cam,
                "errors": self.errors,
                "warnings": self.warnings,
                "processing_time": processing_time,
                "timestamp": end_time.isoformat()
            }
            
            self._log_completion(processing_time, len(self.errors), len(self.warnings))
            
            return result
        
        except Exception as e:
            # Catch-all error handler for unexpected failures
            error_msg = f"Unexpected error in orchestration: {str(e)}"
            self.errors.append(error_msg)
            print(f"ERROR: {error_msg}")
            print(traceback.format_exc())
            
            end_time = datetime.utcnow()
            processing_time = (end_time - start_time).total_seconds()
            
            return self._error_result(application_id, error_msg, start_time)
    
    async def _execute_parallel_research(
        self,
        company_name: str,
        extracted_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute research agents in parallel for efficiency.
        
        Runs web research, promoter intelligence, and industry intelligence
        concurrently since they are independent of each other.
        
        Args:
            company_name: Company name for research
            extracted_data: Extracted data for context
        
        Returns:
            Dictionary containing results from all research agents
        
        Requirements: 3.1, 3.5
        """
        # Extract context for research
        company_info = extracted_data.get("financial_data", {}).get("company_info", {})
        industry = company_info.get("industry") if isinstance(company_info, dict) else None
        
        # Create research tasks
        research_tasks = [
            self._execute_with_recovery(
                self.web_research.research,
                "Web Research",
                company_name,
                {"industry": industry}
            ),
            self._execute_with_recovery(
                self.promoter_intelligence.analyze,
                "Promoter Intelligence",
                company_name,
                None,  # promoters list
                {"industry": industry}
            ),
            self._execute_with_recovery(
                self.industry_intelligence.analyze,
                "Industry Intelligence",
                company_name,
                industry,
                {"company_info": company_info}
            )
        ]
        
        # Execute all research tasks in parallel
        research_results = await asyncio.gather(*research_tasks, return_exceptions=True)
        
        # Process results and handle any exceptions
        web_research_result = research_results[0]
        promoter_result = research_results[1]
        industry_result = research_results[2]
        
        # Handle exceptions and None results
        if isinstance(web_research_result, Exception) or web_research_result is None:
            if isinstance(web_research_result, Exception):
                self.errors.append(f"Web Research failed: {str(web_research_result)}")
            web_research_result = self._empty_web_research_result()
        
        if isinstance(promoter_result, Exception) or promoter_result is None:
            if isinstance(promoter_result, Exception):
                self.errors.append(f"Promoter Intelligence failed: {str(promoter_result)}")
            promoter_result = self._empty_promoter_result()
        
        if isinstance(industry_result, Exception) or industry_result is None:
            if isinstance(industry_result, Exception):
                self.errors.append(f"Industry Intelligence failed: {str(industry_result)}")
            industry_result = self._empty_industry_result()
        
        return {
            "web": web_research_result,
            "promoter": promoter_result,
            "industry": industry_result
        }
    
    async def _execute_with_recovery(
        self,
        agent_func,
        agent_name: str,
        *args,
        **kwargs
    ) -> Optional[Any]:
        """
        Execute an agent function with error recovery and logging.
        
        Implements graceful degradation by catching errors, logging them,
        and allowing the workflow to continue with partial results.
        
        Args:
            agent_func: The agent function to execute
            agent_name: Name of the agent for logging
            *args: Positional arguments for the agent function
            **kwargs: Keyword arguments for the agent function
        
        Returns:
            Agent result or None if execution fails
        
        Requirements: 15.1
        """
        try:
            print(f"[{agent_name}] Starting execution...")
            result = await agent_func(*args, **kwargs)
            print(f"[{agent_name}] Completed successfully")
            return result
        
        except Exception as e:
            error_msg = f"{agent_name} failed: {str(e)}"
            self.errors.append(error_msg)
            print(f"ERROR: {error_msg}")
            print(traceback.format_exc())
            
            # Log detailed error for debugging
            self._log_error(agent_name, e)
            
            # Return None to allow graceful degradation
            return None
    
    def _serialize_risk_assessment(self, risk_assessment: Any) -> Dict[str, Any]:
        """
        Serialize RiskAssessment object to dictionary.
        
        Args:
            risk_assessment: RiskAssessment object or dict
        
        Returns:
            Dictionary representation
        """
        if isinstance(risk_assessment, dict):
            return risk_assessment
        
        # Convert dataclass to dict
        try:
            from dataclasses import asdict
            return asdict(risk_assessment)
        except Exception:
            # Fallback: manual serialization
            return {
                "overall_score": risk_assessment.overall_score,
                "recommendation": risk_assessment.recommendation.value if hasattr(risk_assessment.recommendation, 'value') else str(risk_assessment.recommendation),
                "financial_health": self._serialize_risk_factor(risk_assessment.financial_health),
                "cash_flow": self._serialize_risk_factor(risk_assessment.cash_flow),
                "industry": self._serialize_risk_factor(risk_assessment.industry),
                "promoter": self._serialize_risk_factor(risk_assessment.promoter),
                "external_intelligence": self._serialize_risk_factor(risk_assessment.external_intelligence),
                "summary": risk_assessment.summary
            }
    
    def _serialize_risk_factor(self, risk_factor: Any) -> Dict[str, Any]:
        """Serialize RiskFactorScore to dictionary."""
        if isinstance(risk_factor, dict):
            return risk_factor
        
        try:
            from dataclasses import asdict
            return asdict(risk_factor)
        except Exception:
            return {
                "factor_name": risk_factor.factor_name,
                "score": risk_factor.score,
                "weight": risk_factor.weight,
                "explanation": risk_factor.explanation,
                "key_findings": risk_factor.key_findings
            }
    
    def _empty_web_research_result(self) -> Dict[str, Any]:
        """Return empty web research result for graceful degradation."""
        return {
            "summary": "Web research could not be completed.",
            "news_items": [],
            "red_flags": [],
            "positive_indicators": [],
            "sources": [],
            "research_date": datetime.utcnow().isoformat()
        }
    
    def _empty_promoter_result(self) -> Dict[str, Any]:
        """Return empty promoter intelligence result for graceful degradation."""
        return {
            "summary": "Promoter intelligence could not be completed.",
            "promoter_profiles": [],
            "track_record_analysis": {},
            "conflicts_of_interest": [],
            "red_flags": [],
            "positive_indicators": [],
            "overall_assessment": {},
            "analysis_date": datetime.utcnow().isoformat()
        }
    
    def _empty_industry_result(self) -> Dict[str, Any]:
        """Return empty industry intelligence result for graceful degradation."""
        return {
            "summary": "Industry intelligence could not be completed.",
            "industry": "Unknown",
            "sector_trends": {},
            "competitive_landscape": {},
            "industry_risks": [],
            "market_opportunities": [],
            "growth_outlook": {},
            "overall_assessment": {},
            "analysis_date": datetime.utcnow().isoformat()
        }
    
    def _error_result(
        self,
        application_id: str,
        error_message: str,
        start_time: datetime
    ) -> Dict[str, Any]:
        """
        Create an error result when the workflow cannot complete.
        
        Args:
            application_id: Application ID
            error_message: Error message
            start_time: Workflow start time
        
        Returns:
            Error result dictionary
        """
        end_time = datetime.utcnow()
        processing_time = (end_time - start_time).total_seconds()
        
        return {
            "success": False,
            "application_id": application_id,
            "company_name": "Unknown",
            "extracted_data": {},
            "financial_analysis": {},
            "research": {},
            "forecasts": {},
            "risk_assessment": {},
            "cam": {},
            "errors": [error_message] + self.errors,
            "warnings": self.warnings,
            "processing_time": processing_time,
            "timestamp": end_time.isoformat()
        }
    
    def _log_stage(self, stage_name: str):
        """Log the start of a workflow stage."""
        print(f"\n{'='*60}")
        print(f"STAGE: {stage_name}")
        print(f"{'='*60}")
    
    def _log_error(self, agent_name: str, error: Exception):
        """
        Log detailed error information for debugging.
        
        Args:
            agent_name: Name of the agent that failed
            error: The exception that occurred
        """
        error_details = {
            "agent": agent_name,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # In production, this would log to a proper logging system
        print(f"ERROR DETAILS: {error_details}")
    
    def _log_completion(self, processing_time: float, error_count: int, warning_count: int):
        """
        Log workflow completion summary.
        
        Args:
            processing_time: Total processing time in seconds
            error_count: Number of errors encountered
            warning_count: Number of warnings encountered
        """
        print(f"\n{'='*60}")
        print(f"WORKFLOW COMPLETED")
        print(f"{'='*60}")
        print(f"Processing Time: {processing_time:.2f} seconds")
        print(f"Errors: {error_count}")
        print(f"Warnings: {warning_count}")
        print(f"Status: {'SUCCESS' if error_count == 0 else 'COMPLETED WITH ERRORS'}")
        print(f"{'='*60}\n")
