"""
CrewAI Agents for Airspace Copilot System
- Ops Analyst Agent: Analyzes region snapshots and detects anomalies
- Traveler Support Agent: Answers traveler questions about specific flights
- Both agents use Groq LLM and MCP tools
"""

import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, LLM
from crewai.tools import tool
import requests
from typing import Dict, Any, Optional

# Load environment variables from .env file
# override=False means terminal/env variables take precedence over .env file
load_dotenv(override=False)

# MCP Server base URL
MCP_BASE = os.getenv("MCP_BASE", "http://127.0.0.1:8000/mcp/tool")

# Groq LLM Configuration
# LiteLLM/Groq requires the API key to be set as an environment variable
# Check environment first (terminal variable), then .env file
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()  # Strip any whitespace
# Remove any leading/trailing special characters that might have been accidentally included
GROQ_API_KEY = GROQ_API_KEY.lstrip('<').lstrip('>').strip()
# Additional cleanup - remove any non-printable characters
GROQ_API_KEY = ''.join(char for char in GROQ_API_KEY if char.isprintable())
if not GROQ_API_KEY:
    print("Warning: GROQ_API_KEY not set. Please set it in .env file or environment variables.")
    print("Current working directory:", os.getcwd())
    print(".env file exists:", os.path.exists(".env"))
else:
    # Ensure it's set in environment for LiteLLM (LiteLLM reads from os.environ)
    os.environ["GROQ_API_KEY"] = GROQ_API_KEY
    # Debug: Show where the key came from
    env_key = os.environ.get("GROQ_API_KEY", "")
    if env_key == GROQ_API_KEY:
        source = "environment variable" if os.getenv("GROQ_API_KEY") == GROQ_API_KEY else ".env file"
        print(f"Groq API key loaded from {source} (length: {len(GROQ_API_KEY)}, starts with: {GROQ_API_KEY[:10]}...)")
    else:
        print(f"Warning: Key mismatch! Environment has different key.")
        print(f"  Using key: {GROQ_API_KEY[:10]}...")

# Configure Groq LLM
# CrewAI uses LiteLLM for Groq, so we use the groq/ prefix
# For LiteLLM with Groq, we need to ensure the API key is properly set
# Try different approaches to ensure the key is passed correctly
try:
    # Method 1: Pass api_key directly (preferred)
    groq_llm = LLM(
        model="groq/llama-3.3-70b-versatile",  # Updated: llama-3.1-70b-versatile was decommissioned
        api_key=GROQ_API_KEY,
        temperature=0.3
    )
except Exception as e:
    print(f"Warning: Error creating LLM with api_key parameter: {e}")
    # Method 2: Rely on environment variable only
    groq_llm = LLM(
        model="groq/llama-3.3-13b",  # Updated: llama-3.1-70b-versatile was decommissioned
        temperature=0.3
    )

# ===== MCP Tools =====

@tool("flights_list_region")
def flights_list_region(region: str = "region1", limit: int = 20) -> Dict[str, Any]:
    """
    Get the latest flight snapshot for a region (limited to avoid token limits).
    
    Args:
        region: The region name (e.g., "region1", "region2")
        limit: Maximum number of flights to return (default: 100 to stay within token limits)
    
    Returns:
        Dictionary with region, last_updated, flights list (limited), and count
    """
    limit = min(limit, 20)  # <-- Force max 20 flights
    url = f"{MCP_BASE}/flights.list?region={region}"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            # Limit the number of flights to avoid token limit errors
            if "flights" in data and isinstance(data["flights"], list):
                total_flights = len(data["flights"])
                data["flights"] = data["flights"][:limit]
                data["total_count"] = total_flights
                data["returned_count"] = len(data["flights"])
                if total_flights > limit:
                    data["note"] = f"Showing first {limit} of {total_flights} flights to stay within token limits"
            return data
        return {"error": f"HTTP {resp.status_code}: Could not fetch flights"}
    except Exception as e:
        return {"error": f"Exception: {str(e)}"}

@tool("flights_get_by_identifier")
def flights_get_by_identifier(identifier: str) -> Dict[str, Any]:
    """
    Get a specific flight by callsign or ICAO24 identifier.
    
    Args:
        identifier: Flight callsign (e.g., "THY4KZ") or ICAO24 (e.g., "4baa1a")
    
    Returns:
        Flight data dictionary or error message
    """
    url = f"{MCP_BASE}/flights.get?identifier={identifier}"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            return resp.json()
        elif resp.status_code == 404:
            return {"error": f"Flight '{identifier}' not found"}
        return {"error": f"HTTP {resp.status_code}: Could not fetch flight"}
    except Exception as e:
        return {"error": f"Exception: {str(e)}"}

@tool("alerts_list_active")
def alerts_list_active() -> list:
    """
    Get all active flight alerts/anomalies.
    
    Returns:
        List of alert dictionaries
    """
    url = f"{MCP_BASE}/alerts.list?active_only=true"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            return resp.json()
        return []
    except Exception as e:
        return []

