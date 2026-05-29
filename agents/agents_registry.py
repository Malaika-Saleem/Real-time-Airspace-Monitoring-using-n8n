# agents/agent_registry.py
"""
Simple in-process registry that supports A2A calls.
The registry knows about both agents and can call ops_analyst methods directly.
This simulates A2A calling without an external orchestrator.
"""

from typing import Any, Dict, Optional
from .ops_analyst_agent import ops_analyst

class AgentRegistry:
    def __init__(self):
        # map agent_name -> callable handler
        self._agents = {
            "ops_analyst": ops_analyst
        }

    def call_agent(self, agent_name: str, payload: Dict[str, Any]) -> Any:
        """
        A2A call.
        payload defines 'task' (string) and other fields.
        
        Args:
            agent_name: Name of the agent to call ("ops_analyst")
            payload: Dictionary with 'task' and other parameters
        
        Returns:
            Response from the agent or error dict
        """
        agent = self._agents.get(agent_name)
        if not agent:
            return {"error": f"Unknown agent '{agent_name}'"}

        task = payload.get("task")
        if task == "check_nearby_anomalies":
            lat = payload.get("latitude")
            lon = payload.get("longitude")
            radius_km = payload.get("radius_km", 50.0)
            if lat is None or lon is None:
                return {"error": "latitude and longitude required for check_nearby_anomalies"}
            return agent.check_nearby(lat, lon, radius_km)
        elif task == "summarize_region":
            region = payload.get("region", "region1")
            return agent.summarize_region(region)
        else:
            return {"error": f"Unknown task: {task}"}
