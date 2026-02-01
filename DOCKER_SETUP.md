# Docker Development Setup

This project is configured to run in Docker Compose with hot reloading for development.

## Platform Support

- ✅ **macOS** - Use Make commands or docker-compose directly
- ✅ **Linux** - Use Make commands or docker-compose directly  
- ✅ **Windows** - See [DOCKER_WINDOWS.md](DOCKER_WINDOWS.md) for detailed Windows setup

## Services

- **API** (port 8000) - Main FastAPI app (`app/main.py`)
- **Legacy Backend** (port 8100) - Legacy FastAPI app (`backend/main.py`) 
- **Frontend** (port 5173) - Vite React app

## Quick Start

### macOS / Linux

```bash
# Build images
make docker-build

# Start all services
make docker-up

# Start in background
make docker-up-d

# View logs
make docker-logs

# Stop services
make docker-down
```

### Windows

See [DOCKER_WINDOWS.md](DOCKER_WINDOWS.md) for detailed instructions.

**Quick start:**
```powershell
# PowerShell
.\docker.ps1 fix-frontend  # Fix node_modules issue
.\docker.ps1 build
.\docker.ps1 up

# Or using batch file
docker.bat build
docker.bat up

# Or direct docker-compose
docker-compose build
docker-compose up
```

## Known Issues & Fixes

### Frontend Tailwind/PostCSS Error

If you see this error in the browser:
```
[postcss] Cannot read properties of undefined (reading 'blocklist')
```

**Fix:** The host's `frontend/node_modules` has corrupted dependencies. Delete it and restart:

```bash
# Stop Docker
make docker-down

# Delete host node_modules (you may need sudo)
sudo rm -rf frontend/node_modules

# Restart Docker
make docker-up
```

Docker will use its own clean `node_modules` via a named volume.

### Legacy Backend Database Error

The legacy backend has a pre-existing code issue with database foreign keys:
```
Foreign key associated with column 'microquestexercise.exercise_id' could not find table 'exercise'
```

This is a codebase bug in `backend/models_microquest.py`, not a Docker issue. The API (port 8000) works fine.

## Hot Reloading

- **Backend**: Uvicorn watches for Python file changes
- **Frontend**: Vite HMR watches for TypeScript/React changes
- **Config files**: Mounted so changes apply immediately

## Accessing Services

- Frontend: http://localhost:5173
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Legacy Backend: http://localhost:8100

## Troubleshooting

### Port already in use

If port 5173 is already in use, stop any local Node processes:
```bash
lsof -ti:5173 | xargs kill
```

### Container won't start

Check logs:
```bash
make docker-logs-frontend
make docker-logs-api
make docker-logs-legacy
```

### Changes not reflecting

Restart specific service:
```bash
docker-compose restart frontend
```

Or restart all:
```bash
make docker-restart
```

## Development Tips

1. Edit files normally on your host machine - changes will hot-reload
2. Don't run `npm install` or `pip install` on the host - use containers
3. Shell into containers if needed:
   ```bash
   make docker-shell-frontend
   make docker-shell-api
   ```

## Cleaning Up

```bash
# Remove containers, networks, volumes
make docker-clean
```
