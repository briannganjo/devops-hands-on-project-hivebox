from flask import Flask, jsonify
from hivebox.opensensemap import get_average_temperature_c

# Application Version (v0.0.1 required for Phase 3)
APP_VERSION = "v0.0.1" 

app = Flask(__name__)

@app.route('/version', methods=['GET'])
def get_version():
    """
    API endpoint that returns the application version.
    """
    return jsonify({
        "version": APP_VERSION
    })

@app.route('/temperature', methods=['GET'])
def get_temperature():
    """
    API endpoint that returns the average fresh temperature in Celsius.
    """
    # Call the logic implemented in opensensemap.py
    average_temp = get_average_temperature_c()

    if average_temp is None:
        # If no fresh data is found, return a 503 Service Unavailable or a 200 with an informative message
        return jsonify({
            "status": "error",
            "message": "No fresh temperature measurements (newer than 1 hour) were found from the senseBoxes."
        }), 503
    
    return jsonify({
        "status": "ok",
        "average_temperature_c": average_temp
    })

# If you run the app directly (e.g., 'python -m hivebox.app')
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
