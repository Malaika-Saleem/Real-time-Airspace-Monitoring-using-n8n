# Start MCP Server - Run this from project root
Write-Host "Starting MCP Server..." -ForegroundColor Green
Write-Host "Make sure you're in the project root directory!" -ForegroundColor Yellow
python -m uvicorn server.mcp_server:app --reload --port 8000

