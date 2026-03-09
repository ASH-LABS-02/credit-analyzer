"""AI agents for credit analysis"""

from app.agents.document_intelligence_agent import DocumentIntelligenceAgent
from app.agents.financial_analysis_agent import FinancialAnalysisAgent
from app.agents.web_research_agent import WebResearchAgent
from app.agents.promoter_intelligence_agent import PromoterIntelligenceAgent
from app.agents.industry_intelligence_agent import IndustryIntelligenceAgent
from app.agents.forecasting_agent import ForecastingAgent
from app.agents.risk_scoring_agent import RiskScoringAgent
from app.agents.cam_generator_agent import CAMGeneratorAgent
from app.agents.orchestrator_agent import OrchestratorAgent

__all__ = [
    "DocumentIntelligenceAgent",
    "FinancialAnalysisAgent",
    "WebResearchAgent",
    "PromoterIntelligenceAgent",
    "IndustryIntelligenceAgent",
    "ForecastingAgent",
    "RiskScoringAgent",
    "CAMGeneratorAgent",
    "OrchestratorAgent"
]
