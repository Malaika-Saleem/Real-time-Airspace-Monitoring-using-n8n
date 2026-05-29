"""
Utility script to test and validate the data format from n8n.
This helps ensure the MCP server can properly read the flight data.
"""

import json
from pathlib import Path
from server.db import load_flights_for_region, get_flight_by_identifier, load_alerts

def test_region_loading():
    """Test loading flights for a region."""
    print("=" * 60)
    print("Testing Region Data Loading")
    print("=" * 60)
    
    region = "region1"
    data = load_flights_for_region(region)
    
    print(f"\nRegion: {data.get('region', 'N/A')}")
    print(f"Last Updated: {data.get('last_updated', 'N/A')}")
    print(f"Flight Count: {len(data.get('flights', []))}")
    
    if data.get('flights'):
        print("\nFirst flight sample:")
        flight = data['flights'][0]
        print(f"  ICAO24: {flight.get('icao24')}")
        print(f"  Callsign: {flight.get('callsign')}")
        print(f"  Location: lat={flight.get('latitude')}, lon={flight.get('longitude')}")
        print(f"  Altitude: {flight.get('geo_altitude') or flight.get('baro_altitude')} m")
        print(f"  Speed: {flight.get('velocity_mps')} m/s")
        print(f"  On Ground: {flight.get('on_ground')}")
    
    return data

def test_flight_lookup():
    """Test looking up a specific flight."""
    print("\n" + "=" * 60)
    print("Testing Flight Lookup")
    print("=" * 60)
    
    # Try to find a flight from the data
    region_data = load_flights_for_region("region1")
    flights = region_data.get('flights', [])
    
    if flights:
        # Test with first flight's callsign
        test_callsign = flights[0].get('callsign')
        test_icao24 = flights[0].get('icao24')
        
        if test_callsign:
            print(f"\nLooking up flight by callsign: {test_callsign}")
            flight = get_flight_by_identifier(test_callsign)
            if flight:
                print(f"  Found: {flight.get('callsign')} ({flight.get('icao24')})")
            else:
                print("  Not found")
        
        print(f"\nLooking up flight by ICAO24: {test_icao24}")
        flight = get_flight_by_identifier(test_icao24)
        if flight:
            print(f"  Found: {flight.get('callsign')} ({flight.get('icao24')})")
        else:
            print("  Not found")
    else:
        print("\nNo flights available for testing")

def test_alerts():
    """Test loading alerts."""
    print("\n" + "=" * 60)
    print("Testing Alerts Loading")
    print("=" * 60)
    
    alerts = load_alerts()
    print(f"\nActive Alerts: {len(alerts)}")
    
    if alerts:
        print("\nFirst alert sample:")
        alert = alerts[0]
        for key, value in alert.items():
            print(f"  {key}: {value}")

def validate_flight_structure(flight):
    """Validate that a flight has all expected fields."""
    required_fields = ['icao24', 'latitude', 'longitude']
    optional_fields = ['callsign', 'velocity_mps', 'geo_altitude', 'baro_altitude', 
                      'vertical_rate_mps', 'on_ground', 'true_track_deg']
    
    missing_required = [f for f in required_fields if f not in flight or flight[f] is None]
    
    if missing_required:
        return False, f"Missing required fields: {missing_required}"
    
    return True, "Valid"

def test_data_validation():
    """Validate the structure of flight data."""
    print("\n" + "=" * 60)
    print("Testing Data Validation")
    print("=" * 60)
    
    region_data = load_flights_for_region("region1")
    flights = region_data.get('flights', [])
    
    if not flights:
        print("\nNo flights to validate")
        return
    
    print(f"\nValidating {len(flights)} flights...")
    valid_count = 0
    invalid_count = 0
    
    for i, flight in enumerate(flights[:10]):  # Check first 10
        is_valid, message = validate_flight_structure(flight)
        if is_valid:
            valid_count += 1
        else:
            invalid_count += 1
            print(f"  Flight {i+1} ({flight.get('callsign', flight.get('icao24'))}): {message}")
    
    print(f"\nValidation Results:")
    print(f"  Valid: {valid_count}")
    print(f"  Invalid: {invalid_count}")
    print(f"  (Checked first 10 flights)")

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Airspace Copilot - Data Format Test Utility")
    print("=" * 60)
    
    try:
        # Test region loading
        test_region_loading()
        
        # Test flight lookup
        test_flight_lookup()
        
        # Test alerts
        test_alerts()
        
        # Validate data structure
        test_data_validation()
        
        print("\n" + "=" * 60)
        print("All tests completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nError during testing: {e}")
        import traceback
        traceback.print_exc()

