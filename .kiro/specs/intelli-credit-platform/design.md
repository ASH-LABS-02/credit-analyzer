# Design Document: Intelli-Credit AI-Powered Corporate Credit Decisioning Platform

## Overview

The Intelli-Credit platform is a multi-tier AI-powered system that automates corporate credit analysis through intelligent document processing, multi-agent research, financial analysis, and automated report generation. The architecture follows a layered approach with clear separation between presentation, application logic, AI processing, and data persistence.

The system processes loan applications through a coordinated workflow:
1. Document upload and validation
2. AI-powered data extraction and structuring
3. Multi-agent intelligence gathering (web research, promoter analysis, industry evaluation)
4. Financial analysis and forecasting
5. Risk scoring and credit decision generation
6. CAM report compilation and export
7. Continuous post-approval monitoring

The platform is designed for high throughput (multiple concurrent applications), low latency (5-10 minute end-to-end processing), and explainability (transparent credit decisions with traceable reasoning).

## Architecture

### System Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface Layer                      │
│              (React.js + Tailwind + Framer Motion)          │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   Application API Layer                      │
│                    (FastAPI REST Endpoints)                  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      AI Agent Layer                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Orchestrator Agent                       │  │
│  └──────────────────────────────────────────────────────┘  │
│         ↓          ↓          ↓          ↓          ↓       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │Document  │ │Financial │ │Web       │ │Promoter  │      │
│  │Intel     │ │Analysis  │ │Research  │ │Intel     │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │Industry  │ │Forecast  │ │Risk      │ │CAM       │      │
│  │Intel     │ │          │ │Scoring   │ │Generator │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                  Data Processing Layer                       │
│              (Pandas, NumPy, FAISS Vector Search)           │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      Storage Layer                           │
│          (Firebase: Firestore, Authentication)              │
│     (Documents stored as base64 in Firestore)               │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

- **Frontend**: React.js 18+, Tailwind CSS, Framer Motion, React Router, Chart.js/Recharts
- **Backend**: Python 3.10+, FastAPI, Pydantic
- **AI/ML**: OpenAI API (GPT-4), LangChain for agent orchestration
- **Data Processing**: Pandas, NumPy, python-docx, PyPDF2, openpyxl
- **Vector Search**: FAISS for semantic document retrieval
- **Database**: Firebase Firestore (NoSQL document store for all data including documents)
- **Authentication**: Firebase Authentication
- **Deployment**: Docker, Docker Compose, cloud hosting (AWS/GCP/Azure)

**Note**: Documents are stored directly in Firestore as base64-encoded content rather than using Firebase Storage. This simplifies the architecture and enables atomic transactions across all data.

## Components and Interfaces

### 1. User Interface Layer

**Dashboard Component**
- Displays application list with status indicators
- Provides search and filtering capabilities
- Shows real-time processing progress

**Application Detail Component**
- Multi-tab interface: Overview, Documents, Financial Analysis, Risk Assessment, CAM
- Interactive charts for financial trends and forecasts
- Document viewer with semantic search
- Credit score visualization with factor breakdown

**Document Upload Component**
- Drag-and-drop file upload
- Multi-file selection support
- Upload progress indicators
- File validation feedback

**CAM Export Component**
- Format selection (PDF/Word)
- Template customization options
- Download management

### 2. Application API Layer

**FastAPI Endpoints**

```python
# Application Management
POST   /api/v1/applications                    # Create new application
GET    /api/v1/applications                    # List applications
GET    /api/v1/applications/{app_id}           # Get application details
PATCH  /api/v1/applications/{app_id}           # Update application
DELETE /api/v1/applications/{app_id}           # Delete application

# Document Operations
POST   /api/v1/applications/{app_id}/documents # Upload document
GET    /api/v1/applications/{app_id}/documents # List documents
GET    /api/v1/documents/{doc_id}              # Get document
DELETE /api/v1/documents/{doc_id}              # Delete document

# Analysis Operations
POST   /api/v1/applications/{app_id}/analyze   # Trigger analysis
GET    /api/v1/applications/{app_id}/status    # Get analysis status
GET    /api/v1/applications/{app_id}/results   # Get analysis results

# CAM Operations
POST   /api/v1/applications/{app_id}/cam       # Generate CAM
GET    /api/v1/applications/{app_id}/cam       # Get CAM content
GET    /api/v1/applications/{app_id}/cam/export # Export CAM (PDF/Word)

# Search Operations
POST   /api/v1/applications/{app_id}/search    # Semantic document search

# Monitoring Operations
GET    /api/v1/monitoring/alerts               # Get monitoring alerts
GET    /api/v1/monitoring/applications/{app_id} # Get monitoring status

# Authentication
POST   /api/v1/auth/login                      # User login
POST   /api/v1/auth/logout                     # User logout
GET    /api/v1/auth/me                         # Get current user
```

