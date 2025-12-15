import requests
from datetime import datetime, timezone
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Base URL for the openSenseMap API
BASE_URL = "https://api.opensensemap.org/boxes/"

# IDs of the senseBoxes to monitor
SENSEBOX_IDS = [
    "5eba5fbad46fb8001b799786",
    "5c21ff8f919bf8001adf2488",
    "5ade1acf223bd80019a1011c"
]

# The phenomenon title we are looking for (Temperature)
PHENOMENON_TITLE = "Temperatur"

# Time window for fresh data (1 hour in seconds)
FRESH_WINDOW_SECONDS = 3600

def get_average_temperature_c():
    """
    Fetches the latest temperature measurements from configured senseBoxes,
    filters for measurements newer than 1 hour, and calculates the average.
    """
    fresh_temperatures = []
    
    # Calculate the cutoff time (1 hour ago, in UTC)
    cutoff_time = datetime.now(timezone.utc) - timedelta(seconds=FRESH_WINDOW_SECONDS)

    for box_id in SENSEBOX_IDS:
        url = f"{BASE_URL}{box_id}"
        
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status() # Raises an HTTPError for bad responses (4xx or 5xx)
            data = response.json()

            # The sensor data is in the 'sensors' array
            for sensor in data.get('sensors', []):
                if sensor.get('title') == PHENOMENON_TITLE:
                    measurement = sensor.get('lastMeasurement')
                    
                    if measurement and measurement.get('value') is not None:
                        # Parse the RFC 3339 timestamp
                        created_at_str = measurement.get('createdAt')
                        
                        try:
                            # Python 3.11+ can handle the 'Z' automatically. 
                            # For wider compatibility, we replace 'Z' and ensure UTC timezone.
                            created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00')).astimezone(timezone.utc)
                        except ValueError:
                            logger.warning(f"Invalid timestamp format for box {box_id}: {created_at_str}")
                            continue
                            
                        # 2. Check for freshness (newer than 1 hour)
                        if created_at > cutoff_time:
                            try:
                                temp_value = float(measurement['value'])
                                fresh_temperatures.append(temp_value)
                            except ValueError:
                                logger.warning(f"Non-numeric temperature value for box {box_id}")
                                
                    break # Move to the next box once the Temperature sensor is found
                    
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed for box {box_id}: {e}")
            continue

    # 3. Calculate the average
    if not fresh_temperatures:
        # Return None or raise an error if no fresh data is found
        return None 
    
    average_temp = sum(fresh_temperatures) / len(fresh_temperatures)
    # Return rounded average to one decimal place, matching common temperature displays
    return round(average_temp, 1)

if __name__ == '__main__':
    # Simple test run (you can delete this block later)
    from datetime import timedelta
    avg = get_average_temperature_c()
    print(f"Average fresh temperature: {avg}°C")
