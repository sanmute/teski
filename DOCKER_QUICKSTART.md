# 🐳 Docker Quick Reference

Choose your operating system:

## 🍎 macOS / 🐧 Linux

```bash
# First time: Delete corrupted node_modules
sudo rm -rf frontend/node_modules

# Build and start
make docker-up
```

**Full guide:** [DOCKER_SETUP.md](DOCKER_SETUP.md)

---

## 🪟 Windows

```powershell
# PowerShell - Fix frontend first
.\docker.ps1 fix-frontend
.\docker.ps1 up

# Or use batch file
docker.bat up
```

**Full guide:** [DOCKER_WINDOWS.md](DOCKER_WINDOWS.md)

---

## 🌐 Access Points

Once running:

- **Frontend**: http://localhost:5173
- **API**: http://localhost:8000  
- **API Docs**: http://localhost:8000/docs

## 🔧 Common Commands

| Task | macOS/Linux | Windows (PowerShell) | Windows (Batch) |
|------|-------------|---------------------|-----------------|
| Build | `make docker-build` | `.\docker.ps1 build` | `docker.bat build` |
| Start | `make docker-up` | `.\docker.ps1 up` | `docker.bat up` |
| Start (bg) | `make docker-up-d` | `.\docker.ps1 up-d` | - |
| Logs | `make docker-logs` | `.\docker.ps1 logs` | `docker.bat logs` |
| Stop | `make docker-down` | `.\docker.ps1 down` | `docker.bat down` |
| Clean | `make docker-clean` | `.\docker.ps1 clean` | `docker.bat clean` |
| Fix Frontend | `sudo rm -rf frontend/node_modules && make docker-up` | `.\docker.ps1 fix-frontend` | - |

## ⚠️ Troubleshooting

**Frontend shows Tailwind error?**
→ Delete `frontend/node_modules` and restart Docker

**Port 5173 already in use?**
→ Kill local Node processes: `lsof -ti:5173 | xargs kill` (Mac/Linux) or `netstat -ano | findstr :5173` (Windows)

**Changes not reloading?**
→ File watching is enabled via `CHOKIDAR_USEPOLLING=true`

---

For detailed information, see:
- [DOCKER_SETUP.md](DOCKER_SETUP.md) - Full setup guide (Mac/Linux)
- [DOCKER_WINDOWS.md](DOCKER_WINDOWS.md) - Windows-specific guide
