# Contributing to ThreadWeaver

## Quick Start

```bash
# Backend
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env    # add your API keys
python server.py        # starts on :8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev             # starts on :5173
```

## Project Structure

```
threadweaver/
├── backend/
│   ├── server.py       # FastAPI routes (conversations, messages, MCP, settings)
│   ├── llm.py          # LLM connectors (Anthropic, OpenAI, Gemini, Grok, local)
│   ├── state.py        # Chat state manager (AgentStateGraph integration)
│   ├── tools.py        # Tool execution (built-in + MCP client)
│   ├── config.py       # Runtime config with JSON persistence
│   └── .env.example    # API key template
├── frontend/
│   ├── src/
│   │   ├── routes/
│   │   │   ├── +layout.svelte   # Theme, CSS variables, global styles
│   │   │   └── +page.svelte     # Main chat UI (will be split into components)
│   │   └── lib/
│   │       └── api.ts            # Backend API client
│   └── package.json
├── landing/
│   └── index.html       # threadweaver.org landing page
├── TODO.md              # Feature backlog
└── README.md
```

## Architecture

```
Browser (SvelteKit + adapter-node)
    ↓ HTTP/SSE (proxied via Vite /api → :8000)
FastAPI Backend
    ├── LLM Connectors (Anthropic, OpenAI, Gemini, Grok, Ollama)
    ├── Tool Engine (built-in + MCP servers)
    ├── State Manager (AgentStateGraph when available)
    └── Config Manager (JSON persistence)
```

## Adding a New LLM Provider

1. Add env vars to `.env.example`
2. Add provider config to `config.py` DEFAULT_CONFIG
3. Add routing in `llm.py` stream_response()
4. If OpenAI-compatible: just add config (reuses _agentic_loop_openai)
5. If custom API: add a new _stream_xxx function

## Adding a New Built-in Tool

1. Add tool definition to BUILTIN_TOOLS in `tools.py`
2. Add execution function
3. Add case to execute_builtin_tool()

## Code Style

- Python: follow PEP 8, use type hints
- Svelte: keep components under 300 lines (split when larger)
- Name things clearly — this codebase is meant to be forked

## Future Component Split

The main `+page.svelte` should be split into:
- `ChatMessage.svelte` — single message with actions
- `Sidebar.svelte` — conversation list + branch tree
- `Settings.svelte` — provider config + color picker
- `Notebook.svelte` — highlights panel
- `ModelSelector.svelte` — provider/model dropdowns

## License

MIT OR Apache-2.0
