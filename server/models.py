from pydantic import BaseModel
from typing import Optional

class Flight(BaseModel):
    icao24: str
    callsign: str
    origin_country: str
    time_position: int
    last_contact: int
    longitude: float
    latitude: float
    baro_altitude: Optional[float]
    on_ground: bool
    velocity_mps: float
    true_track_deg: float
    vertical_rate_mps: Optional[float]
    geo_altitude: Optional[float]
    squawk: Optional[str]
    spi: bool
    position_source: int

class Alert(BaseModel):
    flight_callsign: str
    issue: str
    time_detected: int

class Snapshot(BaseModel):
    region_name: str
    flights: list[Flight]
