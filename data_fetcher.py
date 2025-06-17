import logging
import pyotp
import yaml
import pandas as pd
from datetime import datetime, timedelta
from api_helper import ShoonyaApiPy, api # Import the global 'api' instance from api_helper

# Configure logging for data_fetcher.py
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load credentials from cred.yml once when the module is loaded
try:
    with open('cred.yml') as f:
        cred = yaml.load(f, Loader=yaml.FullLoader)
except FileNotFoundError:
    logging.critical("cred.yml not found. Please create it with your API credentials. Exiting.")
    # Exit or raise a more specific error if credentials are critical and not found
    raise FileNotFoundError("cred.yml not found.")
except yaml.YAMLError as e:
    logging.critical(f"Error parsing cred.yml: {e}. Exiting.")
    raise yaml.YAMLError(f"Error parsing cred.yml: {e}")

def initialize_shoonya_api():
    """
    Initializes the ShoonyaApiPy client and performs login.
    This function should be called initially and for re-authentication.
    It updates the global 'api' instance from api_helper.py.
    Raises an exception if login fails.
    """
    global api # Access the global 'api' from api_helper
    token = cred.get('token')
    user = cred.get('user')
    pwd = cred.get('pwd')
    
    if not all([token, user, pwd, cred.get('vc'), cred.get('apikey'), cred.get('imei')]):
        raise ValueError("Missing one or more Shoonya API credentials in cred.yml.")

    # Generate OTP using pyotp
    factor2 = pyotp.TOTP(token).now() 
    vc = cred.get('vc')
    app_key = cred.get('apikey')
    imei = cred.get('imei')

    # Create a new ShoonyaApiPy instance and attempt login
    new_api_instance = ShoonyaApiPy()
    try:
        new_api_instance.login(userid=user, password=pwd, twoFA=factor2, vendor_code=vc, api_secret=app_key, imei=imei)
        logging.info("Shoonya API Login Successful!")
        api = new_api_instance # Update the global api instance after successful login
    except Exception as e:
        logging.error(f"Shoonya API Login Failed during initialization: {e}")
        # It's critical if login fails, so re-raise to indicate a problem to app.py
        raise 

