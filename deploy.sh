#!/usr/bin/env bash
# One-command deployment of the SuperKart backend + frontend containers inside a GitHub Codespace
set -e                                                     # Stop at the first error

docker network create superkart-app-network 2>/dev/null || true          # Shared bridge network (ignore if it exists)
docker rm -f backend frontend 2>/dev/null || true                         # Remove old containers (re-deploy safe)

docker build -t superkart-backend ./backend_files                         # Build the Flask API image
docker build -t superkart-frontend ./frontend_files                       # Build the Streamlit image

docker run -d --name backend --network superkart-app-network -p 7860:7860 superkart-backend     # API on port 7860
docker run -d --name frontend --network superkart-app-network -p 8501:8501 \
  -e BACKEND_URL=http://backend:7860 superkart-frontend                                         # UI on port 8501

docker ps                                                                  # Show the running containers
echo "Backend : port 7860 | Frontend : port 8501 -> set both ports to Public in the PORTS tab"