**Request/Response Models**

```python
# Application Models
class ApplicationCreate(BaseModel):
    company_name: str
    loan_amount: float
    loan_purpose: str
    applicant_email: str

class ApplicationResponse(BaseModel):
    id: str
    company_name: str
    loan_amount: float
    status: str  # "pending", "processing", "complete", "approved", "rejected"
    created_at: datetime
    updated_at: datetime
    credit_score: Optional[float]
    recommendation: Optional[str]

# Document Models
class DocumentUpload(BaseModel):
    file: UploadFile
    document_type: str  # "financial_statement", "bank_statement", "tax_return", etc.

class DocumentResponse(BaseModel):
    id: str
    application_id: str
    filename: str
    file_type: str
    upload_date: datetime
    processing_status: str
    storage_url: str

# Analysis Results Models
class FinancialMetrics(BaseModel):
    revenue: List[float]  # Multi-year
    profit: List[float]
    debt: List[float]
    cash_flow: List[float]
    current_ratio: float
    debt_to_equity: float
    roe: float
    # ... additional ratios

class RiskScore(BaseModel):
    overall_score: float  # 0-100
    financial_health_score: float
    cash_flow_score: float
    industry_score: float
    promoter_score: float
    external_intelligence_score: float
    recommendation: str  # "approve", "approve_with_conditions", "reject"
    explanation: str

class AnalysisResults(BaseModel):
    financial_metrics: FinancialMetrics
    forecasts: Dict[str, List[float]]  # 3-year projections
    risk_score: RiskScore
    research_summary: str
    promoter_analysis: str
    industry_analysis: str
```

### 3. AI Agent Layer

**Orchestrator Agent**
- Coordinates workflow across specialized agents
- Manages task dependencies and execution order
- Aggregates results from all agents
- Handles error recovery and retry logic

```python
class OrchestratorAgent:
    def __init__(self, openai_client, firestore_client):
        self.openai = openai_client
        self.db = firestore_client
        self.agents = self._initialize_agents()
    
    async def process_application(self, application_id: str) -> Dict:
        """
        Orchestrates the complete analysis workflow
        """
        # 1. Document Intelligence
        extracted_data = await self.agents['document'].extract(application_id)
        
        # 2. Parallel Research (Web, Promoter, Industry)
        research_tasks = [
            self.agents['web_research'].research(application_id),
            self.agents['promoter'].analyze(application_id),
            self.agents['industry'].analyze(application_id)
        ]
        research_results = await asyncio.gather(*research_tasks)
        
        # 3. Financial Analysis
        financial_analysis = await self.agents['financial'].analyze(extracted_data)
        
        # 4. Forecasting
        forecasts = await self.agents['forecast'].predict(financial_analysis)
        
        # 5. Risk Scoring
        risk_score = await self.agents['risk'].score({
            'financial': financial_analysis,
            'forecasts': forecasts,
            'research': research_results
        })
        
        # 6. CAM Generation
        cam = await self.agents['cam'].generate({
            'financial': financial_analysis,
            'forecasts': forecasts,
            'risk': risk_score,
            'research': research_results
        })
        
        return {
            'financial_analysis': financial_analysis,
            'forecasts': forecasts,
            'risk_score': risk_score,
            'cam': cam
        }
```

**Document Intelligence Agent**
- Extracts text from PDFs, DOCX, Excel, CSV, images
- Uses OpenAI API for structured data extraction
- Identifies financial metrics, dates, company information
- Handles multi-page documents and tables

```python
class DocumentIntelligenceAgent:
    async def extract(self, application_id: str) -> Dict:
        """
        Extract structured financial data from documents
        """
        documents = await self._get_documents(application_id)
        extracted_data = []
        
        for doc in documents:
            # Extract text based on file type
            text = await self._extract_text(doc)
            
            # Use OpenAI for structured extraction
            prompt = self._build_extraction_prompt(text)
            response = await self.openai.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            
            structured_data = json.loads(response.choices[0].message.content)
            extracted_data.append({
                'document_id': doc.id,
                'data': structured_data,
                'source_pages': self._identify_source_pages(text, structured_data)
            })
        
        return self._merge_extracted_data(extracted_data)
```

**Financial Analysis Agent**
- Calculates financial ratios (liquidity, leverage, profitability, efficiency)
- Computes year-over-year growth rates
- Identifies trends and anomalies
- Compares against industry benchmarks

**Web Research Agent**
- Searches for company news, press releases, regulatory filings
- Gathers market intelligence and competitive information
- Identifies red flags (lawsuits, defaults, negative news)
- Summarizes findings with source citations

**Promoter Intelligence Agent**
- Analyzes director backgrounds and track records
- Searches for past business ventures and outcomes
- Identifies conflicts of interest or reputation issues
- Assesses management quality and experience

