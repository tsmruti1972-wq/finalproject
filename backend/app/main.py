import logging
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .generator import generate_response
from .rag import RagStore
from .schemas import ChatRequest, ChatResponse, RetrievedDoc

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("financial-copilot")

app = FastAPI(title="Financial Decision Support Copilot API", version="0.1.0")
store = RagStore()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Financial Decision Support Copilot API is running", "health": "/health", "chat": "/chat"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    if not req.user_message.strip():
        raise HTTPException(status_code=400, detail="user_message cannot be empty")

    query = "\n".join(
        [
            req.task_type,
            req.user_message,
            req.context_assumptions,
            "\n".join(str(row) for row in req.csv_content[:20]),
        ]
    )

    try:
        retrieved = store.query(query)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if not retrieved:
        response_text = (
            "Key insights\n"
            "- I cannot conclude because no supporting knowledge-base documents were retrieved.\n\n"
            "Drivers and impacts\n"
            "- Insufficient evidence from grounded sources.\n\n"
            "Assumptions made\n"
            "- None beyond user-provided context.\n\n"
            "Risks and uncertainties\n"
            "- Missing retrieved context; please ingest knowledge base and provide clarifying data.\n\n"
            "Suggested follow up questions\n"
            "- Which policy or KPI definition should be applied to this analysis?\n\n"
            "Sources used\n"
            "- No supporting sources cited"
        )
        return ChatResponse(response_text=response_text, retrieved_docs=[])

    logger.info(
        "Retrieved docs for request: %s",
        [{"id": d["id"], "title": d["title"]} for d in retrieved],
    )

    response_text = generate_response(
        task_type=req.task_type,
        user_message=req.user_message,
        context_assumptions=req.context_assumptions,
        csv_rows=req.csv_content,
        retrieved_docs=retrieved,
    )

    docs_payload = [
        RetrievedDoc(id=d["id"], title=d["title"], snippet=d["text"][:300], score=float(d["score"])) for d in retrieved
    ]

    return ChatResponse(response_text=response_text, retrieved_docs=docs_payload)
