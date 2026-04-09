# ThreadWeaver

AI chat with branchable conversations, powered by [AgentStateGraph](https://github.com/nosqltips/AgentStateGraph).

Branch from any message. Explore alternatives. Paste images. Save highlights to your notebook. Connect to Claude, GPT, Gemini, Grok, Ollama, or any local LLM. Call tools via MCP.

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
docker compose exec ollama ollama pull llama3.2:3b
docker compose exec ollama ollama pull llama3.1:8b
```

Then select "Local (Ollama)" in the provider dropdown and pick your model. The model list is sorted with your configured default first, then popular model families (Llama, Mistral, Gemma, etc.), then alphabetical.

### One-Line Install

```bash
git clone https://github.com/nosqltips/ThreadWeaver && cd ThreadWeaver && bash install.sh
```

### Native Install (PicoClaw / Jetson / Linux)

```bash
git clone https://github.com/nosqltips/ThreadWeaver
cd ThreadWeaver
bash install-native.sh
```

Configure in `backend/.env`:
```bash
LLM_PROVIDER=local
LOCAL_BASE_URL=http://localhost:11434/v1
LOCAL_MODEL=llama3.2:3b
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
| Customize | Fixed theme | Accent + background colors |
| Projects | None | Group related chats with shared context |
| Delete/Archive | Basic | Archive to hide, delete with confirm |

## Features

### Chat
- **6 LLM providers**: Claude (Anthropic), GPT (OpenAI), Gemini (Google), Grok (xAI), Ollama, any OpenAI-compatible
- **Multimodal**: paste/drop images into chat
- **Streaming responses**: real-time token display with typing indicator
- **Message timestamps**: time shown on each message
- **User/Assistant avatars**: visual distinction with colored icons and backgrounds

### Branching
- **Branch from any message**: fork conversations to explore alternatives
- **Branch tree**: visual sidebar showing conversation hierarchy
- **Branch from notebook**: create new chats from saved highlights

### Organization
- **Projects**: group related conversations (like ChatGPT projects)
- **Delete conversations**: with confirmation
- **Archive conversations**: hide from list without deleting
- **Full-text search**: across all conversations and branches

### Notebook
- **Save highlights**: click bookmark icon on any message
- **Expandable notes**: click to view full content
- **Comments**: add annotations to saved highlights
- **Branch from note**: start a new conversation from highlighted content
- **Copy to clipboard**: one-click copy of note content

### Tool Calling & MCP
- **4 built-in tools**: read_file, write_file, list_directory, run_command
- **MCP server connections**: connect any MCP-compatible tool server
- **Quick Connect presets**: filesystem, GitHub, SQLite, memory, brave-search
- **Agentic loop**: LLM calls tools → execute → feed results back → repeat
- **Tool calling with Ollama**: local models support OpenAI-format tool use
- **Tools panel**: view all available tools and their descriptions
- **MCP panel**: connect/disconnect servers, browse 100+ servers at mcp.so

### Provenance (AgentStateGraph)
- **Every message versioned**: conversation state tracked as commits
- **Provenance timeline**: visual timeline of all state changes
- **Intent categories**: Checkpoint, Explore, Refine for each action
- **Agent tracking**: who (user/assistant) did what and when
- **Branch events**: branch creation recorded in provenance

### Customization
- **10 accent color presets**: purple, indigo, blue, cyan, green, amber, red, pink, violet, teal
- **10 background color presets**: various dark themes
- **Colors persist**: saved to localStorage across sessions
- **All settings hot-reload**: no restart needed

### Model Selection
- **Provider dropdown**: switch between Claude, GPT, Gemini, Grok, Local
- **Model selector for Ollama**: dropdown of all installed models
- **Smart sorting**: configured default first, then popular families (Llama, Mistral, Gemma, Phi, etc.), then alphabetical
- **Single model display**: shows model name as label when only one available (llama-server)
- **Settings panel**: configure API keys, models, base URLs per provider

## Header Icons

| Icon | Panel | Description |
|------|-------|-------------|
| ⚙ | Settings | Provider config, API keys, model selector, accent/background colors |
| 📊 | Provenance | AgentStateGraph timeline — every action tracked |
| 📓 | Notebook | Saved highlights with expand, comment, branch, copy |
| 🔌 | MCP | Connect/disconnect MCP servers, quick connect presets |
| 🔧 | Tools | View all available tools (built-in + MCP) |

Only one panel open at a time. Click to toggle.

## Architecture

```
threadweaver/
├── backend/                Python FastAPI
│   ├── server.py           REST + SSE endpoints (conversations, messages,
│   │                       branching, projects, provenance, MCP, settings)
│   ├── llm.py              6 LLM connectors (multimodal + agentic tool loop)
│   ├── state.py            AgentStateGraph-native state manager
│   ├── tools.py            Built-in tools + MCP client
│   └── config.py           Runtime config (JSON persistence, hot-reload)
├── frontend/               SvelteKit + adapter-node
│   ├── src/routes/
│   │   ├── +layout.svelte  Theme system, CSS variables, color persistence
│   │   └── +page.svelte    Main chat UI (all panels)
│   └── src/lib/api.ts      Backend API client
├── docker-compose.yml      Backend + frontend containers
├── docker-compose.ollama.yml  Optional Ollama overlay
├── install.sh              Docker installer
├── install-native.sh       Native installer (PicoClaw/Linux)
├── threadweaver.service    Systemd service template
├── landing/                threadweaver.org landing page
├── TODO.md                 Feature backlog
└── CONTRIBUTING.md         Development guide
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/conversations | Create conversation |
| GET | /api/conversations | List (excludes archived) |
| GET | /api/conversations/:id | Get with messages |
| DELETE | /api/conversations/:id | Delete |
| POST | /api/conversations/:id/messages | Send message (SSE stream) |
| POST | /api/conversations/:id/branch | Branch from message |
| POST | /api/conversations/:id/archive | Archive |
| POST | /api/conversations/:id/unarchive | Unarchive |
| POST | /api/conversations/:id/highlights | Save to notebook |
| POST | /api/conversations/:id/project | Assign to project |
| POST | /api/conversations/:id/file | Attach file |
| GET | /api/conversations/:id/provenance | Provenance timeline |
| GET | /api/conversations/:id/tree | Branch tree |
| POST | /api/projects | Create project |
| GET | /api/projects | List projects |
| GET | /api/projects/:id | Project detail + conversations |
| DELETE | /api/projects/:id | Delete project |
| POST | /api/search | Full-text search |
| GET | /api/settings | Provider config (masked keys) |
| PUT | /api/settings/provider/:name | Update provider config |
| PUT | /api/settings/default | Set default provider |
| GET | /api/models/local | List local models (sorted) |
| GET | /api/tools | List all available tools |
| POST | /api/mcp/connect | Connect MCP server |
| DELETE | /api/mcp/:name | Disconnect MCP server |
| GET | /api/mcp/servers | List connected servers |
| GET | /api/health | Health check |

## Supported Platforms

- **Docker** (recommended): any platform with Docker
- **PicoClaw / Jetson**: ARM64 with Ollama, native install
- **macOS / Linux**: native Python + Node development
- **Windows**: via WSL2 + Docker

## License

MIT OR Apache-2.0

## Links

- **Website**: [threadweaver.org](https://threadweaver.org)
- **AgentStateGraph**: [agentstategraph.dev](https://agentstategraph.dev)
- **GitHub**: [github.com/nosqltips/ThreadWeaver](https://github.com/nosqltips/ThreadWeaver)