**Industry Intelligence Agent**
- Evaluates sector trends and growth outlook
- Analyzes competitive landscape
- Assesses industry-specific risks
- Provides context for company performance

**Forecasting Agent**
- Generates 3-year projections for key metrics
- Uses historical trends and industry growth rates
- Incorporates economic indicators
- Provides confidence intervals

```python
class ForecastingAgent:
    async def predict(self, financial_data: Dict) -> Dict:
        """
        Generate 3-year financial forecasts
        """
        historical_data = financial_data['historical']
        
        # Calculate growth rates
        growth_rates = self._calculate_growth_rates(historical_data)
        
        # Get industry benchmarks
        industry_growth = await self._get_industry_growth_rate(
            financial_data['industry']
        )
        
        # Use OpenAI for intelligent forecasting
        prompt = self._build_forecast_prompt(
            historical_data, growth_rates, industry_growth
        )
        
        response = await self.openai.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        forecasts = json.loads(response.choices[0].message.content)
        
        return {
            'revenue': forecasts['revenue_projections'],
            'profit': forecasts['profit_projections'],
            'cash_flow': forecasts['cash_flow_projections'],
            'debt': forecasts['debt_projections'],
            'assumptions': forecasts['assumptions'],
            'confidence': forecasts['confidence_level']
        }
```

**Risk Scoring Agent**
- Calculates weighted risk score (0-100)
- Applies factor weights: financial health 35%, cash flow 25%, industry 15%, promoter 15%, external intelligence 10%
- Generates credit recommendation (approve/conditional/reject)
- Provides detailed explanation for each factor

```python
class RiskScoringAgent:
    WEIGHTS = {
        'financial_health': 0.35,
        'cash_flow': 0.25,
        'industry': 0.15,
        'promoter': 0.15,
        'external_intelligence': 0.10
    }
    
    async def score(self, analysis_data: Dict) -> RiskScore:
        """
        Calculate weighted risk score and recommendation
        """
        # Score each factor (0-100)
        scores = {
            'financial_health': self._score_financial_health(
                analysis_data['financial']
            ),
            'cash_flow': self._score_cash_flow(
                analysis_data['financial']
            ),
            'industry': self._score_industry(
                analysis_data['research']['industry']
            ),
            'promoter': self._score_promoter(
                analysis_data['research']['promoter']
            ),
            'external_intelligence': self._score_external(
                analysis_data['research']['web']
            )
        }
        
        # Calculate weighted overall score
        overall_score = sum(
            scores[factor] * self.WEIGHTS[factor]
            for factor in scores
        )
        
        # Determine recommendation
        if overall_score >= 70:
            recommendation = "approve"
        elif overall_score >= 40:
            recommendation = "approve_with_conditions"
        else:
            recommendation = "reject"
        
        # Generate explanation
        explanation = await self._generate_explanation(scores, overall_score)
        
        return RiskScore(
            overall_score=overall_score,
            financial_health_score=scores['financial_health'],
            cash_flow_score=scores['cash_flow'],
            industry_score=scores['industry'],
            promoter_score=scores['promoter'],
            external_intelligence_score=scores['external_intelligence'],
            recommendation=recommendation,
            explanation=explanation
        )
```

**CAM Generator Agent**
- Compiles all analysis results into structured report
- Formats content with professional styling
- Generates executive summary
- Creates exportable PDF/Word documents

### 4. Data Processing Layer

**Document Processing Pipeline**

```python
class DocumentProcessor:
    def __init__(self):
        self.pdf_extractor = PyPDF2.PdfReader
        self.docx_extractor = python_docx.Document
        self.excel_extractor = openpyxl.load_workbook
    
    async def process_document(self, file_path: str, file_type: str) -> str:
        """
        Extract text from various document formats
        """
        if file_type == 'pdf':
            return self._extract_from_pdf(file_path)
        elif file_type == 'docx':
            return self._extract_from_docx(file_path)
        elif file_type in ['xlsx', 'xls']:
            return self._extract_from_excel(file_path)
        elif file_type == 'csv':
            return self._extract_from_csv(file_path)
        elif file_type in ['jpg', 'jpeg', 'png']:
            return await self._extract_from_image(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
```

**Vector Search Engine**

