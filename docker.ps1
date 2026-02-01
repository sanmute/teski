# Docker Compose helper script for Windows PowerShell
# Alternative to using Make

param(
    [Parameter(Mandatory=$false, Position=0)]
    [string]$Command = "",
    
    [Parameter(Mandatory=$false, Position=1)]
    [string]$Service = ""
)

function Show-Usage {
    Write-Host ""
    Write-Host "Docker Compose Helper for Teski (Windows PowerShell)" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage: .\docker.ps1 [command] [service]" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Commands:" -ForegroundColor Green
    Write-Host "  build              Build all Docker images"
    Write-Host "  up                 Start all services (foreground)"
    Write-Host "  up-d               Start all services (background)"
    Write-Host "  down               Stop all services"
    Write-Host "  logs [service]     View logs (optional: specify service name)"
    Write-Host "  restart [service]  Restart services (optional: specify service name)"
    Write-Host "  clean              Remove all containers, volumes, and images"
    Write-Host "  shell-frontend     Open shell in frontend container"
    Write-Host "  shell-api          Open shell in api container"
    Write-Host "  shell-legacy       Open shell in legacy container"
    Write-Host "  fix-frontend       Fix frontend node_modules issue"
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor Green
    Write-Host "  .\docker.ps1 build"
    Write-Host "  .\docker.ps1 up"
    Write-Host "  .\docker.ps1 logs frontend"
    Write-Host "  .\docker.ps1 restart api"
    Write-Host ""
}

function Ensure-DatabaseFiles {
    # Create empty database files if they don't exist
    if (-not (Test-Path "teski.db")) {
        New-Item -ItemType File -Path "teski.db" -Force | Out-Null
        Write-Host "Created teski.db" -ForegroundColor Gray
    }
    if (-not (Test-Path "teski_v2.db")) {
        New-Item -ItemType File -Path "teski_v2.db" -Force | Out-Null
        Write-Host "Created teski_v2.db" -ForegroundColor Gray
    }
}

switch ($Command) {
    "build" {
        Write-Host "Building Docker images..." -ForegroundColor Cyan
        docker-compose build
    }
    
    "up" {
        Write-Host "Starting services..." -ForegroundColor Cyan
        Ensure-DatabaseFiles
        docker-compose up
    }
    
    "up-d" {
        Write-Host "Starting services in background..." -ForegroundColor Cyan
        Ensure-DatabaseFiles
        docker-compose up -d
        Write-Host ""
        Write-Host "Services started! Access at:" -ForegroundColor Green
        Write-Host "  Frontend: http://localhost:5173"
        Write-Host "  API:      http://localhost:8000"
        Write-Host "  API Docs: http://localhost:8000/docs"
        Write-Host ""
        Write-Host "View logs with: .\docker.ps1 logs" -ForegroundColor Yellow
    }
    
    "down" {
        Write-Host "Stopping services..." -ForegroundColor Cyan
        docker-compose down
    }
    
    "logs" {
        if ($Service) {
            docker-compose logs -f $Service
        } else {
            docker-compose logs -f
        }
    }
    
    "restart" {
        if ($Service) {
            Write-Host "Restarting $Service..." -ForegroundColor Cyan
            docker-compose restart $Service
        } else {
            Write-Host "Restarting all services..." -ForegroundColor Cyan
            docker-compose restart
        }
    }
    
    "clean" {
        Write-Host "Cleaning up Docker resources..." -ForegroundColor Yellow
        docker-compose down -v --rmi local
        docker volume rm teski_frontend_node_modules 2>$null
        Write-Host "Cleanup complete!" -ForegroundColor Green
    }
    
    "shell-frontend" {
        Write-Host "Opening shell in frontend container..." -ForegroundColor Cyan
        docker-compose exec frontend sh
    }
    
    "shell-api" {
        Write-Host "Opening shell in api container..." -ForegroundColor Cyan
        docker-compose exec api bash
    }
    
    "shell-legacy" {
        Write-Host "Opening shell in legacy container..." -ForegroundColor Cyan
        docker-compose exec legacy bash
    }
    
    "fix-frontend" {
        Write-Host "Fixing frontend node_modules issue..." -ForegroundColor Yellow
        Write-Host "  1. Stopping services..." -ForegroundColor Gray
        docker-compose down
        
        Write-Host "  2. Removing frontend/node_modules..." -ForegroundColor Gray
        if (Test-Path "frontend/node_modules") {
            Remove-Item -Recurse -Force "frontend/node_modules" -ErrorAction SilentlyContinue
            Write-Host "     Removed!" -ForegroundColor Green
        } else {
            Write-Host "     Already removed." -ForegroundColor Gray
        }
        
        Write-Host "  3. Removing Docker volume..." -ForegroundColor Gray
        docker volume rm teski_frontend_node_modules 2>$null
        
        Write-Host ""
        Write-Host "Frontend fixed! Now run: .\docker.ps1 up" -ForegroundColor Green
    }
    
    default {
        if ($Command -eq "" -or $Command -eq "help" -or $Command -eq "--help" -or $Command -eq "-h") {
            Show-Usage
        } else {
            Write-Host "Unknown command: $Command" -ForegroundColor Red
            Write-Host ""
            Show-Usage
        }
    }
}
