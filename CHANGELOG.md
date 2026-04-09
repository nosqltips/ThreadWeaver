# Changelog

All notable changes to ThreadWeaver are documented here.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html)

## [0.3.0-beta.1] — 2026-04-09

### Status
**Beta** — Feature complete, running on PicoClaw, needs broader testing and public deployment.

### Added
#### Chat
- Multimodal support: paste/drop images into chat (Anthropic, OpenAI, Gemini, Grok, Ollama)
- Streaming responses with typing indicator
- Message timestamps (e.g., "2:30 PM")
- User/assistant avatars with distinct visual styling
- Accent-tinted user messages for clear differentiation

#### LLM Providers (6 total)
- Anthropic (Claude)
- OpenAI (GPT)
- Google Gemini
- xAI Grok
- Ollama (local)
- Any OpenAI-compatible endpoint

#### Tool Calling & MCP
- 4 built-in tools: read_file, write_file, list_directory, run_command
- MCP server connections (stdio protocol)
- Agentic loop: LLM → tool call → execute → feed back → repeat
- Tool calling with Ollama (local models)
- Quick Connect presets: filesystem, GitHub, SQLite, memory, brave-search
- Tools panel showing all available tools with descriptions
- MCP panel with connect/disconnect, preset quick-connect

#### Branching & Projects
- Branch conversations from any message
- Visual branch tree in sidebar
- Projects (group related chats, ChatGPT-style)
- Conversation delete/archive with confirmation
- Full-text search across all conversations

#### Notebook
- Save any message to notebook with tags
- Expandable notes (click to view full content)
- Add comments to saved highlights
- Branch new conversation from saved note
- Copy note content to clipboard

#### AgentStateGraph Provenance
- Provenance viewer panel with timeline
- Every message recorded as versioned commit
- Intent categories (Checkpoint, Explore, Refine)
- Agent tracking with timestamps
- Branch events recorded in provenance

#### UI/UX
- 5 header icon panels: Settings, Provenance, Notebook, MCP, Tools
- Only one panel open at a time
- Smooth slide-in/slide-out animations
- 10 accent color presets (customizable)
- 10 background color presets (customizable)
- Colors persist to localStorage
- Micro-interactions: hover effects, transforms, glows

#### Settings
- Hot-reload configuration (no restart)
- API key management per provider (masked display)
- Model selector for all providers
- Local Ollama model dropdown with smart sorting (default first, popular families, alphabetical)
- Pre-selected default model from config
- Base URL configuration

#### Deployment
- Docker support with docker-compose
- Docker Ollama overlay (optional)
- Native install script (PicoClaw / Jetson / Linux)
- Systemd service template
- Runs on ARM64 (PicoClaw Jetson) and x86_64
- Vite dev server with /api proxy to backend
- allowedHosts: true for LAN access

### Known Limitations
- No public demo site (threadweaver.org registered but not deployed)
- No user authentication (single-user local deployment)
- No RAG/embeddings yet
- Voice input/output not supported
- Frontend is a single-file Svelte component (will split into modules later)
- Python `dotenv` optional (works with systemd EnvironmentFile)
- `+page.svelte` approaching 1000 lines — needs component extraction

### Fixed
- MCP panel no longer overlaps with Settings panel
- Tools icon now opens a panel instead of being a static badge
- Panel toggle logic: clicking any icon closes all others
- Header icons resized to consistent 20x20 SVG icons (36x36 targets)
- API URL uses relative `/api` path (works on any hostname)
- Python dotenv now optional (graceful fallback)
- Local model support now goes through agentic loop for tool calling
- llama-server single model shown as label instead of empty dropdown

## [0.1.0] — 2026-04-07

### Added
- Initial release with basic chat, branching, notebook, search
- Anthropic + OpenAI + Ollama support
- Basic MCP client
- Sidebar with conversation list
- Streaming responses

## Upcoming (0.4.0)

- Public deployment (threadweaver.org)
- Component refactor (split +page.svelte)
- Markdown rendering in messages
- Code syntax highlighting
- Conversation export (markdown, JSON)
- User authentication (optional)
- RAG / document embeddings
- Mobile responsive layout