```python
class VectorSearchEngine:
    def __init__(self, dimension: int = 1536):  # OpenAI embedding dimension
        self.index = faiss.IndexFlatL2(dimension)
        self.document_map = {}
        self.openai = OpenAI()
    
    async def index_document(self, doc_id: str, text: str):
        """
        Generate embeddings and add to FAISS index
        """
        # Split text into chunks
        chunks = self._chunk_text(text, chunk_size=500)
        
        # Generate embeddings
        embeddings = []
        for chunk in chunks:
            response = await self.openai.embeddings.create(
                model="text-embedding-ada-002",
                input=chunk
            )
            embeddings.append(response.data[0].embedding)
        
        # Add to FAISS index
        embeddings_array = np.array(embeddings).astype('float32')
        start_idx = self.index.ntotal
        self.index.add(embeddings_array)
        
        # Store document mapping
        for i, chunk in enumerate(chunks):
            self.document_map[start_idx + i] = {
                'doc_id': doc_id,
                'chunk': chunk,
                'chunk_index': i
            }
    
    async def search(self, query: str, k: int = 5) -> List[Dict]:
        """
        Semantic search across indexed documents
        """
        # Generate query embedding
        response = await self.openai.embeddings.create(
            model="text-embedding-ada-002",
            input=query
        )
        query_embedding = np.array([response.data[0].embedding]).astype('float32')
        
        # Search FAISS index
        distances, indices = self.index.search(query_embedding, k)
        
        # Return results
        results = []
        for i, idx in enumerate(indices[0]):
            if idx in self.document_map:
                results.append({
                    'doc_id': self.document_map[idx]['doc_id'],
                    'chunk': self.document_map[idx]['chunk'],
                    'relevance_score': float(1 / (1 + distances[0][i]))
                })
        
        return results
```

**Financial Calculator**

```python
class FinancialCalculator:
    @staticmethod
    def calculate_ratios(financial_data: Dict) -> Dict:
        """
        Calculate key financial ratios
        """
        ratios = {}
        
        # Liquidity Ratios
        if financial_data.get('current_assets') and financial_data.get('current_liabilities'):
            ratios['current_ratio'] = (
                financial_data['current_assets'] / financial_data['current_liabilities']
            )
        
        # Leverage Ratios
        if financial_data.get('total_debt') and financial_data.get('total_equity'):
            ratios['debt_to_equity'] = (
                financial_data['total_debt'] / financial_data['total_equity']
            )
        
        # Profitability Ratios
        if financial_data.get('net_income') and financial_data.get('revenue'):
            ratios['net_profit_margin'] = (
                financial_data['net_income'] / financial_data['revenue']
            )
        
        if financial_data.get('net_income') and financial_data.get('total_equity'):
            ratios['roe'] = (
                financial_data['net_income'] / financial_data['total_equity']
            )
        
        # Efficiency Ratios
        if financial_data.get('revenue') and financial_data.get('total_assets'):
            ratios['asset_turnover'] = (
                financial_data['revenue'] / financial_data['total_assets']
            )
        
        return ratios
    
    @staticmethod
    def calculate_growth_rates(time_series: List[float]) -> List[float]:
        """
        Calculate year-over-year growth rates
        """
        growth_rates = []
        for i in range(1, len(time_series)):
            if time_series[i-1] != 0:
                growth = ((time_series[i] - time_series[i-1]) / time_series[i-1]) * 100
                growth_rates.append(growth)
            else:
                growth_rates.append(0.0)
        return growth_rates
```

### 5. Storage Layer

**Firestore Data Model**

```
applications/
  {application_id}/
    - company_name: string
    - loan_amount: number
    - loan_purpose: string
    - status: string
    - created_at: timestamp
    - updated_at: timestamp
    - applicant_email: string
    - credit_score: number (optional)
    - recommendation: string (optional)
    
    documents/
      {document_id}/
        - filename: string
        - file_type: string
        - content_base64: string  # Base64-encoded document content
        - file_size: number
        - upload_date: timestamp
        - processing_status: string
        - extracted_data: map (optional)
        - chunk_count: number (optional, for large files)
        - chunk_ids: array (optional, for large files)
    
    analysis_results/
      - financial_metrics: map
      - forecasts: map
      - risk_score: map
      - research_summary: string
      - promoter_analysis: string
      - industry_analysis: string
      - generated_at: timestamp
    
    cam/
      - content: string
      - generated_at: timestamp
      - version: number

users/
  {user_id}/
    - email: string
    - role: string
    - created_at: timestamp
    - last_login: timestamp

monitoring/
  {application_id}/
    - monitoring_active: boolean
    - last_check: timestamp
    - alerts: array
      - alert_id: string
      - alert_type: string
      - severity: string
      - message: string
      - created_at: timestamp

audit_logs/
  {log_id}/
    - user_id: string
    - action: string
    - resource_type: string
    - resource_id: string
    - timestamp: timestamp
    - details: map
```

**Firebase Storage Structure**

Documents are stored directly in Firestore as base64-encoded content. For documents larger than 1MB (Firestore document size limit), the system uses chunking:

```
applications/{application_id}/documents/{document_id}
  - content_base64: string (for files < 1MB)
  - chunk_count: number (for files >= 1MB)
  - chunk_ids: array (for files >= 1MB)

applications/{application_id}/document_chunks/{chunk_id}
  - parent_doc_id: string
  - chunk_index: number
  - content_base64: string
  - chunk_size: number
```

