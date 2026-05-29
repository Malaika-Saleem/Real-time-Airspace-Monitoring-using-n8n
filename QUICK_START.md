# Quick Start Guide

## Step 1: Activate Virtual Environment

**On Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
```

**On Windows (Command Prompt):**
```cmd
venv\Scripts\activate.bat
```

**On Linux/Mac:**
```bash
source venv/bin/activate
```

You should see `(venv)` at the beginning of your command prompt when activated.

## Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 3: Verify .env File

Make sure your `.env` file exists with your Groq API key:
```bash
# Check if .env exists
cat .env
# or on Windows:
type .env
```

If it doesn't exist, create it (see SETUP_ENV.md).

## Step 4: Start MCP Server

**Important**: Make sure you're in the project root directory (not inside `server/` folder).

In one terminal (keep it running):
```bash
# Make sure you're here: D:\7TH SEMESTER\Agentic AI\A3
python -m uvicorn server.mcp_server:app --reload --port 8000
```

If you get "relative import with no known parent package" error, you're in the wrong directory. Navigate to project root first.

Test it: Open `http://localhost:8000/mcp/tool/flights.list?region=region1` in your browser.

## Step 5: Test the System

**Option A: CLI Mode**
```bash
python main.py
```

**Option B: API Server (for frontend)**
```bash
python api_server.py
```

Then test with:
```bash
# Test operations analysis
curl -X POST http://localhost:8001/ops/analyze -H "Content-Type: application/json" -d "{\"region\": \"region1\"}"

# Test traveler query
curl -X POST http://localhost:8001/traveler/query -H "Content-Type: application/json" -d "{\"identifier\": \"PGT87UJ\", \"question\": \"Where is my flight now?\"}"
```

## Troubleshooting

1. **"Module not found" errors**: Make sure virtual environment is activated
2. **"GROQ_API_KEY not set"**: Check your `.env` file exists and has the key
3. **"Connection refused" to MCP server**: Make sure MCP server is running on port 8000
4. **"No flights found"**: Check that `region1_latest.json` exists and has data

