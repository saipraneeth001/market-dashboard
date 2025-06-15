from flask import Flask, render_template, jsonify
import threading
import time
# Import fetch_data and initialize_shoonya_api directly from data_fetcher
from data_fetcher import fetch_data, initialize_shoonya_api 
from datetime import datetime, time as dt_time, timedelta
import pytz 
import logging

# Configure logging for app.py
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

# Global variable to store the fetched data
latest_data = {}
# Lock to prevent race conditions when updating and reading data simultaneously
data_lock = threading.Lock() 

# Define IST timezone for market hours calculation
IST = pytz.timezone('Asia/Kolkata')

def is_market_hours():
    """
    Checks if the current time is within market hours (9:15 AM - 3:30 PM IST, Mon-Fri).
    Note: Market timings are typically 9:15 AM to 3:30 PM IST for equity.
    """
    now_ist = datetime.now(IST)
    
    # Define market open and close times (adjusted to common Indian market hours)
    market_open_time = dt_time(9, 15, 0)  # 9:15:00 AM IST
    market_close_time = dt_time(15, 30, 0) # 3:30:00 PM IST

    # Check if it's a weekday (Monday=0, Friday=4)
    is_weekday = now_ist.weekday() >= 0 and now_ist.weekday() <= 4 

    # Check if current time is within the defined market hours
    is_within_time_range = market_open_time <= now_ist.time() <= market_close_time

    return is_weekday and is_within_time_range


def update_data_periodically():
    """
    Fetches data every 30 seconds if within market hours, otherwise every 5 minutes.
    This function runs in a separate thread to continuously update `latest_data`.
    It now relies on data_fetcher to manage its own API instance and re-authentication.
    """
    global latest_data
    while True:
        if is_market_hours():
            try:
                # fetch_data internally handles re-authentication if necessary
                new_data = fetch_data() 
                with data_lock:
                    latest_data = new_data
                logging.info(f"Data fetched and updated at {datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S %Z%z')} (Market Hours)")
            except Exception as e:
                # This catches errors that fetch_data might still raise (e.g., persistent auth failure)
                logging.error(f"Critical error fetching data in background thread, possibly API issue: {e}")
                # Optionally, set latest_data to an error state or empty
                with data_lock:
                    latest_data = {"error": "Failed to fetch data"} 
            time.sleep(30) 
        else:
            logging.info(f"Outside market hours. Next data fetch check in 5 minutes at {datetime.now(IST) + timedelta(minutes=5)}. Current time: {datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S %Z%z')}")
            time.sleep(300) 

@app.route('/')
def index():
    """Renders the main HTML page for the dashboard."""
    return render_template('index.html')

@app.route('/api/data')
def get_current_all_data():
    """
    API endpoint to serve all available market data.
    It returns the data that was last fetched by the background thread.
    """
    with data_lock:
        return jsonify(latest_data)

@app.route('/api/nse_data')
def get_nse_data():
    """
    API endpoint to serve only NSE data and VIX.
    Filters the global latest_data for NSE-specific entries.
    """
    with data_lock:
        nse_only_data = {
            key: value for key, value in latest_data.items() if key.startswith('nse_')
        }
        if 'vix' in latest_data:
            nse_only_data['vix'] = latest_data['vix']
        return jsonify(nse_only_data)

@app.route('/api/bse_data')
def get_bse_data():
    """
    API endpoint to serve only BSE data.
    Filters the global latest_data for BSE-specific entries.
    """
    with data_lock:
        bse_only_data = {
            key: value for key, value in latest_data.items() if key.startswith('bse_')
        }
        return jsonify(bse_only_data)

if __name__ == '__main__':
    # Perform initial API authentication once at startup.
    # This sets up the global 'api' instance in data_fetcher.py.
    try:
        initialize_shoonya_api()
        logging.info("Shoonya API initialized successfully at application start.")
    except Exception as e:
        logging.critical(f"Failed to initialize Shoonya API at startup: {e}. Dashboard will not function.")
        # Exit if initial API setup fails, as data fetching won't work
        exit(1) 

    # Perform an initial data fetch to populate 'latest_data' before serving requests.
    try:
        with data_lock:
            latest_data = fetch_data() # No argument needed now
        logging.info("Initial data fetched successfully on startup.")
    except Exception as e:
        logging.error(f"Error during initial data fetch: {e}. Dashboard may show N/A initially.")
        latest_data = {} # Initialize empty if initial fetch fails

    # Start the data fetching in a separate thread.
    # It now relies on data_fetcher to manage its own API instance.
    data_thread = threading.Thread(target=update_data_periodically)
    data_thread.daemon = True
    data_thread.start()
    
    # Run the Flask application.
    # use_reloader=False is important to prevent the Flask reloader from
    # starting the background thread twice in development mode.
    app.run(debug=True, use_reloader=False) 
