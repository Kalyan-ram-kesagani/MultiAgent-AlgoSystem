# Trading Platform

A professional AI-ready automated trading platform.

## Architecture

```
Frontend (React + Vite + TypeScript + Tailwind)
        ↓
    REST API
        ↓
FastAPI Backend (Python)
        ↓
    PostgreSQL
```

## Quick Start

### Prerequisites
- Node.js 18+
- Python 3.11+
- PostgreSQL 16+ (or Docker)

### Database
```bash
docker compose up db -d
```

### Backend
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Full Stack (Docker)
```bash
docker compose up --build
```

## Project Structure

```
├── frontend/          React + Vite + TypeScript
├── backend/           FastAPI + PostgreSQL
├── docker-compose.yml
├── .env.example
└── README.md
```

## Future Roadmap

1. ✅ Website + UI
2. MT5 Integration
3. Live Trading Data
4. Trading Analytics
5. AI Trade Analysis
6. AI Trading Journal
7. AI Strategy Suggestions
8. Backtesting & Validation
9. Controlled Strategy Updates
