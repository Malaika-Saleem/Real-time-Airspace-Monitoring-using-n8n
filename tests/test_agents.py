# tests/test_agents.py
import pytest
from agents.traveler_agent import TravelerSupportAgent, traveler_agent
from agents.ops_analyst_agent import OpsAnalystAgent, ops_analyst
from agents.agent_registry import AgentRegistry

# These tests expect the MCP server running at default (127.0.0.1:8000).
# Start the server before running tests. Alternatively mock requests.

def test_ops_summary():
    a = OpsAnalystAgent()
    summary = a.summarize_region("region1")
    assert "total_flights" in summary
    assert isinstance(summary["total_flights"], int)

def test_traveler_basic_status():
    t = TravelerSupportAgent()
    # choose a callsign known in your flights.json (PGT87UJ used earlier)
    ans = t.answer_question("PGT87UJ", "Where is my flight now?")
    assert isinstance(ans, str)
    assert "lat=" in ans or "could not find" in ans

def test_a2a_nearby_check():
    reg = AgentRegistry()
    # pick lat/lon near the first flight in the JSON
    payload = {"task": "check_nearby_anomalies", "latitude": 41.3076, "longitude": 28.5942, "radius_km": 100}
    res = reg.call_agent("ops_analyst", payload)
    assert "nearby_alerts" in res
