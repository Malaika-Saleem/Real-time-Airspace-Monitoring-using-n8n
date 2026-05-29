# Airspace Copilot — MCP + CrewAI Agents

## Overview
This project provides:
- A FastAPI-based MCP server exposing flight tools (`flights.list`, `flights.get`, `alerts.list`).
- Two CrewAI agents with Groq LLM:
  - **Ops Analyst Agent**: Analyzes region snapshots, detects anomalies, and provides operational summaries.
  - **Traveler Support Agent**: Answers traveler questions about specific flights and can delegate to Ops Analyst (A2A communication).
- Agent-to-Agent (A2A) communication via AgentRegistry.
- Simple CLI and API server for frontend integration.

## Architecture

```
┌─────────────┐
│   n8n       │ → Fetches OpenSky API → Stores snapshots (JSON)
└──────┬──────┘
       │
       ↓
┌─────────────┐
│  MCP Server │ → Reads snapshots → Exposes tools via HTTP
│  (FastAPI)  │
└──────┬──────┘
       │
       ↓
┌─────────────┐
│ CrewAI      │ → Ops Analyst Agent ──┐
│ Agents      │ → Traveler Agent ──────┤ A2A Communication
│ (Groq LLM)  │                        │
└─────────────┘                        │
       │                               │
       ↓                               │
┌─────────────┐                        │
│   Frontend  │ ← API Server ←─────────┘
│     (UI)    │
└─────────────┘
```

## Prerequisites

