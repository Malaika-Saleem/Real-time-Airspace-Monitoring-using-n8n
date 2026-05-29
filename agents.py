# agents.py
from crewai import Agent
from crewai.tools import tool
import requests

MCP_BASE = "http://127.0.0.1:8000"

# ---- Tools using decorator ----
@tool(name="flights.list", description="Return all flights from the MCP server")
def flights_list(**kwargs):
    resp = requests.get(f"{MCP_BASE}/flights/list")
    return resp.json() if resp.status_code == 200 else {"error": "Could not fetch flights"}

@tool(name="flights.get", description="Return details of a specific flight by callsign")
def get_flight(flight_id, **kwargs):
    resp = requests.get(f"{MCP_BASE}/flights/get/{flight_id}")
    return resp.json() if resp.status_code == 200 else {"error": "Flight not found"}

@tool(name="alerts.list", description="Return all active flight alerts")
def alerts_list(**kwargs):
    resp = requests.get(f"{MCP_BASE}/alerts/list")
    return resp.json() if resp.status_code == 200 else {"error": "Could not fetch alerts"}

# ---- Agents ----
ops_agent = Agent(
    role="Airspace Operations Analyst",
    goal="Monitor flights and detect anomalies",
    backstory="You analyze flight data and flag unusual behavior",
    tools=[flights_list, alerts_list],
    verbose=True
)

traveler_agent = Agent(
    role="Flight Support Assistant",
    goal="Answer traveler questions about flights",
    backstory="Help travelers understand their flight status and alerts",
    tools=[get_flight, alerts_list],
    verbose=True
)
