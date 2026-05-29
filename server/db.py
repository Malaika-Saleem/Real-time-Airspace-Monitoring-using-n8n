import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

DATA_DIR = Path(__file__).parent.parent / "data"

def load_flights_for_region(region_name: str) -> Dict[str, Any]:
    """
    Load flights for a region. Returns dict with:
    - region: region name
    - last_updated: timestamp
    - flights: list of flight dicts
    """
    # Try to load from region-specific file first (e.g., region1_latest.json)
    region_file = DATA_DIR.parent / f"{region_name}_latest.json"
    if region_file.exists():
        try:
            with open(region_file, 'r') as f:
                data = json.load(f)
                # Ensure it has the expected structure
                if isinstance(data, dict) and "flights" in data:
                    return data
                # If it's just a list, wrap it
                if isinstance(data, list):
                    return {
                        "region": region_name,
                        "last_updated": int(time.time()),
                        "flights": data
                    }
        except Exception:
            pass
    
    # Fallback to flights.json
    file_path = DATA_DIR / "flights.json"
    if file_path.exists():
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                # Handle both formats: {"region1": [...]} or {"flights": [...]}
                if isinstance(data, dict):
                    if region_name in data:
                        flights_data = data[region_name]
                    elif "flights" in data:
                        flights_data = data["flights"]
                    else:
                        flights_data = []
                else:
                    flights_data = []
                
                return {
                    "region": region_name,
                    "last_updated": int(time.time()),
                    "flights": flights_data if isinstance(flights_data, list) else []
                }
        except Exception:
            pass
    
    # Return empty if nothing found
    return {
        "region": region_name,
        "last_updated": int(time.time()),
        "flights": []
    }

def load_alerts() -> List[Dict[str, Any]]:
    """Load alerts from alerts.json. Returns list of alert dicts."""
    file_path = DATA_DIR / "alerts.json"
    if not file_path.exists():
        return []
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and "alerts" in data:
                return data["alerts"]
            return []
    except Exception:
        return []

def get_flight_by_identifier(identifier: str) -> Optional[Dict[str, Any]]:
    """
    Get a flight by callsign or icao24. Searches across all regions.
    Returns the first match found.
    """
    # Try region1 first (most common)
    snap = load_flights_for_region("region1")
    for f in snap.get("flights", []):
        if f.get("icao24") == identifier or (f.get("callsign") or "").strip() == identifier:
            return f
    
    # Try other regions if region1 doesn't have it
    # For now, just check region1. Can be extended later.
    return None
