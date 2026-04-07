"""
Tool execution engine for ThreadWeaver.

Supports:
1. Built-in tools (file I/O, web fetch)
2. MCP server connections (any MCP-compatible tool server)

The LLM decides when to call tools. Tool results are fed back
into the conversation for the LLM to interpret.
"""

import json
import os
import subprocess
from pathlib import Path
from typing import Any, Optional


# ─── Built-in tools ──────────────────────────────────────────────

BUILTIN_TOOLS = [
    {
        "name": "read_file",
        "description": "Read the contents of a file at the given path. Use for reviewing code, configs, logs, or any text file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Absolute or relative file path"},
                "max_lines": {"type": "integer", "description": "Maximum lines to read (default: 500)", "default": 500},
            },
            "required": ["path"],
        },
    },
    {
        "name": "write_file",
        "description": "Write content to a file. Creates the file if it doesn't exist, overwrites if it does.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to write to"},
                "content": {"type": "string", "description": "Content to write"},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "list_directory",
        "description": "List files and directories at the given path.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Directory path (default: current directory)", "default": "."},
            },
        },
    },
    {
        "name": "run_command",
        "description": "Run a shell command and return its output. Use for builds, tests, git operations, etc.",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Shell command to execute"},
                "timeout": {"type": "integer", "description": "Timeout in seconds (default: 30)", "default": 30},
            },
            "required": ["command"],
        },
    },
]


def execute_builtin_tool(name: str, args: dict) -> dict:
    """Execute a built-in tool and return the result."""
    try:
        if name == "read_file":
            return _read_file(args["path"], args.get("max_lines", 500))
        elif name == "write_file":
            return _write_file(args["path"], args["content"])
        elif name == "list_directory":
            return _list_directory(args.get("path", "."))
        elif name == "run_command":
            return _run_command(args["command"], args.get("timeout", 30))
        else:
            return {"error": f"Unknown tool: {name}"}
    except Exception as e:
        return {"error": str(e)}


def _read_file(path: str, max_lines: int = 500) -> dict:
    p = Path(path).expanduser().resolve()
    if not p.exists():
        return {"error": f"File not found: {path}"}
    if not p.is_file():
        return {"error": f"Not a file: {path}"}

    try:
        content = p.read_text()
        lines = content.split("\n")
        truncated = len(lines) > max_lines
        if truncated:
            lines = lines[:max_lines]

        return {
            "content": "\n".join(lines),
            "path": str(p),
            "lines": len(lines),
            "truncated": truncated,
            "size_bytes": p.stat().st_size,
        }
    except UnicodeDecodeError:
        return {"error": f"Binary file, cannot read as text: {path}"}


def _write_file(path: str, content: str) -> dict:
    p = Path(path).expanduser().resolve()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    return {
        "path": str(p),
        "bytes_written": len(content.encode()),
        "status": "ok",
    }


def _list_directory(path: str) -> dict:
    p = Path(path).expanduser().resolve()
    if not p.exists():
        return {"error": f"Directory not found: {path}"}
    if not p.is_dir():
        return {"error": f"Not a directory: {path}"}

    entries = []
    for item in sorted(p.iterdir()):
        entries.append({
            "name": item.name,
            "type": "dir" if item.is_dir() else "file",
            "size": item.stat().st_size if item.is_file() else None,
        })
    return {"path": str(p), "entries": entries[:100]}  # limit to 100


def _run_command(command: str, timeout: int = 30) -> dict:
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=timeout
        )
        return {
            "stdout": result.stdout[:10000],  # limit output
            "stderr": result.stderr[:5000],
            "exit_code": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"error": f"Command timed out after {timeout}s"}


# ─── MCP Client ──────────────────────────────────────────────────

class MCPClient:
    """Simple MCP client that connects to MCP servers via stdio."""

    def __init__(self):
        self.servers: dict[str, dict] = {}  # name -> {process, tools}
        self._request_id = 0

    def _next_id(self) -> int:
        self._request_id += 1
        return self._request_id

    async def connect(self, name: str, command: str, args: list[str] = None) -> list[dict]:
        """Connect to an MCP server and discover its tools."""
        import asyncio

        full_cmd = [command] + (args or [])
        proc = await asyncio.create_subprocess_exec(
            *full_cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        # Initialize
        init_req = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "threadweaver", "version": "0.1.0"},
            },
        }

        proc.stdin.write((json.dumps(init_req) + "\n").encode())
        await proc.stdin.drain()

        response_line = await proc.stdout.readline()
        init_response = json.loads(response_line)

        # Send initialized notification
        initialized = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
        }
        proc.stdin.write((json.dumps(initialized) + "\n").encode())
        await proc.stdin.drain()

        # List tools
        list_req = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "tools/list",
            "params": {},
        }
        proc.stdin.write((json.dumps(list_req) + "\n").encode())
        await proc.stdin.drain()

        tools_line = await proc.stdout.readline()
        tools_response = json.loads(tools_line)

        tools = tools_response.get("result", {}).get("tools", [])

        self.servers[name] = {
            "process": proc,
            "tools": tools,
            "command": command,
        }

        return tools

    async def call_tool(self, server_name: str, tool_name: str, arguments: dict) -> Any:
        """Call a tool on a connected MCP server."""
        server = self.servers.get(server_name)
        if not server:
            return {"error": f"Server '{server_name}' not connected"}

        proc = server["process"]
        req = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments,
            },
        }

        proc.stdin.write((json.dumps(req) + "\n").encode())
        await proc.stdin.drain()

        response_line = await proc.stdout.readline()
        response = json.loads(response_line)

        result = response.get("result", {})
        content = result.get("content", [])

        # Extract text from content blocks
        text_parts = []
        for block in content:
            if block.get("type") == "text":
                text_parts.append(block["text"])

        return "\n".join(text_parts) if text_parts else json.dumps(result)

    def get_all_tools(self) -> list[dict]:
        """Get all tools from all connected servers + built-in tools."""
        tools = list(BUILTIN_TOOLS)

        for server_name, server in self.servers.items():
            for tool in server["tools"]:
                # Prefix with server name to avoid collisions
                tools.append({
                    "name": f"{server_name}__{tool['name']}",
                    "description": f"[{server_name}] {tool.get('description', '')}",
                    "input_schema": tool.get("inputSchema", {}),
                    "_server": server_name,
                    "_tool_name": tool["name"],
                })

        return tools

    async def disconnect(self, name: str):
        """Disconnect from an MCP server."""
        server = self.servers.pop(name, None)
        if server and server["process"]:
            server["process"].terminate()
            await server["process"].wait()


# Global MCP client
mcp_client = MCPClient()


def get_tool_definitions() -> list[dict]:
    """Get all available tool definitions (built-in + MCP) for the LLM."""
    tools = mcp_client.get_all_tools()

    # Format for Anthropic tool_use
    formatted = []
    for tool in tools:
        formatted.append({
            "name": tool["name"],
            "description": tool["description"],
            "input_schema": tool.get("input_schema", tool.get("inputSchema", {"type": "object"})),
        })
    return formatted


async def execute_tool(name: str, args: dict) -> str:
    """Execute a tool (built-in or MCP) and return the result as a string."""
    # Check if it's an MCP tool (prefixed with server_name__)
    if "__" in name:
        server_name, tool_name = name.split("__", 1)
        result = await mcp_client.call_tool(server_name, tool_name, args)
        return result if isinstance(result, str) else json.dumps(result, indent=2)

    # Built-in tool
    result = execute_builtin_tool(name, args)
    return json.dumps(result, indent=2)