CAM exports can be generated on-demand and returned directly to the client without persistent storage.

## Data Models

### Core Domain Models

```python
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict
from enum import Enum

class ApplicationStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    ANALYSIS_COMPLETE = "analysis_complete"
    APPROVED = "approved"
    APPROVED_WITH_CONDITIONS = "approved_with_conditions"
    REJECTED = "rejected"

class CreditRecommendation(Enum):
    APPROVE = "approve"
    APPROVE_WITH_CONDITIONS = "approve_with_conditions"
    REJECT = "reject"

@dataclass
class Application:
    id: str
    company_name: str
    loan_amount: float
    loan_purpose: str
    applicant_email: str
    status: ApplicationStatus
    created_at: datetime
    updated_at: datetime
    credit_score: Optional[float] = None
    recommendation: Optional[CreditRecommendation] = None

@dataclass
class Document:
    id: str
    application_id: str
    filename: str
    file_type: str
    content_base64: str  # Base64-encoded document content
    file_size: int
    upload_date: datetime
    processing_status: str
    extracted_data: Optional[Dict] = None
    chunk_count: Optional[int] = None  # For large files
    chunk_ids: Optional[List[str]] = None  # For large files

@dataclass
class FinancialMetrics:
    revenue: List[float]  # Multi-year historical data
    profit: List[float]
    debt: List[float]
    cash_flow: List[float]
    current_assets: float
    current_liabilities: float
    total_assets: float
    total_equity: float
    total_debt: float
    
    # Calculated ratios
    current_ratio: float
    debt_to_equity: float
    net_profit_margin: float
    roe: float
    asset_turnover: float
    
    # Growth rates
    revenue_growth: List[float]
    profit_growth: List[float]

@dataclass
class Forecast:
    metric_name: str
    historical_values: List[float]
    projected_values: List[float]  # 3-year projections
    confidence_level: float
    assumptions: List[str]

@dataclass
class RiskFactorScore:
    factor_name: str
    score: float  # 0-100
    weight: float
    explanation: str
    key_findings: List[str]

@dataclass
class RiskAssessment:
    overall_score: float  # 0-100
    recommendation: CreditRecommendation
    financial_health: RiskFactorScore
    cash_flow: RiskFactorScore
    industry: RiskFactorScore
    promoter: RiskFactorScore
    external_intelligence: RiskFactorScore
    summary: str

@dataclass
class ResearchFindings:
    web_research: str
    promoter_analysis: str
    industry_analysis: str
    sources: List[str]
    red_flags: List[str]
    positive_indicators: List[str]

@dataclass
class AnalysisResults:
    application_id: str
    financial_metrics: FinancialMetrics
    forecasts: List[Forecast]
    risk_assessment: RiskAssessment
    research_findings: ResearchFindings
    generated_at: datetime

@dataclass
class CAM:
    application_id: str
    content: str  # Markdown or HTML formatted content
    version: int
    generated_at: datetime
    sections: Dict[str, str]  # Section name -> content mapping

@dataclass
class MonitoringAlert:
    id: str
    application_id: str
    alert_type: str
    severity: str  # "low", "medium", "high", "critical"
    message: str
    details: Dict
    created_at: datetime
    acknowledged: bool
```


## Correctness Properties

A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.

### Property 1: Document Upload Round-Trip Integrity

*For any* valid document (PDF, DOCX, Excel, CSV, or image format) uploaded to an application, the document should be stored in Firestore as base64-encoded content and retrievable with the same content and associated with the correct application identifier.

**Validates: Requirements 1.1, 1.4, 1.5**

### Property 2: Invalid Document Rejection

*For any* file with an invalid format or exceeding size limits, the upload should be rejected with a descriptive error message, and no storage operation should occur.

**Validates: Requirements 1.2, 1.3**

### Property 3: Financial Data Extraction Completeness

*For any* document containing financial information, the Document Intelligence Agent should extract all present Financial_Metrics (revenue, profit, debt, cash flow, ratios) and structure them in the standardized format.

**Validates: Requirements 2.1, 2.2**

### Property 4: Extraction Traceability

*For any* extracted financial value, the system should maintain a reference to the source document ID and page number, enabling traceability back to the original source.

**Validates: Requirements 2.5**

### Property 5: Extracted Data Persistence

*For any* completed extraction, the structured data should be persisted to Firestore with the correct document reference, and retrieving the data should return the same structured values.

**Validates: Requirements 2.4**

### Property 6: Orchestrator Agent Coordination

*For any* application requiring analysis, the Orchestrator should delegate tasks to all required specialized agents (Document Intelligence, Financial Analysis, Web Research, Promoter Intelligence, Industry Intelligence, Forecasting, Risk Scoring, CAM Generator) and aggregate their results into a unified analysis.

