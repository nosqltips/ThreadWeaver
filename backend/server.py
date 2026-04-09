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

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not required if env vars are set directly (e.g., systemd EnvironmentFile)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from config import config
from llm import stream_response
from state import ChatStateManager
from tools import mcp_client, get_tool_definitions

VERSION = "0.3.0-beta.1"

app = FastAPI(
    title="ThreadWeaver",
    description="AI chat with branchable conversations, powered by AgentStateGraph",
    version=VERSION,
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

class CreateProjectRequest(BaseModel):
    name: str
    description: str = ""
    system_prompt: str = ""

class AddToProjectRequest(BaseModel):
    project_id: str

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


# ─── Delete / Archive ────────────────────────────────────────────

@app.delete("/api/conversations/{conv_id}")
def delete_conversation(conv_id: str):
    if state.delete_conversation(conv_id):
        return {"status": "deleted", "id": conv_id}
    raise HTTPException(404, "Conversation not found")

@app.post("/api/conversations/{conv_id}/archive")
def archive_conversation(conv_id: str):
    if state.archive_conversation(conv_id):
        return {"status": "archived", "id": conv_id}
    raise HTTPException(404, "Conversation not found")

@app.post("/api/conversations/{conv_id}/unarchive")
def unarchive_conversation(conv_id: str):
    if state.unarchive_conversation(conv_id):
        return {"status": "unarchived", "id": conv_id}
    raise HTTPException(404, "Conversation not found")

@app.get("/api/conversations/archived")
def list_archived():
    return state.list_archived()


# ─── Projects ────────────────────────────────────────────────────

@app.post("/api/projects")
def create_project(req: CreateProjectRequest):
    project = state.create_project(req.name, req.description, req.system_prompt)
    return {"id": project.id, "name": project.name}

@app.get("/api/projects")
def list_projects():
    return state.list_projects()

@app.get("/api/projects/{project_id}")
def get_project(project_id: str):
    project = state.get_project(project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    return {
        "id": project.id, "name": project.name,
        "description": project.description,
        "system_prompt": project.system_prompt,
        "tags": project.tags, "created_at": project.created_at,
        "conversations": state.get_project_conversations(project_id),
    }

@app.delete("/api/projects/{project_id}")
def delete_project(project_id: str):
    if state.delete_project(project_id):
        return {"status": "deleted", "id": project_id}
    raise HTTPException(404, "Project not found")

@app.post("/api/conversations/{conv_id}/project")
def add_to_project(conv_id: str, req: AddToProjectRequest):
    if state.add_conversation_to_project(conv_id, req.project_id):
        return {"status": "ok"}
    raise HTTPException(400, "Invalid conversation or project")


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

class ProviderUpdate(BaseModel):
    api_key: Optional[str] = None
    model: Optional[str] = None
    base_url: Optional[str] = None
    enabled: Optional[bool] = None

class DefaultProviderUpdate(BaseModel):
    provider: str

@app.get("/api/settings")
def get_settings():
    return {
        "default_provider": config.default_provider,
        "providers": config.get_all_providers(),
    }

@app.put("/api/settings/provider/{name}")
def update_provider(name: str, req: ProviderUpdate):
    """Update a provider's config (API key, model, base URL)."""
    updates = {}
    if req.api_key is not None:
        updates["api_key"] = req.api_key
    if req.model is not None:
        updates["model"] = req.model
    if req.base_url is not None:
        updates["base_url"] = req.base_url
    if req.enabled is not None:
        updates["enabled"] = req.enabled
    config.update_provider(name, updates)
    return {"status": "updated", "provider": name}

@app.put("/api/settings/default")
def set_default_provider(req: DefaultProviderUpdate):
    config.default_provider = req.provider
    return {"status": "ok", "default_provider": req.provider}

def _sort_models(models: list[dict], default_model: str) -> list[dict]:
    """Sort models: default first, then popular families, then alphabetical."""
    # Popular model families in priority order
    priority_prefixes = [
        "llama3", "llama2", "mistral", "mixtral", "gemma", "phi",
        "codellama", "deepseek", "qwen", "vicuna", "neural-chat",
    ]

    def sort_key(m):
        name = m["name"].lower()
        # Default model always first
        if name == default_model.lower() or name.startswith(default_model.lower().split(":")[0]):
            return (0, 0, name)
        # Priority by family
        for i, prefix in enumerate(priority_prefixes):
            if name.startswith(prefix):
                return (1, i, name)
        # Everything else alphabetical
        return (2, 0, name)

    return sorted(models, key=sort_key)

@app.get("/api/models/local")
async def list_local_models():
    """List available models from Ollama or any OpenAI-compatible server (llama-server, vLLM, etc.)."""
    import httpx
    base_url = config.get_base_url("local") or "http://localhost:11434"
    default_model = config.get_model("local") or "llama3"
    ollama_url = base_url.replace("/v1", "")

    async with httpx.AsyncClient(timeout=5) as client:
        # Try Ollama native API first (/api/tags)
        try:
            resp = await client.get(f"{ollama_url}/api/tags")
            if resp.status_code == 200:
                data = resp.json()
                models = [
                    {
                        "name": m["name"],
                        "size": m.get("size", 0),
                        "modified": m.get("modified_at", ""),
                    }
                    for m in data.get("models", [])
                ]
                models = _sort_models(models, default_model)
                return {"models": models, "default": default_model, "source": ollama_url, "server_type": "ollama"}
        except Exception:
            pass

        # Fallback: OpenAI-compatible /v1/models (llama-server, vLLM, LM Studio)
        try:
            v1_url = base_url if "/v1" in base_url else f"{base_url}/v1"
            resp = await client.get(f"{v1_url}/models")
            if resp.status_code == 200:
                data = resp.json()
                models = [
                    {
                        "name": m.get("id", m.get("model", "unknown")),
                        "size": 0,
                        "modified": "",
                    }
                    for m in data.get("data", [])
                ]
                models = _sort_models(models, default_model)
                return {"models": models, "default": default_model, "source": v1_url, "server_type": "openai-compatible"}
        except Exception:
            pass

    return {"models": [], "error": "No model server found. Tried Ollama and OpenAI-compatible endpoints."}


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
        "version": VERSION,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
