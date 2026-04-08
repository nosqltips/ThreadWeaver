# ThreadWeaver

AI chat with branchable conversations, powered by [AgentStateGraph](https://github.com/nosqltips/AgentStateGraph).

Branch from any message. Explore alternatives. Paste images. Save highlights to your notebook. Connect to Claude, GPT, Gemini, Grok, Ollama, or any local LLM.

## Quick Start (Docker)

```bash
git clone https://github.com/nosqltips/ThreadWeaver
cd ThreadWeaver
cp backend/.env.example .env
# Edit .env with your API keys (or skip for local-only)
docker compose up -d
```

Open **http://localhost:3000**

### With Local Models (Ollama)

```bash
docker compose -f docker-compose.yml -f docker-compose.ollama.yml up -d
docker compose exec ollama ollama pull llama3
```

Then select "Local (Ollama)" in the provider dropdown and pick your model.

### One-Line Install

```bash
git clone https://github.com/nosqltips/ThreadWeaver && cd ThreadWeaver && bash install.sh
```

## Quick Start (Development)

```bash
# Backend
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # add your API keys
python server.py      # starts on :8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev           # starts on :5173
```

## What Makes This Different

| Feature | Normal Chat | ThreadWeaver |
|---------|------------|-----------------|
| History | Linear scroll | Branching DAG, searchable |
| "What if" | Start a new chat | Branch from any message |
| Save a highlight | Copy-paste to Notes | Click → tagged in notebook |
| Find something | Scroll forever | Search by content or tag |
| Images | Some support | Paste/drop, all providers |
| Tool calling | None | Built-in + MCP servers |
| Audit trail | None | Every message versioned via AgentStateGraph |
| Customize | Fixed theme | 10 accent colors |

## Features

- **6 LLM providers**: Claude (Anthropic), GPT (OpenAI), Gemini (Google), Grok (xAI), Ollama, any OpenAI-compatible
- **Multimodal**: paste/drop images into chat
- **Branch from any message**: fork conversations to explore alternatives
- **Branch tree**: visual sidebar showing conversation branches
- **Notebook**: save message highlights with tags
- **Search**: full-text search across all conversations
- **Tool calling**: 4 built-in tools (read/write files, list dirs, run commands) + MCP server connections
- **Settings UI**: configure providers, API keys, models — no restart needed
- **Local model selector**: dropdown of installed Ollama models
- **Accent colors**: 10 presets, persisted across sessions
- **AgentStateGraph provenance**: every message exchange is a versioned commit

## Architecture

```
threadweaver/
├── backend/                Python FastAPI
│   ├── server.py           REST + SSE endpoints
│   ├── llm.py              6 LLM connectors (multimodal + tool calling)
│   ├── state.py            AgentStateGraph-native state manager
│   ├── tools.py            Built-in tools + MCP client
│   └── config.py           Runtime config (JSON persistence)
├── frontend/               SvelteKit
│   ├── src/routes/         Chat UI with branching + notebook
│   └── src/lib/api.ts      Backend API client
├── docker-compose.yml      Backend + frontend
├── docker-compose.ollama.yml  Optional Ollama for local models
├── install.sh              One-line installer
└── landing/                threadweaver.org landing page
```

## Supported Platforms

- **Docker** (recommended): any platform with Docker
- **PicoClaw / Jetson**: runs on ARM64 with local Ollama
- **macOS / Linux**: native Python + Node development
- **Windows**: via WSL2 + Docker

## License

MIT OR Apache-2.0

## Links

- **Website**: [threadweaver.org](https://threadweaver.org)
- **AgentStateGraph**: [agentstategraph.dev](https://agentstategraph.dev)
- **GitHub**: [github.com/nosqltips/ThreadWeaver](https://github.com/nosqltips/ThreadWeaver)
