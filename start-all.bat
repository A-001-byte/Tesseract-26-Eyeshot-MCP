@echo off
echo Starting Tesseract Services...

if not exist d:\Tesseract-26-Eyeshot-MCP\frontend\node_modules (
	echo [setup] Installing frontend dependencies...
	call npm --prefix d:\Tesseract-26-Eyeshot-MCP\frontend install
	if errorlevel 1 (
		echo [setup] Frontend dependency install failed.
		exit /b 1
	)
)

echo [1/4] Starting CAD Engine (port 5000)...
start "CAD-Engine" cmd /k "cd /d d:\Tesseract-26-Eyeshot-MCP\cad-engine && python python_cad_engine.py"

timeout /t 3 /nobreak >nul

echo [2/4] Starting LLM Service (port 7000)...
start "LLM-Service" cmd /k "cd /d d:\Tesseract-26-Eyeshot-MCP\llm-service && python -m uvicorn app.main:app --host 127.0.0.1 --port 7000"

timeout /t 2 /nobreak >nul

echo [3/4] Starting Backend MCP (port 8000)...
start "Backend-MCP" cmd /k "cd /d d:\Tesseract-26-Eyeshot-MCP\backend-mcp && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"

timeout /t 2 /nobreak >nul

echo [4/4] Starting Frontend (port 3000)...
start "Frontend" cmd /k "cd /d d:\Tesseract-26-Eyeshot-MCP\frontend && npm run dev -- --host 0.0.0.0 --port 3000"

echo.
echo All services starting...
echo.
echo   CAD Engine:  http://localhost:5000
echo   LLM Service: http://localhost:7000
echo   Backend MCP: http://localhost:8000
echo   Frontend:    http://localhost:3000
echo.
echo Opening browser in 5 seconds...
timeout /t 5 /nobreak >nul
start http://localhost:3000
