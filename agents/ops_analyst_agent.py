# agents/ops_analyst_agent.py
"""
Ops Analyst Agent:
- Uses MCP tools to list flights in a region and compute anomalies
- Exposes a simple interface that can be called directly (A2A) via AgentRegistry
"""

from typing import Dict, Any, List, Optional
import requests
import os
import math
import time

MCP_BASE = os.getenv("MCP_BASE", "http://127.0.0.1:8000/mcp/tool")

class OpsAnalystAgent:
    def __init__(self, mcp_base: str = MCP_BASE):
        self.mcp_base = mcp_base

    def _call_tool_flights_list(self, region: str):
        url = f"{self.mcp_base}/flights.list?region={region}"
        try:
            r = requests.get(url, timeout=6)
            if r.status_code == 200:
                return r.json()
        except requests.RequestException:
            return None
        return None

    def _call_tool_alerts_list(self):
        url = f"{self.mcp_base}/alerts.list"
        try:
            r = requests.get(url, timeout=6)
            if r.status_code == 200:
                return r.json()
        except requests.RequestException:
            return []
        return []

    def _compute_anomalies_for_flight(self, f: Dict[str, Any]) -> List[str]:
        anomalies = []
        # use geo_altitude if present else baro_altitude
        altitude = f.get("geo_altitude") or f.get("baro_altitude") or 0
        velocity = f.get("velocity_mps") or 0
        vr = f.get("vertical_rate_mps") or 0

        # rule: low speed at high altitude
        if velocity < 50 and altitude > 5000:
            anomalies.append("Low speed at high altitude")

        # rule: very high vertical rate (rapid climb/descent)
        if abs(vr) > 20:
            anomalies.append(f"Rapid vertical rate ({vr:.1f} m/s)")

        # rule: unusually low altitude for cruising speed
        if altitude < 500 and velocity > 200:
            anomalies.append("Low altitude at high speed")

        return anomalies

    def summarize_region(self, region: str) -> Dict[str, Any]:
        """
        Summarize region: returns dict:
        { region, last_updated, total_flights, alerts: [...], summary_text }
        """
        snap = self._call_tool_flights_list(region)
        if not snap:
            return {"error": "Could not fetch region snapshot"}

        flights = snap.get("flights", [])
        total = len(flights)
        alerts = []
        # compute anomalies
        for f in flights:
            if f.get("on_ground"):
                continue
            anomalies = self._compute_anomalies_for_flight(f)
            if anomalies:
                alerts.append({
                    "icao24": f.get("icao24"),
                    "callsign": f.get("callsign"),
                    "anomalies": anomalies,
                    "latitude": f.get("latitude"),
                    "longitude": f.get("longitude")
                })

        # incorporate alerts.list active (MCP computed)
        mcp_alerts = self._call_tool_alerts_list() or []
        
        # Build simple natural-language summary
        headline = f"Region {region}: {total} flights; {len(alerts)} detected anomalies."
        top_alerts = alerts[:5]
        summary_lines = [headline]
        
        if top_alerts:
            summary_lines.append("\nTop anomalies:")
            for a in top_alerts:
                callsign = a.get("callsign") or a.get("icao24", "Unknown")
                summary_lines.append(f"- {callsign}: {', '.join(a.get('anomalies', []))}")
        
        if mcp_alerts:
            summary_lines.append(f"\nMCP alerts: {len(mcp_alerts)} active alerts from system.")
        
        summary_text = "\n".join(summary_lines)
        
        return {
            "region": region,
            "last_updated": snap.get("last_updated"),
            "total_flights": total,
            "alerts": alerts,
            "mcp_alerts": mcp_alerts,
            "summary_text": summary_text
        }
    
    def check_nearby(self, latitude: float, longitude: float, radius_km: float = 50.0) -> Dict[str, Any]:
        """
        Check for anomalies near a given location.
        Returns dict with nearby_alerts and summary.
        """
        snap = self._call_tool_flights_list("region1")  # Default to region1
        if not snap:
            return {"error": "Could not fetch region snapshot", "nearby_alerts": [], "summary": "No data available"}
        
        flights = snap.get("flights", [])
        nearby_alerts = []
        
        # Simple distance calculation (Haversine approximation for small distances)
        def distance_km(lat1, lon1, lat2, lon2):
            R = 6371  # Earth radius in km
            dlat = math.radians(lat2 - lat1)
            dlon = math.radians(lon2 - lon1)
            a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
            c = 2 * math.asin(math.sqrt(a))
            return R * c
        
        for f in flights:
            if f.get("on_ground"):
                continue
            
            f_lat = f.get("latitude")
            f_lon = f.get("longitude")
            
            if f_lat is None or f_lon is None:
                continue
            
            dist = distance_km(latitude, longitude, f_lat, f_lon)
            if dist <= radius_km:
                anomalies = self._compute_anomalies_for_flight(f)
                if anomalies:
                    nearby_alerts.append({
                        "icao24": f.get("icao24"),
                        "callsign": f.get("callsign"),
                        "anomalies": anomalies,
                        "latitude": f_lat,
                        "longitude": f_lon,
                        "distance_km": round(dist, 2)
                    })
        
        summary = f"Found {len(nearby_alerts)} anomaly(ies) within {radius_km} km of ({latitude:.4f}, {longitude:.4f})"
        
        return {
            "nearby_alerts": nearby_alerts,
            "summary": summary
        }

# Create a singleton instance for A2A calls
ops_analyst = OpsAnalystAgent()
