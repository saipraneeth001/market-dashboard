from flask import Flask, render_template, jsonify
import json
import threading
import time
from data_fetcher import fetch_data # Assuming data_fetcher.py is in the same directory
from datetime import datetime

app = Flask(__name__)

# Global variable to store the fetched data
latest_data = {}
data_lock = threading.Lock() # To prevent race conditions when updating data

def update_data_periodically():
    """Fetches data every 30 seconds and updates the global variable."""
    global latest_data
    while True:
        try:
            new_data = fetch_data()
            with data_lock:
                latest_data = new_data
            print(f"Data fetched and updated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        except Exception as e:
            print(f"Error fetching data: {e}")
        time.sleep(30) # Fetch data every 30 seconds

# Start the data fetching in a separate thread when the app starts
data_thread = threading.Thread(target=update_data_periodically)
data_thread.daemon = True # Daemonize the thread so it exits when the main app exits
data_thread.start()

@app.route('/')
def index():
    """Renders the main dashboard page."""
    with data_lock:
        data_for_template = latest_data.copy() # Get a copy for rendering
    return render_template('index.html', data=data_for_template)

@app.route('/api/data')
def get_current_all_data():
    """API endpoint to get the latest ALL data as JSON."""
    with data_lock:
        return jsonify(latest_data)

@app.route('/api/nse_data')
def get_nse_data():
    """API endpoint to get only NSE related data and VIX as JSON."""
    with data_lock:
        nse_only_data = {
            key: value for key, value in latest_data.items() if key.startswith('nse_')
        }
        # Add VIX to NSE data as requested
        if 'vix' in latest_data:
            nse_only_data['vix'] = latest_data['vix']
        return jsonify(nse_only_data)

@app.route('/api/bse_data')
def get_bse_data():
    """API endpoint to get only BSE related data as JSON."""
    with data_lock:
        bse_only_data = {
            key: value for key, value in latest_data.items() if key.startswith('bse_')
        }
        return jsonify(bse_only_data)


if __name__ == '__main__':
    # Initial data fetch before starting the server
    try:
        latest_data = fetch_data()
        print("Initial data fetched successfully.")
    except Exception as e:
        print(f"Error during initial data fetch: {e}")
        latest_data = {} # Initialize empty if initial fetch fails

    app.run(debug=True) # debug=True allows for auto-reloading during development