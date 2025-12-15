import pytest
import json
from hivebox.app import app, APP_VERSION
from hivebox.opensensemap import SENSEBOX_IDS, FRESH_WINDOW_SECONDS
from unittest.mock import patch, Mock
from datetime import datetime, timezone, timedelta

# Use the Flask test client for API calls
@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

# --- Mock Data Setup ---

# Define a function to generate a mock openSenseMap response structure
def generate_mock_response(temp_c, seconds_ago):
    """Generates a mock openSenseMap API response with a specific temperature and age."""
    # Calculate the past timestamp for the measurement
    past_time = datetime.now(timezone.utc) - timedelta(seconds=seconds_ago)
    created_at_str = past_time.isoformat().replace('+00:00', 'Z')
    
    return {
        "_id": "mockBoxId", 
        "sensors": [
            {
                "title": "Temperatur",
                "lastMeasurement": {
                    "value": str(temp_c),
                    "createdAt": created_at_str
                }
            },
            # Include another sensor to mimic the real response structure
            {"title": "rel. Luftfeuchte", "lastMeasurement": {"value": "50.0", "createdAt": created_at_str}}
        ]
    }

# --- Unit Tests ---

def test_version_endpoint_success(client):
    """Tests the /version endpoint returns the correct version number."""
    response = client.get('/version')
    data = json.loads(response.data)
    
    assert response.status_code == 200
    assert data['version'] == APP_VERSION
    # In Phase 3, this should specifically be "v0.0.1"
    assert data['version'] == "v0.0.1" 

@patch('requests.get')
def test_temperature_endpoint_average_calculation(mock_get, client):
    """Tests the /temperature endpoint correctly averages fresh data."""
    
    # 1. Setup Mock Responses: 2 fresh, 1 stale
    # Box 1: Fresh (10 minutes old) at 15.0°C
    mock_1 = Mock()
    mock_1.json.return_value = generate_mock_response(15.0, 600) 
    
    # Box 2: Fresh (30 minutes old) at 25.0°C
    mock_2 = Mock()
    mock_2.json.return_value = generate_mock_response(25.0, 1800)
    
    # Box 3: Stale (70 minutes old, > 60 minutes cutoff) at 100.0°C - SHOULD BE IGNORED
    mock_3 = Mock()
    mock_3.json.return_value = generate_mock_response(100.0, 4200) # 4200 seconds is 70 minutes

    # Make requests.get return the mocks sequentially for the 3 SENSEBOX_IDS
    mock_get.side_effect = [mock_1, mock_2, mock_3]
    
    # 2. Run the test
    response = client.get('/temperature')
    data = json.loads(response.data)
    
    # 3. Assertions
    assert response.status_code == 200
    assert data['status'] == 'ok'
    
    # Expected average: (15.0 + 25.0) / 2 fresh measurements = 20.0
    assert data['average_temperature_c'] == 20.0
    
    # Ensure the API was called once for each of the 3 senseBox IDs
    assert mock_get.call_count == len(SENSEBOX_IDS)

@patch('requests.get')
def test_temperature_endpoint_no_fresh_data(mock_get, client):
    """Tests /temperature returns a 503 error if all data is stale."""
    
    # Setup Mock Responses: All data is stale (70 minutes old)
    mock_stale = Mock()
    mock_stale.json.return_value = generate_mock_response(10.0, 4200)
    
    # Make requests.get return the stale mock for all 3 SENSEBOX_IDS
    mock_get.side_effect = [mock_stale] * len(SENSEBOX_IDS)
    
    # Run the test
    response = client.get('/temperature')
    
    # Assertions: Should be a 503 Service Unavailable
    assert response.status_code == 503
    data = json.loads(response.data)
    assert data['status'] == 'error'
    assert 'No fresh temperature measurements' in data['message']
