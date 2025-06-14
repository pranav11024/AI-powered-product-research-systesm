@echo off
echo Starting Product Research System...

echo Starting ML Service...
start "ML Service" python ml_service.py

timeout /t 3

echo Starting Scraper Service...
start "Scraper Service" python scraper_service.py

timeout /t 3

echo Starting API Server...
start "API Server" python api_server.py

timeout /t 3

echo Starting n8n...
start "n8n" n8n start

echo All services started!
echo.
echo Dashboard: http://127.0.0.1:8000
echo n8n Editor: http://127.0.0.1:5678
echo.
pause