**Validates: Requirements 3.1, 3.5**

### Property 7: Financial Ratio Calculation Correctness

*For any* set of financial data with non-zero denominators, the calculated ratios (current ratio, debt-to-equity, net profit margin, ROE, asset turnover) should match the standard financial formulas.

**Validates: Requirements 4.1**

### Property 8: Growth Rate Calculation Correctness

*For any* multi-year time series of financial data, the calculated year-over-year growth rates should correctly represent the percentage change between consecutive periods.

**Validates: Requirements 4.2**

### Property 9: Calculated Metrics Metadata Completeness

*For any* calculated financial metric or ratio, the system should provide a definition and industry benchmark comparison data.

**Validates: Requirements 4.5**

### Property 10: Forecast Completeness

*For any* application with sufficient historical data, the Forecasting Agent should generate 3-year projections for all required metrics (revenue, profit, cash flow, debt) with confidence levels and documented assumptions.

**Validates: Requirements 5.1, 5.3, 5.5**

### Property 11: Forecast Methodology Validation

*For any* generated forecast, the system should incorporate historical trends, industry growth rates, and economic indicators as inputs to the forecasting model.

**Validates: Requirements 5.2**

### Property 12: Risk Score Calculation and Weighting

*For any* complete analysis with all risk factors scored, the overall credit score should be calculated as a weighted sum using the specified weights (financial health 35%, cash flow 25%, industry 15%, promoter 15%, external intelligence 10%) and fall within the range 0-100.

**Validates: Requirements 6.1, 6.2**

### Property 13: Credit Recommendation Mapping

*For any* calculated credit score, the recommendation should be "Reject" if score < 40, "Approve with conditions" if 40 ≤ score < 70, and "Approve" if score ≥ 70.

**Validates: Requirements 6.4, 6.5, 6.6**

### Property 14: Risk Score Explainability

*For any* generated credit score, the system should provide detailed explanations for each of the five risk factor contributions and document the key factors influencing the recommendation.

**Validates: Requirements 6.3, 6.7**

### Property 15: CAM Document Structure Completeness

*For any* generated CAM, the document should include all required sections (executive summary, company overview, financial analysis, risk assessment, credit recommendation) with generation timestamp and version tracking.

**Validates: Requirements 7.1, 7.2, 7.5**

### Property 16: CAM Export Format Validity

*For any* CAM export request specifying PDF or Word format, the system should generate a valid file in the requested format that can be opened by standard document readers.

**Validates: Requirements 7.4**

### Property 17: Authentication Enforcement

*For any* API request without valid Firebase Authentication credentials, the system should reject the request and return an authentication error.

**Validates: Requirements 8.1, 8.3**

### Property 18: Session Creation and Permissions

*For any* successful user login, the system should create a session with role-based permissions that correctly enforce access rules for viewing, editing, and approving applications.

**Validates: Requirements 8.2, 8.5**

### Property 19: Session Expiration Enforcement

*For any* expired user session, subsequent API requests should be rejected and require re-authentication.

**Validates: Requirements 8.4**

### Property 20: Application Status State Machine

*For any* application, status transitions should follow the valid state machine: "Pending Document Upload" → "Processing" (on document upload) → "Analysis Complete" (on analysis completion) → {"Approved", "Approved with Conditions", "Rejected"} (on credit decision).

**Validates: Requirements 9.1, 9.2, 9.3, 9.4**

### Property 21: Audit Trail Completeness

*For any* status transition or user action, the system should create an audit log entry with timestamp, user identifier, and action details.

**Validates: Requirements 9.5, 17.1**

### Property 22: Monitoring Activation on Approval

*For any* application that receives an "Approved" or "Approved with Conditions" status, the system should initiate continuous monitoring for that company.

**Validates: Requirements 10.1**

### Property 23: Alert Generation and Notification

*For any* detected material adverse change during monitoring, the system should generate a Monitoring_Alert and send notifications to relevant users via dashboard and email.

**Validates: Requirements 10.3, 10.4**

### Property 24: Monitoring Activity Logging

*For any* monitoring check performed, the system should log the check timestamp and findings.

**Validates: Requirements 10.5**

### Property 25: Document Access Control

*For any* document stored in Firestore, unauthorized users should be unable to access the document, while authorized users with proper permissions should be able to retrieve it.

**Validates: Requirements 12.3**

### Property 26: API Token Validation

*For any* API request with an invalid or missing authentication token, the system should reject the request with an appropriate HTTP 401 or 403 status code.

**Validates: Requirements 12.4**

### Property 27: API Endpoint Completeness

*For all* core operations (application management, document operations, analysis operations, CAM operations, search operations, monitoring operations, authentication), the system should expose corresponding RESTful API endpoints.

**Validates: Requirements 14.1**

### Property 28: API Response Format Consistency

