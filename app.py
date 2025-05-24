from flask import Flask, render_template, jsonify
import json
import threading
import time
from data_fetcher import fetch_data
from datetime import datetime, time as dt_time, timedelta
import pytz # Import pytz

app = Flask(__name__)

# Global variable to store the fetched data
latest_data = {}
data_lock = threading.Lock() # To prevent race conditions when updating data

# Define IST timezone
IST = pytz.timezone('Asia/Kolkata')

def is_market_hours():
    """
    Checks if the current time is within market hours (9 AM - 4 PM IST, Mon-Fri).
    """
    now_ist = datetime.now(IST)
    
    # Define market open and close times
    market_open_time = dt_time(9, 0, 0)  # 9:00:00 AM IST
    market_close_time = dt_time(16, 0, 0) # 4:00:00 PM IST

    # Check if it's a weekday (Monday=0, Friday=4)
    is_weekday = now_ist.weekday() >= 0 and now_ist.weekday() <= 4 # 0 for Mon, 4 for Fri

    # Check if current time is within market hours
    is_within_time_range = market_open_time <= now_ist.time() <= market_close_time

    # For debugging purposes, you can uncomment this
    # print(f"Current IST time: {now_ist.strftime('%Y-%m-%d %H:%M:%S %Z%z')}")
    # print(f"Is weekday: {is_weekday}, Is within time range: {is_within_time_range}")

    return is_weekday and is_within_time_range


def update_data_periodically():
    """Fetches data every 30 seconds if within market hours, otherwise every 5 minutes."""
    global latest_data
    while True:
        if is_market_hours():
            try:
                new_data = fetch_data()
                with data_lock:
                    latest_data = new_data
                print(f"Data fetched and updated at {datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S %Z%z')} (Market Hours)")
            except Exception as e:
                print(f"Error fetching data: {e}")
            time.sleep(30) # Fetch every 30 seconds during market hours
        else:
            print(f"Outside market hours. Next check in 5 minutes at {datetime.now(IST) + timedelta(minutes=5)}. Current time: {datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S %Z%z')}")
            time.sleep(300) # Check every 5 minutes outside market hours to save resources

# Start the data fetching in a separate thread when the app starts
data_thread = threading.Thread(target=update_data_periodically)
data_thread.daemon = True
data_thread.start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/data')
def get_current_all_data():
    with data_lock:
        return jsonify(latest_data)

@app.route('/api/nse_data')
def get_nse_data():
    with data_lock:
        nse_only_data = {
            key: value for key, value in latest_data.items() if key.startswith('nse_')
        }
        if 'vix' in latest_data:
            nse_only_data['vix'] = latest_data['vix']
        return jsonify(nse_only_data)

@app.route('/api/bse_data')
def get_bse_data():
    with data_lock:
        bse_only_data = {
            key: value for key, value in latest_data.items() if key.startswith('bse_')
        }
        return jsonify(bse_only_data)

if __name__ == '__main__':
    # Initial data fetch when the app starts, regardless of market hours,
    # so the dashboard isn't completely empty on startup.
    # The periodic updates will then adhere to market hours.
    try:
        latest_data = fetch_data()
        print("Initial data fetched successfully on startup.")
    except Exception as e:
        print(f"Error during initial data fetch: {e}")
        latest_data = {} # Initialize empty if initial fetch fails

    app.run(debug=True)