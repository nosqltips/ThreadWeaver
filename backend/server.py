"""
ThreadWeaver — FastAPI backend.

Provides REST + SSE endpoints for the chat UI:
- Conversations: create, list, get, branch, search
- Messages: send (with streaming response), history
- Highlights: create, list
- Settings: get/update LLM provider config
"""

import json
import os
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from llm import stream_response
from state import ChatStateManager

load_dotenv()

app = FastAPI(
    title="ThreadWeaver",
    description="LLM-agnostic chat with StateGraph-native branching",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state manager
state = ChatStateManager()


# ─── Models ───────────────────────────────────────────────────────

class CreateConversationRequest(BaseModel):
    title: str = "New Chat"

class ImageData(BaseModel):
    data: str  # base64-encoded
    media_type: str = "image/png"

class SendMessageRequest(BaseModel):
    content: str
    provider: Optional[str] = None  # override LLM provider for this message
    images: Optional[list[ImageData]] = None  # multimodal: attached images

class BranchRequest(BaseModel):
    at_message: int
    title: Optional[str] = None

class HighlightRequest(BaseModel):
    start_index: int
    end_index: int
    tag: Optional[str] = None

class SearchRequest(BaseModel):
    query: str

class SettingsUpdate(BaseModel):
    provider: Optional[str] = None
    model: Optional[str] = None


# ─── Conversation endpoints ──────────────────────────────────────

@app.post("/api/conversations")
def create_conversation(req: CreateConversationRequest):
    conv = state.create_conversation(req.title)
    return {"id": conv.id, "title": conv.title, "branch": conv.branch}


@app.get("/api/conversations")
def list_conversations():
    return state.list_conversations()


@app.get("/api/conversations/{conv_id}")
def get_conversation(conv_id: str):
    conv = state.get_conversation(conv_id)
    if not conv:
        raise HTTPException(404, "Conversation not found")
    return {
        "id": conv.id,
        "title": conv.title,
        "branch": conv.branch,
        "messages": [
            {"role": m.role, "content": m.content, "timestamp": m.timestamp}
            for m in conv.messages
        ],
        "parent_id": conv.parent_id,
        "parent_message_index": conv.parent_message_index,
        "tags": conv.tags,
    }


@app.get("/api/conversations/{conv_id}/tree")
def get_conversation_tree(conv_id: str):
    tree = state.get_conversation_tree(conv_id)
    if not tree:
        raise HTTPException(404, "Conversation not found")
    return tree


# ─── Message endpoints ───────────────────────────────────────────

@app.post("/api/conversations/{conv_id}/messages")
async def send_message(conv_id: str, req: SendMessageRequest):
    conv = state.get_conversation(conv_id)
    if not conv:
        raise HTTPException(404, "Conversation not found")

    # Add user message (with optional images)
    images = None
    if req.images:
        images = [{"data": img.data, "media_type": img.media_type} for img in req.images]
    state.add_message(conv_id, "user", req.content, images=images)

    # Build message history for the LLM
    messages = []
    for m in conv.messages:
        msg = {"role": m.role, "content": m.content}
        if hasattr(m, "images") and m.images:
            msg["images"] = m.images
        messages.append(msg)

    # Stream the response
    async def generate():
        full_response = ""
        async for chunk in stream_response(messages, provider=req.provider):
            full_response += chunk
            yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"

        # Save the complete assistant response
        state.add_message(conv_id, "assistant", full_response)
        yield f"data: {json.dumps({'type': 'done', 'content': full_response})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ─── Branch endpoints ────────────────────────────────────────────

@app.post("/api/conversations/{conv_id}/branch")
def branch_conversation(conv_id: str, req: BranchRequest):
    try:
        new_conv = state.branch_conversation(conv_id, req.at_message, req.title)
        return {
            "id": new_conv.id,
            "title": new_conv.title,
            "branch": new_conv.branch,
            "parent_id": new_conv.parent_id,
            "parent_message_index": new_conv.parent_message_index,
            "message_count": len(new_conv.messages),
        }
    except ValueError as e:
        raise HTTPException(400, str(e))


# ─── Highlight / Notebook endpoints ──────────────────────────────

@app.post("/api/conversations/{conv_id}/highlights")
def create_highlight(conv_id: str, req: HighlightRequest):
    try:
        highlight = state.create_highlight(
            conv_id, req.start_index, req.end_index, req.tag
        )
        return highlight
    except ValueError as e:
        raise HTTPException(400, str(e))


# ─── Provenance (AgentStateGraph) ─────────────────────────────────

@app.get("/api/conversations/{conv_id}/provenance")
def get_provenance(conv_id: str):
    """Get the AgentStateGraph provenance trail for a conversation."""
    return state.get_provenance(conv_id)


# ─── Search ──────────────────────────────────────────────────────

@app.post("/api/search")
def search(req: SearchRequest):
    return state.search_conversations(req.query)


# ─── Settings ────────────────────────────────────────────────────

@app.get("/api/settings")
def get_settings():
    return {
        "provider": os.getenv("LLM_PROVIDER", "anthropic"),
        "anthropic_model": os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514"),
        "openai_model": os.getenv("OPENAI_MODEL", "gpt-4"),
        "local_model": os.getenv("LOCAL_MODEL", "llama3"),
        "local_base_url": os.getenv("LOCAL_BASE_URL", "http://localhost:11434/v1"),
    }


# ─── Health ──────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "conversations": len(state.conversations),
        "stategraph": "connected" if state.sg else "not available",
        "version": "0.1.0",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
