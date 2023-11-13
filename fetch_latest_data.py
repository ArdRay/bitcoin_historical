#!/bin/python3
import pandas as pd
import requests
import datetime
import argparse
import json
from dateutil import tz

def fetch_daily_data(symbol, start, end):
    pair_split = symbol.split('/') 
    symbol = pair_split[0] + '-' + pair_split[1]
    url = f'https://api.pro.coinbase.com/products/{symbol}/candles?granularity=3600&start={start}&end={end}'
    try:
        response = requests.get(url, timeout=2)
        print('HTTP code: {} - {} to {} - size: {}'.format(response.status_code,start,end,len(response.content)))
        if response.status_code == 200: 
            data = pd.DataFrame(json.loads(response.text), columns=['unix', 'low', 'high', 'open', 'close', 'volume'])
            data['date'] = pd.to_datetime(data['unix'], unit='s').dt.tz_localize(tz.tzlocal())
            data['vol_fiat'] = data['volume'] * data['close'] ##approximate
            return(data)
    except requests.exceptions.RequestException as e:
        raise SystemExit(e)

def fetch_present_data(filename='historical_data/bitcoin.csv'):
    df_raw = pd.read_csv(filename)
    df_raw['date'] = pd.to_datetime(df_raw['unix'], unit='s').dt.tz_localize(tz.tzlocal())
    df_raw = df_raw.sort_values(by=['date'])
    df_raw = df_raw.set_index('date')
    df_raw.index = pd.to_datetime(df_raw.index)
    return(df_raw)

def fetch_and_save_data(current_data, filename='historical_data/bitcoin.csv'):
    end_date = pd.Timestamp.today().strftime('%Y-%m-%d %H:00:00')
    start_date = current_data.tail(1).index.strftime('%Y-%m-%d %H:00:00').values[0]
    newly_fetched_data = fetch_daily_data('BTC/USD', start_date, end_date)
    newly_fetched_data = newly_fetched_data.sort_values(by=['date'])
    newly_fetched_data = newly_fetched_data.set_index('date')
    newly_fetched_data.index = pd.to_datetime(newly_fetched_data.index)
    combined_data = pd.concat([newly_fetched_data, current_data])
    combined_data = combined_data.sort_values(by=['date'])
    combined_data = combined_data.drop_duplicates(subset=['unix'])
    combined_data.to_csv(filename, index=True)
    print('CSV saved at {}'.format(filename))

def main():
    parser = argparse.ArgumentParser(description='Fetch the latest historical data from coinbase API.')
    parser.add_argument('-f','--file', help='Path to file is required.', required=True)
    args = parser.parse_args()

    current_year = datetime.date.today().year
    adjusted_file_path = "historical_data/bitcoin_{}.csv".format(current_year)
    
    # Dirty adjustment to avoid ever-increasing CSV file
    if current_year >= 2024:
        current_data = fetch_present_data(adjusted_file_path)
        fetch_and_save_data(current_data, adjusted_file_path)  
    else:
        current_data = fetch_present_data(args.file)
        fetch_and_save_data(current_data, args.file)   

if __name__ == "__main__":
    main()