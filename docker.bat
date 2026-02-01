@echo off
REM Docker Compose helper script for Windows
REM Alternative to using Make

if "%1"=="" goto usage

if "%1"=="build" goto build
if "%1"=="up" goto up
if "%1"=="down" goto down
if "%1"=="logs" goto logs
if "%1"=="restart" goto restart
if "%1"=="clean" goto clean
if "%1"=="shell-frontend" goto shell_frontend
if "%1"=="shell-api" goto shell_api
if "%1"=="shell-legacy" goto shell_legacy
goto usage

:build
echo Building Docker images...
docker-compose build
goto end

:up
echo Starting services...
REM Ensure database files exist
type nul > teski.db 2>nul
type nul > teski_v2.db 2>nul
docker-compose up
goto end

:down
echo Stopping services...
docker-compose down
goto end

:logs
if "%2"=="" (
    docker-compose logs -f
) else (
    docker-compose logs -f %2
)
goto end

:restart
if "%2"=="" (
    docker-compose restart
) else (
    docker-compose restart %2
)
goto end

:clean
echo Cleaning up Docker resources...
docker-compose down -v --rmi local
docker volume rm teski_frontend_node_modules 2>nul
echo Cleanup complete!
goto end

:shell_frontend
docker-compose exec frontend sh
goto end

:shell_api
docker-compose exec api bash
goto end

:shell_legacy
docker-compose exec legacy bash
goto end

:usage
echo.
echo Docker Compose Helper for Teski (Windows)
echo.
echo Usage: docker.bat [command]
echo.
echo Commands:
echo   build              Build all Docker images
echo   up                 Start all services (foreground)
echo   down               Stop all services
echo   logs [service]     View logs (optional: specify service name)
echo   restart [service]  Restart services (optional: specify service name)
echo   clean              Remove all containers, volumes, and images
echo   shell-frontend     Open shell in frontend container
echo   shell-api          Open shell in api container
echo   shell-legacy       Open shell in legacy container
echo.
echo Examples:
echo   docker.bat build
echo   docker.bat up
echo   docker.bat logs frontend
echo   docker.bat restart api
echo.
goto end

:end
