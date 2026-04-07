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
from tools import mcp_client, get_tool_definitions

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
    providers = {
        "anthropic": {"model": os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514"), "configured": bool(os.getenv("ANTHROPIC_API_KEY"))},
        "openai": {"model": os.getenv("OPENAI_MODEL", "gpt-4"), "configured": bool(os.getenv("OPENAI_API_KEY"))},
        "gemini": {"model": os.getenv("GEMINI_MODEL", "gemini-2.0-flash"), "configured": bool(os.getenv("GEMINI_API_KEY"))},
        "grok": {"model": os.getenv("GROK_MODEL", "grok-3"), "configured": bool(os.getenv("GROK_API_KEY"))},
        "local": {"model": os.getenv("LOCAL_MODEL", "llama3"), "base_url": os.getenv("LOCAL_BASE_URL", "http://localhost:11434/v1"), "configured": True},
    }
    return {
        "default_provider": os.getenv("LLM_PROVIDER", "anthropic"),
        "providers": providers,
    }


# ─── MCP Server Management ────────────────────────────────────────

class MCPConnectRequest(BaseModel):
    name: str           # e.g., "stategraph"
    command: str        # e.g., "/path/to/agentstategraph-mcp"
    args: list[str] = []

@app.post("/api/mcp/connect")
async def connect_mcp(req: MCPConnectRequest):
    """Connect to an MCP server and discover its tools."""
    try:
        tools = await mcp_client.connect(req.name, req.command, req.args)
        return {
            "name": req.name,
            "tools": len(tools),
            "tool_names": [t["name"] for t in tools],
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to connect: {e}")

@app.delete("/api/mcp/{name}")
async def disconnect_mcp(name: str):
    await mcp_client.disconnect(name)
    return {"status": "disconnected", "name": name}

@app.get("/api/mcp/servers")
def list_mcp_servers():
    return {
        name: {
            "tools": len(server["tools"]),
            "tool_names": [t["name"] for t in server["tools"]],
        }
        for name, server in mcp_client.servers.items()
    }

@app.get("/api/tools")
def list_tools():
    """List all available tools (built-in + MCP)."""
    return get_tool_definitions()


# ─── File Upload ─────────────────────────────────────────────────

class FileUploadRequest(BaseModel):
    path: str

@app.post("/api/conversations/{conv_id}/file")
def attach_file(conv_id: str, req: FileUploadRequest):
    """Read a file and add its contents as a system message in the conversation."""
    from tools import execute_builtin_tool
    result = execute_builtin_tool("read_file", {"path": req.path})
    if "error" in result:
        raise HTTPException(400, result["error"])

    content = f"📎 **File: {req.path}**\n```\n{result['content'][:5000]}\n```"
    state.add_message(conv_id, "user", content)
    return {"status": "ok", "lines": result["lines"], "truncated": result.get("truncated", False)}


# ─── Health ──────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "conversations": len(state.conversations),
        "stategraph": "connected" if state.sg else "not available",
        "mcp_servers": len(mcp_client.servers),
        "tools_available": len(get_tool_definitions()),
        "version": "0.1.0",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
