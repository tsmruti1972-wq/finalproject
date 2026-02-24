# Financial Decision Support Copilot

Pilot-ready full stack app for senior financial analysts. It turns financial inputs and business context into executive-ready decision-support outputs using a grounded RAG pipeline.

## What is included

- `frontend/`: React + TypeScript single-page app
- `backend/`: FastAPI API with `/chat` endpoint and RAG pipeline
- `backend/data/knowledge_base/`: sample knowledge base (9 docs)
- `samples/`: sample CSV files for demo workflows

## Core workflows supported

1. Variance explanation
2. Executive narrative builder
3. Assumption and risk checker

All responses are structured with required headings:

- Key insights
- Drivers and impacts
- Assumptions made
- Risks and uncertainties
- Suggested follow up questions
- Sources used (appended with cited titles)

## Tech stack

- Frontend: React, TypeScript, Vite
- Backend: FastAPI (Python)
- Retrieval: FAISS vector index using local hashing embeddings

## Local setup

## 1) Backend setup

```bash
cd /Users/smrutitapiawala/Documents/New\ project/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2) Ingest sample knowledge base into vector store

```bash
cd /Users/smrutitapiawala/Documents/New\ project/backend
source .venv/bin/activate
PYTHONPATH=. python scripts/ingest_kb.py
```

Expected output includes generated files:

- `backend/data/vector_store/kb.faiss`
- `backend/data/vector_store/metadata.json`

## 3) Start backend API

```bash
cd /Users/smrutitapiawala/Documents/New\ project/backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

API health check: `GET http://localhost:8000/health`

## 4) Start frontend

Open a second terminal:

```bash
cd /Users/smrutitapiawala/Documents/New\ project/frontend
npm install
npm run dev
```

Frontend URL: `http://localhost:5173`

## Optional external model usage (OpenAI/Groq compatible)

The backend uses an external LLM when `LLM_API_KEY` is set (or compatible legacy variables are present); otherwise it runs a deterministic grounded fallback response generator.

```bash
export LLM_API_KEY="your_key"
export LLM_MODEL="gpt-4o-mini"
# Optional for OpenAI-compatible providers (Groq/OpenRouter/etc.)
export LLM_BASE_URL="https://api.groq.com/openai/v1"
```

## Using the app

1. Upload a CSV from `samples/` or your own file.
2. Add context/assumptions in the left panel.
3. Select task type.
4. Ask a prompt in Copilot Chat and click Submit.
5. Review structured output in the right panel.

## Input contract for `/chat`

`POST /chat`

```json
{
  "task_type": "variance_explanation",
  "user_message": "Explain key December variance",
  "context_assumptions": "Cloud credits are one-time.",
  "csv_content": [
    {"period": "2025-12", "account": "Revenue", "actual": 100, "budget": 110}
  ]
}
```

## Guardrails implemented

- Conservative finance tone
- No fabricated numbers
- No definitive claims without support
- Facts separated from assumptions
- If support is missing, response states it cannot conclude and asks clarifying questions

## Logging

Backend logs retrieved document ids and titles for each `/chat` request for debugging and traceability.

## Basic error handling

- Empty `user_message` rejected
- Empty or invalid CSV upload surfaced in UI
- Missing vector index returns API error instructing ingestion

## Free publish option

Use GitHub Pages for the frontend and a free backend host for FastAPI.

- Deployment guide: `/Users/smrutitapiawala/Documents/New project/DEPLOY_FREE.md`