*For any* API request (successful or error), the system should return a response in valid JSON format with an appropriate HTTP status code and, in case of errors, include descriptive error messages with error codes.

**Validates: Requirements 14.2, 14.3**

### Property 29: API Rate Limiting

*For any* API endpoint, when the number of requests from a single client exceeds the rate limit threshold within the time window, subsequent requests should be throttled with HTTP 429 status code.

**Validates: Requirements 14.5**

### Property 30: Agent Failure Recovery

*For any* agent failure during processing, the Orchestrator should log the error with detailed information and either attempt recovery or gracefully degrade functionality without crashing the entire workflow.

**Validates: Requirements 15.1, 15.5**

### Property 31: External API Retry Logic

*For any* failed external API call, the system should implement retry logic with exponential backoff, attempting the request multiple times before reporting failure.

**Validates: Requirements 15.2**

### Property 32: Database Transaction Rollback

*For any* failed database operation within a transaction, the system should rollback all changes made within that transaction and return an appropriate error message.

**Validates: Requirements 15.3**

### Property 33: Document Processing Error Isolation

*For any* application with multiple documents where one document is corrupted or fails processing, the system should isolate the error to that document and continue processing the remaining documents.

**Validates: Requirements 15.4**

### Property 34: Vector Embedding Indexing

*For any* processed document, the system should generate vector embeddings for the document content and store them in the FAISS index, enabling semantic search.

**Validates: Requirements 16.1**

### Property 35: Semantic Search Functionality

*For any* search query submitted for an application, the system should perform semantic search across all indexed documents and return results ranked by relevance with highlighted matching sections.

**Validates: Requirements 16.2, 16.3**

### Property 36: AI Decision Logging

*For any* decision made by an AI agent (extraction, analysis, scoring, recommendation), the system should log the reasoning, data sources used, and decision outcome.

**Validates: Requirements 17.2**

### Property 37: Audit Record Immutability

*For any* credit decision audit record, once created, the record should be immutable and any attempt to modify it should be rejected.

**Validates: Requirements 17.3**

### Property 38: Audit Query and Export

*For any* audit log query with filtering criteria, the system should return matching audit records and support export functionality.

**Validates: Requirements 17.4**

### Property 39: Task Queue Management

*For any* batch operation request, the system should queue tasks and process them in order, maintaining proper task state (queued, processing, completed, failed).

**Validates: Requirements 18.3**

### Property 40: Capacity Management and Notification

*For any* situation where processing capacity is reached, the system should queue additional requests and notify users of expected wait times.

**Validates: Requirements 18.4**

### Property 41: Concurrent Operation Data Consistency

*For any* set of concurrent operations on the same application, the system should maintain data consistency and isolation, ensuring no data corruption or race conditions occur.

**Validates: Requirements 18.5**

## Error Handling

### Error Categories

**1. Input Validation Errors**
- Invalid file formats or sizes
- Missing required fields
- Malformed data structures
- Response: HTTP 400 Bad Request with descriptive error message

**2. Authentication/Authorization Errors**
- Missing or invalid authentication tokens
- Insufficient permissions for requested operation
- Expired sessions
- Response: HTTP 401 Unauthorized or 403 Forbidden with error details

**3. Resource Not Found Errors**
- Application ID not found
- Document ID not found
- User not found
- Response: HTTP 404 Not Found with resource identifier

**4. Processing Errors**
- Document extraction failures
- AI agent failures
- External API failures
- Response: HTTP 500 Internal Server Error with error ID for tracking

**5. Rate Limiting Errors**
- Too many requests from single client
- Response: HTTP 429 Too Many Requests with retry-after header

**6. Capacity Errors**
- System at maximum capacity
- Response: HTTP 503 Service Unavailable with estimated wait time

### Error Handling Strategies

**Retry with Exponential Backoff**
```python
async def retry_with_backoff(
    func: Callable,
    max_retries: int = 3,
    base_delay: float = 1.0
) -> Any:
    """
    Retry a function with exponential backoff
    """
    for attempt in range(max_retries):
        try:
            return await func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            delay = base_delay * (2 ** attempt)
            await asyncio.sleep(delay)
```

**Circuit Breaker Pattern**
```python
class CircuitBreaker:
    """
    Prevent cascading failures by stopping requests to failing services
    """
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open
    
    async def call(self, func: Callable) -> Any:
        if self.state == "open":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "half-open"
            else:
                raise Exception("Circuit breaker is open")
        
        try:
            result = await func()
            if self.state == "half-open":
                self.state = "closed"
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.failure_threshold:
                self.state = "open"
            raise
```

**Graceful Degradation**
- If Web Research Agent fails, continue with available data and flag missing research
- If Forecasting Agent fails, provide analysis without forecasts and notify user
- If CAM generation fails, provide raw analysis results for manual report creation

