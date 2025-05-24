# Libraries
import os
import time
import json
import math
import requests
import logging
import pandas as pd
import numpy as np
from prettytable import PrettyTable

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(process)d - %(levelname)s - %(message)s',datefmt='%d-%b-%y %H:%M:%S')

# Logging Statements
# logger = logging.getLogger()
# logger.setLevel(logging.DEBUG)
# formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
# file_handler = logging.FileHandler('../logs/mylogs.log')
# file_handler.setLevel(logging.DEBUG)
# file_handler.setFormatter(formatter)
# logger.addHandler(file_handler)


# Method to get nearest strikes
# def round_nearest(x,num=50): return int(math.ceil(float(x)/num)*num)

def custom_round_to_nearest(x, num = 50):
    if x % 50 <= 25:
        return x - (x % num)
    else:
        return x + (num - (x % num))
    
def nearest_strike_bnf(x): return int(custom_round_to_nearest(x,100))
def nearest_strike_nf(x): return int(custom_round_to_nearest(x,50))

# Urls for fetching Data
url_oc      = "https://www.nseindia.com/option-chain"
url_bnf     = 'https://www.nseindia.com/api/option-chain-indices?symbol=BANKNIFTY'
url_nf      = 'https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY'
url_indices = "https://www.nseindia.com/api/allIndices"

# Headers
headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36',
            'accept-language': 'en,gu;q=0.9,hi;q=0.8',
            'accept-encoding': 'gzip, deflate, br'}

sess = requests.Session()
cookies = dict()

# Local methods
def set_cookie():
    request = sess.get(url_oc, headers=headers, timeout=5)
    cookies = dict(request.cookies)
    
def get_data(url):
    set_cookie()
    response = sess.get(url, headers=headers, timeout=5, cookies=cookies)
    if(response.status_code==401):
        set_cookie()
        response = sess.get(url_nf, headers=headers, timeout=5, cookies=cookies)
    if(response.status_code==200):
        return response.text
    return ""

def set_header():
    global bnf_ul
    global nf_ul
    global bnf_nearest
    global nf_nearest
    response_text = get_data(url_indices)
    data = json.loads(response_text)
    for index in data["data"]:
        if index["index"]=="NIFTY 50":
            nf_ul = index["last"]
            logging.debug(f"NIFTY LTP is : {nf_ul}")
        if index["index"]=="NIFTY BANK":
            bnf_ul = index["last"]
            logging.debug(f"NIFTY BANK LTP is : {bnf_ul}")
    logging.info('Fetched latest NIFTY and BANK NIFTY LTP')
    logging.info(f'LTP NIFTY - {nf_ul} and BANK NIFTY - {bnf_ul}')
    bnf_nearest=nearest_strike_bnf(bnf_ul)
    nf_nearest=nearest_strike_nf(nf_ul)


def fetch_options(num,step,nearest,url):
    """
    num : Num of OTM's for CALL and PUT
    step: window of difference between each ATM
    nearest : rounded LTP Price
    url: url of the Scrip
    """
    strike = nearest - (step*num)
    start_strike = nearest - (step*num)
    response_text = get_data(url)
    data = json.loads(response_text)
    currExpiryDate = data["records"]["expiryDates"][0]
    sam_list = []
    for item in data['records']['data']:
        if item["expiryDate"] == currExpiryDate:
            if item["strikePrice"] == strike and item["strikePrice"] <= start_strike+(step*num*2):
                flattened_entry = {
                    'expiryDate': item['expiryDate'],
                    'CE_strikePrice': item['CE']['strikePrice'],
                    'CE expiryDate': item['CE']['expiryDate'],
                    'PE_strikePrice': item['PE']['strikePrice'],
                    'PE expiryDate': item['PE']['expiryDate'],
                    'CE_IV': item['CE']['impliedVolatility'],
                    'CE_LTP' : item['CE']['lastPrice'],
                    'strikePrice': item['strikePrice'],
                    'PE_LTP' : item['PE']['lastPrice'],# Flatten the 'CE' sub-dictionary
                    'PE_IV' : item['PE']['impliedVolatility'],  # Flatten the 'PE' sub-dictionary
                }
                strike = strike + step
                sam_list.append(flattened_entry)
    return sam_list

def percent_diff(ce_ltp_value,pe_ltp_value):
    if ce_ltp_value > pe_ltp_value:
        return int(((ce_ltp_value - pe_ltp_value)/pe_ltp_value)*100), "C"
    elif ce_ltp_value < pe_ltp_value:
        return int((((pe_ltp_value - ce_ltp_value)/ce_ltp_value)*100)), "P"
    else:
        return 0, "EQ"
    