# ===== Agent Definitions =====

ops_analyst_agent = Agent(
    role="Airspace Operations Analyst",
    goal="Monitor flights in a region, detect anomalies (unusual speed/altitude patterns, rapid changes), and provide clear operational summaries",
    backstory="""You are an experienced airspace operations analyst with deep knowledge of flight patterns and safety protocols. 
    You analyze real-time flight data to identify anomalies such as:
    - Low speed at high altitude (potential stall risk)
    - Rapid vertical rate changes (unusual climb/descent)
    - Low altitude at high speed (potential safety concern)
    - Stationary flights at altitude (unusual behavior)
    
    You provide clear, actionable summaries for operations teams.""",
    tools=[flights_list_region, alerts_list_active],
    llm=groq_llm,
    verbose=True,
    allow_delegation=False
)

traveler_support_agent = Agent(
    role="Personal Flight Watchdog Assistant",
    goal="Help travelers understand their flight status, location, altitude, speed, and any concerns in plain language",
    backstory="""You are a friendly and helpful flight support assistant. Travelers rely on you to answer questions about their flights.
    You can:
    - Tell them where their flight is now (latitude/longitude)
    - Explain if the flight is climbing, descending, or level
    - Check for any anomalies or alerts related to their flight
    - Answer questions about flight status in natural, easy-to-understand language
    
    When travelers ask about nearby flights or regional issues, you can collaborate with the Operations Analyst.""",
    tools=[flights_get_by_identifier, alerts_list_active],
    llm=groq_llm,
    verbose=True,
    allow_delegation=True  # Can delegate to ops_analyst_agent
)

# ===== Tasks =====

def create_ops_summary_task(region: str = "region1") -> Task:
    """Create a task for the ops analyst to summarize a region."""
    return Task(
        description=f"""Analyze the current flight situation in {region}.
        
        Steps:
        1. Use flights_list_region to get the latest snapshot for {region} (the tool will return a limited sample to stay within token limits)
        2. Review the flights and identify anomalies using these criteria:
           - Low speed (< 50 m/s) at high altitude (> 5000 m)
           - Rapid vertical rate (> 20 m/s or < -20 m/s)
           - Low altitude (< 500 m) at high speed (> 200 m/s)
        3. Check alerts_list_active for any system-generated alerts
        4. Provide a clear summary including:
           - Total number of flights in the region (check the total_count field if available)
           - Number of anomalous flights found in the sample
           - Details of the most critical anomalies (callsign, issue, location) - focus on the top 5-10 most critical
           - A natural language summary suitable for operations staff
        
        Important: The tool returns a limited sample of flights to avoid token limits. Focus your analysis on the flights provided, and note if there are more flights in the region.
        
        Format your response as a clear, professional operations report.""",
        agent=ops_analyst_agent,
        expected_output="A detailed operations summary with flight count, anomaly count, and descriptions of critical issues"
    )

def create_traveler_query_task(identifier: str, question: str) -> Task:
    """Create a task for the traveler support agent to answer a question."""
    return Task(
        description=f"""Answer the traveler's question about flight {identifier}.
        
        Question: {question}
        
        Steps:
        1. Use flights_get_by_identifier to get the latest data for flight {identifier}
        2. If the question asks about location/status/climbing/descending, analyze the flight data
        3. If the question asks about nearby issues or other flights, you may need to collaborate with the Operations Analyst
        4. Use alerts_list_active to check if there are any alerts for this flight
        5. Provide a clear, friendly answer in plain language
        
        Important: Always base your answer on the actual flight data. If data is unavailable, say so clearly.""",
        agent=traveler_support_agent,
        expected_output="A clear, friendly answer to the traveler's question based on real flight data"
    )

# ===== Crew Setup =====

def create_ops_crew(region: str = "region1") -> Crew:
    """Create a crew for operations analysis."""
    task = create_ops_summary_task(region)
    return Crew(
        agents=[ops_analyst_agent],
        tasks=[task],
        verbose=True
    )

def create_traveler_crew(identifier: str, question: str) -> Crew:
    """Create a crew for traveler support."""
    task = create_traveler_query_task(identifier, question)
    return Crew(
        agents=[traveler_support_agent, ops_analyst_agent],  # Include ops_analyst for delegation
        tasks=[task],
        verbose=True
    )

# ===== Convenience Functions =====

def analyze_region(region: str = "region1") -> str:
    """
    Analyze a region and return a summary.
    
    Args:
        region: Region name to analyze
    
    Returns:
        Summary string
    """
    crew = create_ops_crew(region)
    result = crew.kickoff()
    return str(result)

def answer_traveler_question(identifier: str, question: str) -> str:
    """
    Answer a traveler's question about their flight.
    
    Args:
        identifier: Flight callsign or ICAO24
        question: The traveler's question
    
    Returns:
        Answer string
    """
    crew = create_traveler_crew(identifier, question)
    result = crew.kickoff()
    return str(result)