def fetch_data(retry_count=0, max_retries=1):
    """
    Fetches real-time and historical market data for NSE, BSE, and VIX
    using the global authenticated Shoonya API instance.
    Includes logic to re-authenticate and retry on failure.
    """
    global api # Ensure we're using the global api instance

    # Removed the explicit api.is_logged_in() check.
    # The try-except block around the API calls will now handle authentication issues.

    nse_exchange = "NSE"
    nse_token = "26000" 
    bse_exchange = "BSE"
    bse_token = "1"     
    vix_token = "26017" 
    days = 1            
    interval = "1"      

    def get_time_series(exchange, token, days, interval):
        """Helper function to fetch time series (historical) data."""
        now = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        prev_day_timestamp = (now - timedelta(days=days)).timestamp()
        
        return api.get_time_price_series(exchange=exchange, token=token, starttime=prev_day_timestamp, interval=interval)
    
    def process_df(df):
        """Helper function to process historical data DataFrame."""
        df = df.sort_index(ascending=False)
        df[['intl', 'inth']] = df[['intl', 'inth']].apply(pd.to_numeric, errors='coerce')
        return df
    
    # Initialize previous day close (pdc) to 0.0
    nse_pdc = 0.0
    bse_pdc = 0.0

    # Initialize all result variables with "N/A" to ensure they always have a value
    nse_ltp, nse_pdh, nse_pdl, nse_cdh, nse_cdl, nse_hh, nse_ll, nse_ill, nse_ihh, nse_c2c = ["N/A"] * 10
    bse_ltp, bse_pdh, bse_pdl, bse_cdh, bse_cdl, bse_hh, bse_ll, bse_ill, bse_ihh, bse_c2c = ["N/A"] * 10
    vix = "N/A"

    try:
        # Check if api is None *before* making any calls that would use it
        # This initial check remains important for when the app first starts and API might not be ready
        if api is None:
            raise Exception("API instance is None. Attempting initial authentication.")

        # Fetch historical data for NSE and BSE
        nse_df_raw = api.get_time_price_series(exchange=nse_exchange, token=nse_token, 
                                                starttime=(datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=days)).timestamp(), 
                                                interval=interval)
        bse_df_raw = api.get_time_price_series(exchange=bse_exchange, token=bse_token, 
                                                starttime=(datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=days)).timestamp(), 
                                                interval=interval)

        nse_df = pd.DataFrame(nse_df_raw) if nse_df_raw else None
        bse_df = pd.DataFrame(bse_df_raw) if bse_df_raw else None

        # Process NSE historical data
        if nse_df is None or nse_df.empty:
            logging.warning("NSE historical data is empty or None.")
        else:
            nse_df['time'] = pd.to_datetime(nse_df['time'], format='%d-%m-%Y %H:%M:%S')
            nse_pdc = float(nse_df.sort_values(by='time', ascending=False).iloc[0]['intc'])
            nse_df = process_df(nse_df)

        # Process BSE historical data
        if bse_df is None or bse_df.empty:
            logging.warning("BSE historical data is empty or None.")
        else:
            bse_df['time'] = pd.to_datetime(bse_df['time'], format='%d-%m-%Y %H:%M:%S')
            bse_pdc = float(bse_df.sort_values(by='time', ascending=False).iloc[0]['intc'])
            bse_df = process_df(bse_df)

        # Fetch real-time quotes for NSE, BSE, and VIX
        nse_resp = api.get_quotes(exchange=nse_exchange, token=nse_token)
        bse_resp = api.get_quotes(exchange=bse_exchange, token=bse_token)
        vix_resp = api.get_quotes(exchange=nse_exchange, token=vix_token)

        # Safely assign values from NSE real-time response
        if nse_resp:
            try:
                nse_ltp = round(float(nse_resp.get('lp', 0)), 2) 
                nse_cdh = round(float(nse_resp.get('h', nse_resp.get('c', 0))), 2) 
                nse_cdl = round(float(nse_resp.get('l', nse_resp.get('c', 0))), 2) 
                
                if nse_df is not None and not nse_df.empty:
                    nse_pdh = round(float(nse_df['inth'].max()), 2) 
                    nse_pdl = round(float(nse_df['intl'].min()), 2) 
                    nse_hh = round(nse_ltp - nse_pdl, 2) 
                    nse_ll = round(nse_pdh - nse_ltp, 2) 
                else:
                    nse_pdh, nse_pdl = "N/A", "N/A" 
                    nse_hh, nse_ll = "N/A", "N/A"
                
                nse_ill = round(nse_cdh - nse_ltp, 2) 
                nse_ihh = round(nse_ltp - nse_cdl, 2) 
                nse_c2c = round(nse_ltp - nse_pdc, 2) if nse_pdc != 0.0 else "N/A"
            except (ValueError, TypeError) as e:
                logging.error(f"Error processing NSE response: {e}")

        # Safely assign values from BSE real-time response
        if bse_resp:
            try:
                bse_ltp = round(float(bse_resp.get('lp', 0)), 2)
                bse_cdh = round(float(bse_resp.get('h', bse_resp.get('c', 0))), 2)
                bse_cdl = round(float(bse_resp.get('l', bse_resp.get('c', 0))), 2)
                
                if bse_df is not None and not bse_df.empty:
                    bse_pdh = round(float(bse_df['inth'].max()), 2)
                    bse_pdl = round(float(bse_df['intl'].min()), 2)
                    bse_hh = round(bse_ltp - bse_pdl, 2)
                    bse_ll = round(bse_pdh - bse_ltp, 2)
                else:
                    bse_pdh, bse_pdl = "N/A", "N/A"
                    bse_hh, bse_ll = "N/A", "N/A"
                
                bse_ill = round(bse_cdh - bse_ltp, 2)
                bse_ihh = round(bse_ltp - bse_cdl, 2)
                bse_c2c = round(bse_ltp - bse_pdc, 2) if bse_pdc != 0.0 else "N/A"
            except (ValueError, TypeError) as e:
                logging.error(f"Error processing BSE response: {e}")

        # Safely assign VIX value
        if vix_resp and 'lp' in vix_resp:
            try:
                vix = float(vix_resp['lp'])
            except (ValueError, TypeError) as e:
                logging.error(f"Error processing VIX response: {e}")

        # Return a dictionary of all fetched and calculated market data
        return {
            "nse_ltp": nse_ltp, "nse_pdh" : nse_pdh, "nse_pdl" : nse_pdl, "nse_cdh": nse_cdh, "nse_cdl": nse_cdl, "nse_hh": nse_hh, "nse_ll": nse_ll, "nse_ill": nse_ill, "nse_ihh": nse_ihh, "nse_c2c" : nse_c2c,
            "bse_ltp": bse_ltp, "bse_pdh" : bse_pdh, "bse_pdl" : bse_pdl, "bse_cdh": bse_cdh, "bse_cdl": bse_cdl, "bse_hh": bse_hh, "bse_ll": bse_ll, "bse_ill": bse_ill, "bse_ihh": bse_ihh, "bse_c2c" : bse_c2c,
            "vix": vix
        }
    except Exception as e:
        logging.error(f"An error occurred during data fetching: {e}. Attempting re-authentication and retry.")
        if retry_count < max_retries:
            try:
                initialize_shoonya_api() # Attempt to re-authenticate
                return fetch_data(retry_count + 1, max_retries) # Retry the fetch
            except Exception as reauth_e:
                logging.error(f"Re-authentication failed: {reauth_e}. Cannot fetch data.")
        else:
            logging.error(f"Max retries ({max_retries}) reached for data fetch. Returning N/A data.")
        
        # If all retries fail, return default N/A values
        return {
            "nse_ltp": "N/A", "nse_pdh": "N/A", "nse_pdl": "N/A", "nse_cdh": "N/A", "nse_cdl": "N/A", "nse_hh": "N/A", "nse_ll": "N/A", "nse_ill": "N/A", "nse_ihh": "N/A", "nse_c2c": "N/A",
            "bse_ltp": "N/A", "bse_pdh": "N/A", "bse_pdl": "N/A", "bse_cdh": "N/A", "bse_cdl": "N/A", "bse_hh": "N/A", "bse_ll": "N/A", "bse_ill": "N/A", "bse_ihh": "N/A", "bse_c2c": "N/A",
            "vix": "N/A"
        }
