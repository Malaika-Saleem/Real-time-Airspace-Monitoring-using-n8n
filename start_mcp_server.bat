@echo off
REM Start MCP Server - Run this from project root
echo Starting MCP Server...
echo Make sure you're in the project root directory!
python -m uvicorn server.mcp_server:app --reload --port 8000
pause

