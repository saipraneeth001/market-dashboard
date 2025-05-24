import logging
import pyotp
import yaml
import pandas as pd
from datetime import datetime, timedelta
from api_helper import ShoonyaApiPy

with open('cred.yml') as f:
    cred = yaml.load(f, Loader=yaml.FullLoader)

def fetch_data():
    token = cred['token']
    user = cred['user']
    pwd = cred['pwd']
    factor2 = pyotp.TOTP(token).now()
    vc = cred['vc']
    app_key = cred['apikey']
    imei = cred['imei']

    nse_exchange = "NSE"
    nse_token = "26000"
    bse_exchange = "BSE"
    bse_token = "1"
    vix_token = "26017"
    days = 1
    interval = "1"

    api = ShoonyaApiPy()
    api.login(userid=user, password=pwd, twoFA=factor2, vendor_code=vc, api_secret=app_key, imei=imei)
    print("Login Successful!")

    def get_time_series(exchange, token, days, interval):
        now = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        prev_day = now - timedelta(days=days)
        ret = api.get_time_price_series(exchange=exchange, token=token, starttime=prev_day.timestamp(), interval=interval)
        return pd.DataFrame(ret) if ret else None
    
    def process_df(df):
        df = df.sort_index(ascending=False)
        df[['intl', 'inth']] = df[['intl', 'inth']].apply(pd.to_numeric)
        return df
    
    nse_df = get_time_series(nse_exchange, nse_token, days, interval)
    bse_df = get_time_series(bse_exchange, bse_token, days, interval)

    nse_df['time'] = pd.to_datetime(nse_df['time'], format='%d-%m-%Y %H:%M:%S')
    nse_pdc = float(nse_df.sort_values(by='time', ascending=False).iloc[0]['intc'])

    bse_df['time'] = pd.to_datetime(bse_df['time'], format='%d-%m-%Y %H:%M:%S')
    bse_pdc = float(bse_df.sort_values(by='time', ascending=False).iloc[0]['intc'])

    nse_df = process_df(nse_df)
    bse_df = process_df(bse_df)

    nse_resp = api.get_quotes(exchange=nse_exchange, token=nse_token)
    bse_resp = api.get_quotes(exchange=bse_exchange, token=bse_token)
    vix_resp = api.get_quotes(exchange=nse_exchange, token=vix_token)

    nse_ltp = round(float(nse_resp['lp']),2)
    nse_pdh = round(float(nse_df['inth'].max()),2)
    nse_pdl = round(float(nse_df['intl'].min()),2)
    nse_pdc = round(nse_pdc,2)
    nse_cdh = round(float(nse_resp.get('h', nse_resp['c'])),2)
    nse_cdl = round(float(nse_resp.get('l', nse_resp['c'])),2)
    nse_hh = round(nse_ltp - nse_pdl,2)
    nse_ll = round(nse_pdh - nse_ltp,2)
    nse_ill = round(nse_cdh - nse_ltp,2)
    nse_ihh = round(nse_ltp - nse_cdl,2)
    nse_c2c = nse_ltp - nse_pdc
    

    bse_ltp = round(float(bse_resp['lp']),2)
    bse_pdh = round(float(bse_df['inth'].max()),2)
    bse_pdl = round(float(bse_df['intl'].min()),2)
    bse_pdc = round(bse_pdc,2)
    bse_cdh = round(float(bse_resp.get('h', bse_resp['c'])),2)
    bse_cdl = round(float(bse_resp.get('l', bse_resp['c'])),2)
    bse_hh = round(bse_ltp - bse_pdl,2)
    bse_ll = round(bse_pdh - bse_ltp,2)
    bse_ill = round(bse_cdh - bse_ltp,2)
    bse_ihh = round(bse_ltp - bse_cdl,2)
    bse_c2c = bse_ltp - bse_pdc


    vix = float(vix_resp['lp'])

    return {
        "nse_ltp": nse_ltp, "nse_pdh" : nse_pdh, "nse_pdl" : nse_pdl, "nse_cdh": nse_cdh, "nse_cdl": nse_cdl, "nse_hh": nse_hh, "nse_ll": nse_ll, "nse_ill": nse_ill, "nse_ihh": nse_ihh, "nse_c2c" : nse_c2c,
        "bse_ltp": bse_ltp, "bse_pdh" : bse_pdh, "bse_pdl" : bse_pdl, "bse_cdh": bse_cdh, "bse_cdl": bse_cdl, "bse_hh": bse_hh, "bse_ll": bse_ll, "bse_ill": bse_ill, "bse_ihh": bse_ihh, "bse_c2c" : bse_c2c,
        "vix": vix
    }
