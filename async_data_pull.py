import json
import requests
import os

import asyncio
import aiohttp
from datetime import datetime, timedelta
import pandas as pd

# authentication requires your API credentials
CLIENT_ID = os.environ.get('CLIENT_ID') # api key
CLIENT_SECRET = os.environ.get('CLIENT_SECRET') # secret
REFRESH_TOKEN = os.environ.get('REFRESH_TOKEN') # your refresh token


def get_access_token():
    url = "https://signin.tradestation.com/oauth/token"

    payload=f'grant_type=refresh_token&client_id={CLIENT_ID}&client_secret={CLIENT_SECRET}&refresh_token={REFRESH_TOKEN}'
    headers = {
      'Content-Type': 'application/x-www-form-urlencoded'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    response_data = response.json()
    return response_data['access_token']


def process_chunk(chunk):
    return pd.DataFrame(chunk['Bars'])


async def fetch_data(session, start_date, end_date):
    params = {
        "unit": "Minute",
        "interval": "15",
        "firstdate": start_date.isoformat() + "Z",
        "lastdate": end_date.isoformat() + "Z",
    }
    async with session.get(BASE_URL, params=params) as response:
        return await response.json()

async def main(symb):
    start_date = datetime(2000, 1, 1)
    end_date = datetime(2024, 8, 29)
    chunk_size = timedelta(days=365)  # 1 year chunks

    async with aiohttp.ClientSession(headers=headers) as session:
        tasks = []
        current_start = start_date
        while current_start < end_date:
            current_end = min(current_start + chunk_size, end_date)
            task = asyncio.create_task(fetch_data(session, current_start, current_end))
            tasks.append(task)
            current_start = current_end

        results = await asyncio.gather(*tasks)

    # Process and combine results as needed
    dfs = []
    for result in results:
        # Process each chunk of data
        if 'Bars' in result:
        	df_chunk = process_chunk(result)
        	dfs.append(df_chunk)

    # Concatenate all DataFrames
    final_df = pd.concat(dfs, ignore_index=True)

    # Sort the DataFrame by date if necessary
    final_df['TimeStamp'] = pd.to_datetime(final_df['TimeStamp'])  
    final_df = final_df.sort_values('TimeStamp')

    # Remove any duplicate rows if they exist
    final_df = final_df.drop_duplicates()

    print(f"{symb} shape: {final_df.shape}")

    # Optionally, save the DataFrame to a CSV file
    final_df.to_csv(f'{symb}_15m_data_2000_2024.csv', index=False)

if __name__ == "__main__":
	markets = ['@ES','@NG','@CL','@GC','@NQ','@RTY','@US','@TY']

	for market in markets:
		BASE_URL = f"https://api.tradestation.com/v3/marketdata/barcharts/{market}"
		access_token = get_access_token()
		headers = {"Authorization": f'Bearer {access_token}'}
		asyncio.run(main(market))

	print("we've finished loading the data")