def calc_values_option(df,ATM,step):
    upper_strike = ATM + step
    lower_strike = ATM - step
    pe_ltp_value = df.loc[df['strikePrice'] == lower_strike, 'PE_LTP'].values[0]
    ce_ltp_value = df.loc[df['strikePrice'] == upper_strike, 'CE_LTP'].values[0]
    diff, h_value = percent_diff(pe_ltp_value,ce_ltp_value)
    pe_ltp_value = int(pe_ltp_value)
    ce_ltp_value = int(ce_ltp_value)
    return lower_strike, upper_strike, pe_ltp_value, ce_ltp_value, diff, h_value

def send_tg_message(TOKEN, chat_id, msg_type, msg_text):
    msg = f'https://api.telegram.org/bot{TOKEN}/{msg_type}?chat_id={chat_id}&text={msg_text}&parse_mode=HTML'
    logging.info("Sending Message to Telegram")
    telegram_msg = requests.get(msg)
    logging.info(f"Status Code: {telegram_msg.status_code}")
    if telegram_msg.status_code == 200:
        logging.info("Message posted to group")
    else:
        logging.info("Failed posting to group")
    logging.info("Waiting for 300 seconds")


while True:
    set_header()

    data = fetch_options(4,50,nf_nearest,url_nf)
    df = pd.DataFrame(data)
    df= df[['expiryDate','CE_IV', 'CE_LTP', 'strikePrice', 'PE_LTP', 'PE_IV']]

    # Telegram Message Type
    msg_type = 'sendMessage'
    tabular_data = PrettyTable(border=True, header=True, padding_width=0)
    tabular_data.field_names = ["LS", "US", "PE", "CE", "%D", "H"]
    
    lower_strike, upper_strike, pe_ltp_value, ce_ltp_value, diff, h_value = calc_values_option(df = df,ATM = nf_nearest,step=0)
    tabular_data.add_row([lower_strike, upper_strike, ce_ltp_value, pe_ltp_value, diff, h_value])

    lower_strike, upper_strike, pe_ltp_value, ce_ltp_value, diff, h_value = calc_values_option(df = df,ATM = nf_nearest,step=50)
    tabular_data.add_row([lower_strike, upper_strike, pe_ltp_value, ce_ltp_value, diff, h_value])

    lower_strike, upper_strike, pe_ltp_value, ce_ltp_value, diff, h_value = calc_values_option(df = df,ATM = nf_nearest,step=100)
    tabular_data.add_row([lower_strike, upper_strike, pe_ltp_value, ce_ltp_value, diff, h_value])

    lower_strike, upper_strike, pe_ltp_value, ce_ltp_value, diff, h_value = calc_values_option(df = df,ATM = nf_nearest,step=150)
    tabular_data.add_row([lower_strike, upper_strike, pe_ltp_value, ce_ltp_value, diff, h_value])

    lower_strike, upper_strike, pe_ltp_value, ce_ltp_value, diff, h_value = calc_values_option(df = df,ATM = nf_nearest,step=200)
    tabular_data.add_row([lower_strike, upper_strike, pe_ltp_value, ce_ltp_value, diff, h_value])

    # logging.info(f"{lower_strike}, {upper_strike}, {pe_ltp_value}, {ce_ltp_value}, {diff}, {h_value}")

    # ALERT in 200 WINDOW based on CE and PE values and difference between them             
    if (h_value == "C") and (diff >= 50):
        chat_id = 716713436
        msg_text = f"""<b>NIFTY LTP : {nf_ul}</b>\n<b>ATM :{nf_nearest}</b>\n<b>In 200 Window, CE > PE by {diff}</b>\n<b>Please place an Order</b>"""
        try:
            logging.info("ALERT")
            send_tg_message(TOKEN, chat_id, msg_type, msg_text)
        except Exception as e:
            logging.WARNING(f"Exception occured is {e}")
            continue
    if (h_value == "P") and (diff >= 80):
        chat_id = 716713436
        msg_text = f"""<b>NIFTY LTP : {nf_ul}</b>\n<b>ATM :{nf_nearest}</b>\n<b>In 200 Window, PE > CE by {diff}</b>\n<b>Please place an Order</b>"""
        try:
            logging.info("ALERT")
            send_tg_message(TOKEN, chat_id, msg_type, msg_text)
        except Exception as e:
            logging.WARNING(f"Exception occured is {e}")
            continue

    # response = requests.get(f"https://api.telegram.org/bot{TOKEN}/getUpdates").json()
    # Channel 1 - 5 mins interval updates
    # Channel 2 - Nearby Round Off
    # Channel 3 -  Alert Channel

    # chat_id = -986899914
    chat_id = 716713436
    msg_text = f"""<b>NIFTY LTP : {nf_ul}</b>\n<b>ATM :{nf_nearest}</b>\n\n<pre>{tabular_data}</pre>"""
    
    # Sending the 5 MIN REPORT for NIFTY
    try:
        send_tg_message(TOKEN, chat_id, msg_type, msg_text)
    except Exception as e:
        logging.WARNING(f"Exception occured is {e}")
        continue
    time.sleep(300)

