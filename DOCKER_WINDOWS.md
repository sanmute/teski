# Running Teski with Docker on Windows

This guide helps you run the Teski project using Docker Compose on Windows.

## Prerequisites

1. **Install Docker Desktop for Windows**
   - Download from: https://www.docker.com/products/docker-desktop
   - Ensure WSL 2 backend is enabled (recommended)
   - Make sure Docker Desktop is running

2. **Install Make (Optional but Recommended)**
   - Option A: Install via Chocolatey: `choco install make`
   - Option B: Install via Scoop: `scoop install make`
   - Option C: Use Git Bash (comes with Git for Windows)
   - Option D: Use the direct `docker-compose` commands (see below)

## Setup Steps

### 1. Clone the Repository
```powershell
git clone <repository-url>
cd teski
```

### 2. Configure Line Endings (Important!)
Git on Windows may convert line endings. Fix this:

```powershell
# In PowerShell or Git Bash
git config core.autocrlf false
git rm --cached -r .
git reset --hard
```

### 3. Fix the Frontend Node Modules Issue

**IMPORTANT:** Before starting Docker, delete the corrupted `node_modules`:

```powershell
# In PowerShell (run as Administrator if needed)
Remove-Item -Recurse -Force frontend\node_modules -ErrorAction SilentlyContinue

# Or in Git Bash / Command Prompt
rm -rf frontend/node_modules
```

This is crucial because the host's node_modules may have corrupted dependencies.

## Running with Make (Recommended)

If you have Make installed:

```powershell
# Build images
make docker-build

# Start all services
make docker-up

# Or start in background
make docker-up-d

# View logs
make docker-logs

# Stop services
make docker-down
```

## Running without Make

If you don't have Make, use these Docker Compose commands directly:

### PowerShell:
```powershell
# Build images
docker-compose build

# Start services (foreground)
docker-compose up

# Start services (background)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Clean up everything
docker-compose down -v
docker volume rm teski_frontend_node_modules
```

### Command Prompt:
Same commands as PowerShell above.

### Git Bash:
You can use the Make commands in Git Bash just like on Linux/Mac.

## Accessing the Application

Once running, open your browser:

- **Frontend**: http://localhost:5173
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Legacy Backend**: http://localhost:8100 (may have errors - see Known Issues)

## Windows-Specific Issues & Solutions

### Issue 1: "Cannot read properties of undefined (reading 'blocklist')"

**Solution:** Delete `frontend/node_modules` before starting Docker (see Step 3 above).

### Issue 2: File watching not working / Hot reload not triggering

Docker Desktop on Windows may have file watching issues. Solutions:

1. **Enable WSL 2 Backend** (Recommended)
   - Open Docker Desktop Settings → General
   - Check "Use the WSL 2 based engine"
   - Restart Docker Desktop

2. **Increase File Watchers** (if using WSL 2)
   ```bash
   # In WSL 2 terminal
   echo fs.inotify.max_user_watches=524288 | sudo tee -a /etc/sysctl.conf
   sudo sysctl -p
   ```

3. **Already Configured:** The docker-compose.yml already sets `CHOKIDAR_USEPOLLING=true` for polling-based file watching as a fallback.

### Issue 3: Volume mount performance is slow

**Solution:** Use WSL 2 backend and clone the repository inside WSL 2:

```bash
# In WSL 2 terminal (Ubuntu)
cd ~
git clone <repository-url>
cd teski
# Delete node_modules
rm -rf frontend/node_modules
# Run docker-compose
docker-compose up
```

This gives native Linux performance.

### Issue 4: Port already in use (EADDRINUSE)

**Solution:** Stop any processes using the ports:

```powershell
# Check what's using port 5173
netstat -ano | findstr :5173

# Kill the process (replace PID with actual process ID)
taskkill /PID <PID> /F

# Or for multiple ports
netstat -ano | findstr :5173
netstat -ano | findstr :8000
netstat -ano | findstr :8100
```

### Issue 5: Permission denied errors

**Solution:** Run PowerShell or Command Prompt as Administrator:
- Right-click → "Run as Administrator"

### Issue 6: Line ending issues (scripts fail to execute)

**Solution:** 
```powershell
# Convert line endings in shell scripts (if any)
dos2unix <filename>

# Or configure git properly (see Setup Steps above)
```

## Development Workflow on Windows

1. **Edit files normally** in your Windows editor (VS Code, etc.)
2. **Docker will auto-detect changes** and hot-reload
3. **View logs** in a separate terminal: `docker-compose logs -f`
4. **Restart if needed**: `docker-compose restart frontend` (or `api`, `legacy`)

## Troubleshooting Commands

```powershell
# Check if Docker is running
docker info

# Check running containers
docker ps

# Check all containers (including stopped)
docker ps -a

# View specific service logs
docker-compose logs frontend
docker-compose logs api
docker-compose logs legacy

# Shell into a container
docker-compose exec frontend sh
docker-compose exec api bash

# Rebuild from scratch
docker-compose down -v
docker-compose build --no-cache
docker-compose up
```

## Performance Tips

1. **Use WSL 2 Backend** - Much faster than Hyper-V
2. **Clone inside WSL 2** - Best performance for file operations
3. **Exclude from Windows Defender** - Add your project folder to exclusions
4. **Allocate more resources** - Docker Desktop Settings → Resources
   - CPUs: 4+
   - Memory: 4GB+

## Known Limitations

- **Legacy Backend** (port 8100) has a pre-existing database schema bug (not Windows-specific)
- **File watching** may be slightly slower than native development
- **Windows paths** with spaces may cause issues - avoid spaces in project path

## Alternative: Using WSL 2 Directly (Best Performance)

For the best experience, run everything in WSL 2:

1. **Open WSL 2 terminal** (Ubuntu/Debian)
   ```bash
   wsl
   ```

2. **Clone and run inside WSL 2**
   ```bash
   cd ~
   git clone <repository-url>
   cd teski
   rm -rf frontend/node_modules
   
   # Use Make commands
   make docker-up
   ```

3. **Access from Windows browser** - Works the same: http://localhost:5173

4. **Edit files from Windows** - Use VS Code with WSL extension:
   - Install "Remote - WSL" extension
   - Open folder in WSL: `code .` (from WSL terminal)

## Getting Help

If you encounter issues:

1. Check Docker Desktop is running
2. Check the DOCKER_SETUP.md file
3. View container logs: `docker-compose logs`
4. Restart Docker Desktop
5. Try rebuilding: `docker-compose build --no-cache`

## Quick Start (TL;DR)

```powershell
# 1. Delete corrupted node_modules
Remove-Item -Recurse -Force frontend\node_modules

# 2. Start Docker Desktop

# 3. Build and run
docker-compose build
docker-compose up

# 4. Open browser to http://localhost:5173
```

That's it! 🚀
