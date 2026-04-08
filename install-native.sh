#!/bin/bash
# ThreadWeaver — Native Install (no Docker)
# For PicoClaw, Jetson, Raspberry Pi, or any Linux/macOS system
#
# Usage: bash install-native.sh

set -e

INSTALL_DIR="${INSTALL_DIR:-$(pwd)}"

echo "=== ThreadWeaver Native Install ==="
echo "Install directory: $INSTALL_DIR"
echo ""

# Backend: Python venv
echo "Setting up Python backend..."
python3 -m venv "$INSTALL_DIR/venv"
"$INSTALL_DIR/venv/bin/pip" install --quiet -r "$INSTALL_DIR/backend/requirements.txt"
echo "  Python dependencies installed."

# .env
if [ ! -f "$INSTALL_DIR/backend/.env" ]; then
    cp "$INSTALL_DIR/backend/.env.example" "$INSTALL_DIR/backend/.env"
    echo "  Created backend/.env — edit with your settings."
fi

# Frontend: npm install
echo "Setting up frontend..."
cd "$INSTALL_DIR/frontend"
npm install --silent
echo "  Frontend dependencies installed."
cd "$INSTALL_DIR"

echo ""
echo "=== Installation complete ==="
echo ""
echo "To start ThreadWeaver:"
echo ""
echo "  # Terminal 1: Backend"
echo "  cd $INSTALL_DIR/backend"
echo "  ../venv/bin/python server.py"
echo ""
echo "  # Terminal 2: Frontend"
echo "  cd $INSTALL_DIR/frontend"
echo "  npx vite --host 0.0.0.0 --port 5173"
echo ""
echo "  Then open: http://$(hostname):5173"
echo ""
echo "Or create a systemd service — see README.md"
