# ThreadWeaver

LLM-agnostic chat application with StateGraph-native branching conversations, notebook highlights, and searchable history.

**This is the demo/dogfood project for [StateGraph](https://github.com/nosqltips/StateGraph).**

## What Makes This Different

| Feature | Normal Chat | ThreadWeaver |
|---------|------------|-----------------|
| History | Linear scroll | Branching DAG, searchable |
| "What if" | Start a new chat | Branch from any message, compare |
| Save a highlight | Copy-paste to Notes | Select → tag → it's in the graph |
| Find something | Scroll forever | Query by topic, date, content |
| Undo a direction | Can't | Checkout a previous branch point |

## Architecture

```
threadweaver/
├── backend/          Python FastAPI + StateGraph
│   ├── server.py     API server
│   ├── llm.py        LLM connectors (Anthropic, OpenAI-compatible, local)
│   └── state.py      StateGraph integration
├── frontend/         SvelteKit chat UI
│   ├── routes/       Pages
│   └── lib/          Components (chat, branch viewer, notebook)
└── config.yaml       LLM provider + StateGraph settings
```

## Supported LLM Providers

- **Anthropic** (Claude) — native API
- **OpenAI** — GPT-4, GPT-3.5, etc.
- **Ollama** — local models (Llama, Mistral, etc.)
- **LM Studio** — local models with OpenAI-compatible API
- **Any OpenAI-compatible endpoint** — vLLM, llama.cpp server, etc.

## Quick Start

```bash
# Backend
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # add your API keys
python server.py

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

## License

MIT OR Apache-2.0
