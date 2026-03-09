# Intelli-Credit AI-Powered Corporate Credit Decisioning Platform

An AI-powered corporate credit analysis platform that automates company loan application evaluation for banks, fintech lenders, and NBFCs. The system replaces the traditional 5-10 day manual credit appraisal process with automated analysis completed in 5-10 minutes.

## Features

- **AI-Powered Document Processing**: Automatically extract financial data from PDFs, DOCX, Excel, CSV, and images
- **Multi-Agent Research System**: Gather intelligence from multiple sources (web research, promoter analysis, industry evaluation)
- **Financial Analysis & Forecasting**: Calculate financial ratios, analyze trends, and generate 3-year projections
- **Risk Scoring**: Explainable credit scores with weighted risk factors
- **Automated CAM Generation**: Generate comprehensive Credit Appraisal Memos in PDF/Word format
- **Continuous Monitoring**: Post-approval monitoring with automated alerts
- **Semantic Document Search**: Natural language search across uploaded documents

## Architecture

The platform follows a layered architecture:

```
User Interface Layer (React + Tailwind + Framer Motion)
    ↓
Application API Layer (FastAPI)
    ↓
AI Agent Layer (OpenAI + LangChain)
    ↓
Data Processing Layer (Pandas, NumPy, FAISS)
    ↓
Storage Layer (Firebase: Firestore, Storage, Authentication)
```

## Technology Stack

### Backend
- Python 3.10+
- FastAPI
- Pydantic
- OpenAI API (GPT-4)
- LangChain
- Pandas, NumPy
- FAISS (vector search)
- Firebase Admin SDK

### Frontend
- React 18+
- TypeScript
- Tailwind CSS
- Framer Motion
- React Router
- Chart.js/Recharts
- Axios

### Infrastructure
- Docker & Docker Compose
- Firebase (Firestore, Storage, Authentication)
- Cloud hosting (AWS/GCP/Azure)

## Project Structure

```
intelli-credit-platform/
├── backend/                    # Python FastAPI backend
│   ├── app/
│   │   ├── agents/            # AI agents
│   │   ├── api/               # API endpoints
│   │   ├── core/              # Core utilities
│   │   ├── models/            # Data models
│   │   ├── repositories/      # Database layer
│   │   ├── services/          # Business logic
│   │   └── main.py            # FastAPI app
│   ├── tests/                 # Backend tests
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                   # React frontend
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── contexts/          # React contexts
│   │   ├── pages/             # Page components
│   │   ├── services/          # API client
│   │   ├── utils/             # Utilities
│   │   └── App.tsx
│   ├── public/
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- Docker & Docker Compose
- Firebase project with Firestore, Storage, and Authentication enabled
- OpenAI API key

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd intelli-credit-platform
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your Firebase and OpenAI credentials
   ```

3. **Run with Docker Compose**
   ```bash
   docker-compose up --build
   ```

   The backend will be available at `http://localhost:8000`
   The frontend will be available at `http://localhost:3000`

### Manual Setup (Development)

#### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Running Tests

#### Backend Tests
```bash
cd backend
pytest
pytest --cov=app tests/  # With coverage
```

#### Frontend Tests
```bash
cd frontend
npm test
npm run test:coverage  # With coverage
```

## API Documentation

Once the backend is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Configuration

### Environment Variables

Create a `.env` file in the root directory with the following variables:

```env
# OpenAI
OPENAI_API_KEY=your_openai_api_key

# Firebase
FIREBASE_PROJECT_ID=your_project_id
FIREBASE_PRIVATE_KEY=your_private_key
FIREBASE_CLIENT_EMAIL=your_client_email
FIREBASE_STORAGE_BUCKET=your_storage_bucket

# Backend
BACKEND_PORT=8000
BACKEND_HOST=0.0.0.0
CORS_ORIGINS=http://localhost:3000

# Frontend
VITE_API_URL=http://localhost:8000
VITE_FIREBASE_API_KEY=your_firebase_api_key
VITE_FIREBASE_AUTH_DOMAIN=your_auth_domain
VITE_FIREBASE_PROJECT_ID=your_project_id
VITE_FIREBASE_STORAGE_BUCKET=your_storage_bucket
VITE_FIREBASE_MESSAGING_SENDER_ID=your_sender_id
VITE_FIREBASE_APP_ID=your_app_id
```

## License

[Your License Here]

## Contributing

[Contributing Guidelines]
