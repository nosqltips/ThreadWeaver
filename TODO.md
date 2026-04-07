# ThreadWeaver — Feature Backlog

## Next Session
- [ ] Update README.md to reflect all current features (multimodal, 6 providers, tool calling, MCP, settings UI, accent colors, AgentStateGraph integration)
- [ ] Update AgentStateGraph README.md similarly
- [ ] Deploy ThreadWeaver as BYOK demo (static frontend + user's own API keys)
- [ ] Component refactor (split +page.svelte into ChatMessage, Sidebar, Settings, Notebook, ModelSelector)
- [ ] Blog post visibility push

## Missing vs Competitors

### High Priority
- [ ] User authentication (simple JWT or local accounts)
- [ ] RAG / embeddings — upload documents, search by semantic similarity
- [ ] Markdown rendering in chat messages (code blocks, tables, links)
- [ ] Code syntax highlighting
- [ ] Conversation export (markdown, JSON, PDF)
- [ ] Settings UI in the frontend (switch providers, set API keys)

### Medium Priority
- [ ] Voice input (Whisper API)
- [ ] Voice output (TTS)
- [ ] File upload via UI (not just paste — file picker)
- [ ] Drag-and-drop files into chat
- [ ] Conversation sharing (shareable link)
- [ ] Mobile responsive layout
- [ ] System prompt configuration per conversation
- [ ] Model selection per conversation

### Low Priority / Future
- [ ] Plugin ecosystem beyond MCP
- [ ] Ollama model management (pull, list, delete)
- [ ] Token counting / cost estimation
- [ ] Conversation templates / presets
- [ ] Collaborative real-time editing (multiple users)
- [ ] Keyboard shortcuts

## Unique Features to Polish
- [ ] Branch comparison view (side-by-side diff of two branches)
- [ ] Branch merge (combine branches back together)
- [ ] Notebook export (tagged highlights as standalone document)
- [ ] AgentStateGraph provenance viewer in UI (show the commit DAG)
- [ ] MCP server management UI (connect/disconnect in the frontend)
- [ ] Tool approval UI (human-in-the-loop before tool execution)
