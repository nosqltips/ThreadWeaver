#!/bin/bash
# ThreadWeaver — Quick Install
# https://github.com/nosqltips/ThreadWeaver

set -e

echo "=== ThreadWeaver Install ==="
echo ""

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    cp backend/.env.example .env
    echo "Created .env from template."
    echo ""
    echo "  Edit .env with your API keys:"
    echo "    nano .env"
    echo ""
    echo "  Or set just one provider, e.g.:"
    echo "    echo 'ANTHROPIC_API_KEY=sk-ant-...' >> .env"
    echo ""
else
    echo ".env already exists — keeping your settings."
fi

echo ""
echo "Starting ThreadWeaver..."
echo ""

# Check if Ollama should be included
if command -v ollama &> /dev/null || [ "${WITH_OLLAMA:-}" = "1" ]; then
    echo "Ollama detected — including local model support."
    docker compose -f docker-compose.yml -f docker-compose.ollama.yml up -d --build
else
    docker compose up -d --build
fi

echo ""
echo "=== ThreadWeaver is running! ==="
echo ""
echo "  Frontend: http://localhost:3000"
echo "  Backend:  http://localhost:8000"
echo "  Health:   http://localhost:8000/api/health"
echo ""
echo "  To stop:  docker compose down"
echo "  Logs:     docker compose logs -f"
echo ""

# If Ollama was started, remind to pull a model
if docker compose ps ollama &> /dev/null 2>&1; then
    echo "  Pull a local model:"
    echo "    docker compose exec ollama ollama pull llama3"
    echo ""
fi
