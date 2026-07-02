from pydantic import BaseModel


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer: str
    plan: str
    route: str
    sources: list[str]
    tool_used: str | None = None
    tool_output: str | None = None


class IngestResponse(BaseModel):
    chunks_indexed: int
    directory: str


class HistoryItem(BaseModel):
    id: str
    user_message: str
    agent_response: str
    plan: str | None = None


class HealthResponse(BaseModel):
    status: str
