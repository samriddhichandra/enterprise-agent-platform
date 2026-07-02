"""
FastAPI entrypoint. Exposes the agent platform over REST:

    POST /chat      -> run a question through the Planner/Research agent graph
    POST /ingest     -> index documents from the docs directory into Chroma
    GET  /history    -> list past conversations from PostgreSQL
    GET  /health     -> liveness check

Run with:
    uvicorn backend.main:app --reload
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.schemas import ChatRequest, ChatResponse, IngestResponse, HistoryItem, HealthResponse
from backend.agents.graph import run_agent
from backend.rag.pipeline import rag_pipeline
from backend.database.session import init_db, get_session
from backend.database.models import Conversation


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="Enterprise Agent Platform", lifespan=lifespan)


@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="ok")


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, session: AsyncSession = Depends(get_session)):
    result = run_agent(request.question)

    # Persist the exchange so /history can show it later
    record = Conversation(
        user_message=request.question,
        agent_response=result["answer"],
        plan=result["plan"],
    )
    session.add(record)
    await session.commit()

    sources = sorted({chunk["source"] for chunk in result["retrieved_chunks"]})
    return ChatResponse(
        answer=result["answer"],
        plan=result["plan"],
        route=result["route"],
        sources=sources,
        tool_used=result["tool_used"] or None,
        tool_output=result["tool_output"] or None,
    )


@app.post("/ingest", response_model=IngestResponse)
async def ingest():
    count = rag_pipeline.ingest_directory()
    return IngestResponse(chunks_indexed=count, directory=rag_pipeline.vectorstore._persist_directory)


@app.get("/history", response_model=list[HistoryItem])
async def history(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Conversation).order_by(Conversation.created_at.desc()).limit(20))
    rows = result.scalars().all()
    return [
        HistoryItem(id=r.id, user_message=r.user_message, agent_response=r.agent_response, plan=r.plan)
        for r in rows
    ]