1. Python 3.8+
2. Groq API key (free tier available at https://console.groq.com/)
3. n8n running locally (your partner's responsibility)

## Installation

1. **Activate the virtual environment** (if using one):
   
   On Windows (PowerShell):
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```
   
   If you get an execution policy error:
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```
   
   On Windows (Command Prompt):
   ```cmd
   venv\Scripts\activate.bat
   ```
   
   On Linux/Mac:
   ```bash
   source venv/bin/activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   
   **Note**: If you don't have a virtual environment, create one first:
   ```bash
   python -m venv venv
   # Then activate it (see step 1)
   # Then install dependencies
   ```

3. **Set up environment variables**:
   
   Create a `.env` file in the project root with your Groq API key:
   ```bash
   GROQ_API_KEY=your_groq_api_key_here
   MCP_BASE=http://127.0.0.1:8000/mcp/tool
   API_PORT=8001
   ```
   
   **Important**: The `.env` file is already in `.gitignore` to protect your API keys. Never commit API keys to version control!
   
   **Quick setup on Windows (PowerShell)**:
   ```powershell
   @"
   GROQ_API_KEY=your_groq_api_key_here
   MCP_BASE=http://127.0.0.1:8000/mcp/tool
   API_PORT=8001
   "@ | Out-File -FilePath .env -Encoding utf8
   ```

## Running the System

### 1. Start the MCP Server

The MCP server reads flight data from `region1_latest.json` (populated by n8n) in the project root.

**Important**: Always run from the project root directory (not from inside `server/`):

```bash
# Make sure you're in the project root (D:\7TH SEMESTER\Agentic AI\A3)
python -m uvicorn server.mcp_server:app --reload --port 8000
```

**Or use the helper script**:
```powershell
.\start_mcp_server.ps1
```

**If you get "relative import" errors**, it means you're in the wrong directory. Navigate to the project root first:
```bash
cd "D:\7TH SEMESTER\Agentic AI\A3"
python -m uvicorn server.mcp_server:app --reload --port 8000
```

**Data Source**: The MCP server automatically looks for `region1_latest.json` in the project root (from n8n). If not found, it falls back to `data/flights.json`.

The MCP server exposes:
- `GET /mcp/tool/flights.list?region=region1` - Get flights for a region
- `GET /mcp/tool/flights.get?identifier=THY4KZ` - Get a specific flight by callsign or ICAO24
- `GET /mcp/tool/alerts.list` - Get active alerts
- `GET /mcp/manifest` - MCP manifest

**Test the MCP server**: Open `http://localhost:8000/mcp/tool/flights.list?region=region1` in your browser to verify it's working.

### 2. Run Agents (CLI Mode)

For interactive testing:

```bash
python main.py
```

This provides a simple CLI to:
- Analyze regions (Operations Mode)
- Query flights (Traveler Mode)

### 3. Run API Server (for Frontend)

For frontend integration:

```bash
python api_server.py
```

The API server exposes:
- `POST /ops/analyze` - Analyze a region
  ```json
  {"region": "region1"}
  ```
- `POST /traveler/query` - Query about a flight
  ```json
  {
    "identifier": "THY4KZ",
    "question": "Where is my flight now?"
  }
  ```

## Agent Details

### Ops Analyst Agent

**Role**: Airspace Operations Analyst  
**Tools**: `flights_list_region`, `alerts_list_active`  
**Capabilities**:
- Fetches region snapshots via MCP
- Detects anomalies:
  - Low speed at high altitude
  - Rapid vertical rate changes
  - Low altitude at high speed
- Generates natural-language summaries using Groq LLM

**Example Task**:
```python
from agents.crewai_agents import analyze_region
result = analyze_region("region1")
print(result)
```

### Traveler Support Agent

**Role**: Personal Flight Watchdog Assistant  
**Tools**: `flights_get_by_identifier`, `alerts_list_active`  
**Capabilities**:
- Answers questions about specific flights
- Explains flight status in plain language
- Can delegate to Ops Analyst for nearby anomaly checks (A2A)

**Example Task**:
```python
from agents.crewai_agents import answer_traveler_question
result = answer_traveler_question("THY4KZ", "Where is my flight now?")
print(result)
```

## A2A Communication

The Traveler Support Agent can call the Ops Analyst Agent through the `AgentRegistry`:

```python
from agents.agents_registry import AgentRegistry

registry = AgentRegistry()
result = registry.call_agent("ops_analyst", {
    "task": "check_nearby_anomalies",
    "latitude": 41.0,
    "longitude": 29.0,
    "radius_km": 50.0
})
```

**Note**: The file is `agents_registry.py` (with 's'), not `agent_registry.py`.

## MCP Tools

All agents access data through MCP tools, not directly from files:

1. **flights_list_region(region)**: Get latest snapshot for a region
2. **flights_get_by_identifier(identifier)**: Get flight by callsign or ICAO24
3. **alerts_list_active()**: Get all active alerts

## Data Structure

The system reads flight data in this priority order:

1. **`region1_latest.json`** (in project root) - **Primary source from n8n**
   - This is the file your partner's n8n workflow populates
   - Should contain an array of flight objects with OpenSky API format
   - Format: `[{icao24, callsign, latitude, longitude, ...}, ...]`

2. **`data/flights.json`** - Fallback flight data
   - Used if `region1_latest.json` is not found
   - Can be region-specific: `{"region1": [...], "region2": [...]}`

3. **`data/alerts.json`** - Active alerts
   - Stores anomaly alerts generated by the system
   - Format: `[{icao24, callsign, anomalies: [...], ...}, ...]`

**Note**: The MCP server automatically detects and uses `region1_latest.json` when available, which is the file your n8n partner provides.

## Testing

Run tests:
```bash
pytest tests/
```

## Project Structure

```
.
├── agents/
│   ├── __init__.py
│   ├── crewai_agents.py      # Main CrewAI agents with Groq LLM
│   ├── ops_analyst_agent.py  # Ops Analyst (non-CrewAI, for A2A)
│   ├── traveller_agent.py    # Traveler Support (non-CrewAI, for A2A)
│   └── agents_registry.py    # A2A communication registry
├── server/
│   ├── __init__.py
│   ├── mcp_server.py         # FastAPI MCP server
│   ├── db.py                 # Data access layer (reads region1_latest.json)
│   └── models.py             # Pydantic models
├── data/
│   ├── flights.json          # Fallback flight data
│   ├── alerts.json           # Active alerts
│   └── regions.json          # Region definitions
├── utils/
│   └── test_data_format.py   # Data validation utility
├── region1_latest.json       # Primary data source from n8n (in project root)
├── main.py                   # CLI entry point
├── api_server.py             # API server for frontend
├── .env                      # Environment variables (Groq API key)
├── requirements.txt
├── README.md
└── QUICK_START.md            # Quick setup guide
```

## Notes

- **Data Source**: The system uses `region1_latest.json` from n8n as the primary data source
- **Fallback Handling**: The system is designed to work even when OpenSky API is unavailable (uses cached snapshots from n8n)
- **LLM**: All agents use Groq LLM (via LiteLLM) for natural language generation
- **MCP Tools**: Agents access data through MCP tools, not directly from files (proper abstraction)
- **A2A Communication**: Traveler Agent can consult Ops Analyst when needed (e.g., checking nearby anomalies)
- **API Key**: The Groq API key is loaded from `.env` file automatically using `python-dotenv`

## Quick Test

After setup, test the complete flow:

1. **Start MCP Server** (Terminal 1):
   ```powershell
   python -m uvicorn server.mcp_server:app --reload --port 8000
   ```

2. **Run Main Application** (Terminal 2):
   ```powershell
   python main.py
   # Select option 1 to test Operations Mode
   # Select option 2 to test Traveler Mode
   ```

3. **Or Test API Server** (Terminal 2):
   ```powershell
   python api_server.py
   # Then test with curl or Postman
   ```

## Troubleshooting

### Common Issues

1. **"Invalid API Key" Error**:
   - Make sure `.env` file exists in the project root
   - Verify `GROQ_API_KEY` is set correctly (should start with `gsk_`)
   - Ensure `python-dotenv` is installed: `pip install python-dotenv`
   - The system automatically loads `.env` using `load_dotenv()`

2. **"Relative import with no known parent package" Error**:
   - You're running commands from the wrong directory
   - Always run from the project root: `D:\7TH SEMESTER\Agentic AI\A3`
   - Never run from inside `server/` or `agents/` directories
   - Use: `python -m uvicorn server.mcp_server:app` (not `python server/mcp_server.py`)

3. **"Module not found" Errors**:
   - Make sure virtual environment is activated (you should see `(venv)` in prompt)
   - Install dependencies: `pip install -r requirements.txt`
   - Verify you're using the correct Python interpreter from venv

4. **MCP Server Connection Error**:
   - Ensure MCP server is running: `python -m uvicorn server.mcp_server:app --reload --port 8000`
   - Check it's accessible: `http://localhost:8000/mcp/manifest`
   - Verify the port 8000 is not already in use

5. **No Flight Data / Empty Results**:
   - Check that `region1_latest.json` exists in the project root (from n8n)
   - Verify the file has valid JSON with flight data
   - The MCP server looks for `region1_latest.json` first, then falls back to `data/flights.json`
   - Test data loading: `python utils/test_data_format.py`

6. **"LiteLLM is not available" Error**:
   - Install litellm: `pip install litellm`
   - It's already in `requirements.txt`, so run: `pip install -r requirements.txt`

7. **Import Errors (traveler_agent vs traveller_agent)**:
   - The file is named `traveller_agent.py` (British spelling with double 'l')
   - All imports have been fixed to use the correct name
   - If you see this error, make sure you have the latest code

### Verification Steps

1. **Check API Key**:
   ```python
   python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('Key loaded:', bool(os.getenv('GROQ_API_KEY')))"
   ```

2. **Check Data File**:
   ```powershell
   Test-Path region1_latest.json
   ```

3. **Test MCP Server**:
   ```powershell
   # In browser or using curl:
   curl http://localhost:8000/mcp/tool/flights.list?region=region1
   ```

4. **Test Imports**:
   ```python
   python -c "from agents.crewai_agents import analyze_region; print('Imports OK')"
   ```
