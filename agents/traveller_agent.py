# agents/traveler_agent.py
"""
Traveler Support Agent:
- Uses MCP tools to fetch a single flight
- Answers user-style questions (status, climbing/descending, nearby anomalies)
- Can call OpsAnalystAgent through AgentRegistry for A2A requests
"""

from typing import Optional, Dict, Any
import requests
import os
import time
import json

from .agents_registry import AgentRegistry

MCP_BASE = os.getenv("MCP_BASE", "http://127.0.0.1:8000/mcp/tool")

class TravelerSupportAgent:
    def __init__(self, mcp_base: str = MCP_BASE):
        self.mcp_base = mcp_base
        self.registry = AgentRegistry()

    def _call_tool_flights_get(self, identifier: str) -> Optional[Dict[str, Any]]:
        url = f"{self.mcp_base}/flights.get?identifier={identifier}"
        try:
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                return r.json()
        except requests.RequestException:
            return None
        return None

    def _format_flight_summary(self, flight: Dict[str, Any]) -> str:
        # grounded, friendly text
        lat = flight.get("latitude")
        lon = flight.get("longitude")
        alt = flight.get("geo_altitude") or flight.get("baro_altitude")
        speed = flight.get("velocity_mps")
        vr = flight.get("vertical_rate_mps")
        callsign = flight.get("callsign") or flight.get("icao24")
        last_contact = flight.get("last_contact")
        when = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(last_contact)) if last_contact else "N/A"
        trend = "level"
        if vr is not None:
            if vr > 1.0:
                trend = "climbing"
            elif vr < -1.0:
                trend = "descending"
        return (f"{callsign} last seen at {when}. Location: lat={lat:.4f}, lon={lon:.4f}. "
                f"Altitude ≈ {alt} m, speed ≈ {speed} m/s. The aircraft appears to be {trend}.")

    def answer_question(self, identifier: str, question: str) -> str:
        """
        Main entry. identifier: callsign or icao24.
        question: user's free text.
        """
        flight = self._call_tool_flights_get(identifier)
        if not flight:
            return f"Sorry — I could not find flight '{identifier}'. The MCP server may be down or the ID is wrong."

        q = question.lower()
        # Simple intent detection
        if "where" in q or "now" in q or "status" in q:
            summary = self._format_flight_summary(flight)
            return summary

        if "climb" in q or "descend" in q or "vertical" in q:
            vr = flight.get("vertical_rate_mps")
            if vr is None:
                return "Vertical rate data is unavailable for this flight."
            if vr > 1:
                return f"The flight is currently climbing at about {vr:.2f} m/s."
            if vr < -1:
                return f"The flight is currently descending at about {abs(vr):.2f} m/s."
            return "The flight is roughly level (no significant vertical rate)."

        if "near" in q and "issue" in q or "anomal" in q or "other flights" in q:
            # A2A: call OpsAnalystAgent via registry
            # We'll send coordinates so Ops Analyst can check nearby area
            lat = flight.get("latitude")
            lon = flight.get("longitude")
            payload = {"task": "check_nearby_anomalies", "latitude": lat, "longitude": lon, "radius_km": 50}
            ops_response = self.registry.call_agent("ops_analyst", payload)
            if not ops_response:
                return "I asked the Ops Analyst to check nearby flights but did not get a response."
            # ops_response expected to be dict with 'nearby_alerts' and 'summary'
            alerts = ops_response.get("nearby_alerts", [])
            if not alerts:
                return "No nearby alerts found within the requested radius."
            text_lines = [f"Found {len(alerts)} nearby alert(s):"]
            for a in alerts:
                text_lines.append(f"- {a.get('callsign') or a.get('icao24')}: {', '.join(a.get('anomalies', []))}")
            text_lines.append("\nOps summary: " + ops_response.get("summary", "No summary provided."))
            return "\n".join(text_lines)

        # default fallback: provide formatted summary + hint
        return self._format_flight_summary(flight) + " (If you want to check nearby problems, ask: 'Are there any flights near mine with issues?')"

# convenience instance for simple imports
traveler_agent = TravelerSupportAgent()