**Error Logging and Monitoring**
```python
class ErrorLogger:
    """
    Centralized error logging with structured data
    """
    async def log_error(
        self,
        error: Exception,
        context: Dict,
        severity: str = "error"
    ):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'stack_trace': traceback.format_exc(),
            'context': context,
            'severity': severity,
            'error_id': str(uuid.uuid4())
        }
        
        # Log to Firestore for persistence
        await self.db.collection('error_logs').add(log_entry)
        
        # Log to stdout for real-time monitoring
        logger.error(json.dumps(log_entry))
        
        return log_entry['error_id']
```

## Testing Strategy

### Dual Testing Approach

The Intelli-Credit platform requires both unit testing and property-based testing for comprehensive coverage:

**Unit Tests** focus on:
- Specific examples of document processing (e.g., parsing a sample financial statement)
- Integration points between components (e.g., Orchestrator → Agent communication)
- Edge cases (e.g., zero denominators in ratio calculations, empty documents)
- Error conditions (e.g., corrupted files, API failures)
- UI component rendering and interactions

**Property-Based Tests** focus on:
- Universal properties that hold for all inputs (e.g., risk score always in 0-100 range)
- Round-trip properties (e.g., upload → store → retrieve preserves content)
- Invariants (e.g., audit logs are immutable after creation)
- State machine transitions (e.g., application status follows valid paths)
- Calculation correctness (e.g., financial ratios match formulas for any input)

### Property-Based Testing Configuration

**Framework**: Use `hypothesis` for Python backend testing

**Configuration**:
- Minimum 100 iterations per property test (due to randomization)
- Each property test must reference its design document property
- Tag format: `# Feature: intelli-credit-platform, Property {number}: {property_text}`

**Example Property Test**:
```python
from hypothesis import given, strategies as st
import pytest

# Feature: intelli-credit-platform, Property 13: Credit Recommendation Mapping
@given(credit_score=st.floats(min_value=0, max_value=100))
def test_credit_recommendation_mapping(credit_score):
    """
    For any calculated credit score, the recommendation should be:
    - "Reject" if score < 40
    - "Approve with conditions" if 40 <= score < 70
    - "Approve" if score >= 70
    """
    recommendation = get_recommendation_from_score(credit_score)
    
    if credit_score < 40:
        assert recommendation == "reject"
    elif credit_score < 70:
        assert recommendation == "approve_with_conditions"
    else:
        assert recommendation == "approve"

# Feature: intelli-credit-platform, Property 12: Risk Score Calculation and Weighting
@given(
    financial_health=st.floats(min_value=0, max_value=100),
    cash_flow=st.floats(min_value=0, max_value=100),
    industry=st.floats(min_value=0, max_value=100),
    promoter=st.floats(min_value=0, max_value=100),
    external_intelligence=st.floats(min_value=0, max_value=100)
)
def test_risk_score_weighting(
    financial_health, cash_flow, industry, promoter, external_intelligence
):
    """
    For any complete analysis with all risk factors scored,
    the overall credit score should be calculated as a weighted sum
    using the specified weights and fall within the range 0-100.
    """
    risk_factors = {
        'financial_health': financial_health,
        'cash_flow': cash_flow,
        'industry': industry,
        'promoter': promoter,
        'external_intelligence': external_intelligence
    }
    
    overall_score = calculate_overall_risk_score(risk_factors)
    
    # Verify weighted calculation
    expected_score = (
        financial_health * 0.35 +
        cash_flow * 0.25 +
        industry * 0.15 +
        promoter * 0.15 +
        external_intelligence * 0.10
    )
    
    assert abs(overall_score - expected_score) < 0.01
    assert 0 <= overall_score <= 100
```

### Unit Testing Strategy

**Backend Unit Tests** (pytest):
- Test individual agent functions with mocked dependencies
- Test API endpoints with mocked database and AI services
- Test financial calculation functions with known inputs/outputs
- Test error handling paths
- Test authentication and authorization logic

**Frontend Unit Tests** (Jest + React Testing Library):
- Test component rendering with various props
- Test user interactions (clicks, form submissions)
- Test chart data formatting
- Test routing and navigation
- Test error state displays

**Integration Tests**:
- Test complete workflows (upload → extract → analyze → score → CAM)
- Test database operations with test Firestore instance
- Test file storage operations with test Firebase Storage
- Test API endpoint chains
- Test agent orchestration

### Test Coverage Goals

- Backend code coverage: ≥ 80%
- Frontend code coverage: ≥ 75%
- All correctness properties: 100% (each property must have a property-based test)
- Critical paths (authentication, credit scoring, CAM generation): 100%

### Continuous Integration

- Run all tests on every commit
- Run property-based tests with 100 iterations in CI
- Run extended property-based tests (1000+ iterations) nightly
- Monitor test execution time and optimize slow tests
- Fail builds on test failures or coverage drops

