from utils.args import get_args
import pandas as pd
import requests
from datetime import datetime, timedelta


class DataGeneration:
    def __init__(self,
                 instument_name: str = 'EUR_USD',
                 time_frame: str = 'H1',
                 count: int = 100,
                 start_time: str = '',
                 end_time: str = '',
                 price: str = 'MBA',
                 MaxReturnedCandleLimit: int = 5000):
        args = get_args()
        self.instument_name = instument_name
        self.time_frame = time_frame
        self.count = count
        self.start_time = start_time
        self.end_time = end_time
        self.MaxReturnedCandleLimit = MaxReturnedCandleLimit
        self.URL = f"{args.SERVICE_URL}/instruments/{instument_name}/candles"
        self.session = requests.Session()
        self.price = price
        self.prices_list = []
        if 'M' in self.price:
            self.prices_list.append('mid')
        if 'B' in self.price:
            self.prices_list.append('bid')
        if 'A' in self.price:
            self.prices_list.append('ask')
        self.headers = args.SECURE_HEADER
        self.params = dict(
            granularity=self.time_frame,
            price=self.price
        )

    def calculate_time_interval(self):
        """Calculate the time interval for each API call based on MaxReturnedCandleLimit."""
        time_frame_to_seconds = {
            'S5': 5,
            'S10': 10,
            'S15': 15,
            'S30': 30,
            'M1': 60,
            'M2': 120,
            'M5': 300,
            'M15': 900,
            'M30': 1800,
            'H1': 3600,
            'H4': 14400,
            'D': 86400
        }
        if self.time_frame not in time_frame_to_seconds:
            raise ValueError(f"Unsupported time frame: {self.time_frame}")
        interval_seconds = time_frame_to_seconds[self.time_frame] * self.MaxReturnedCandleLimit
        return timedelta(seconds=interval_seconds)

    def get_data(self):
        self.response = self.session.get(self.URL, params=self.params, headers=self.headers)
        return self.response.status_code, self.response.json()

    def get_instruments_df(self):
        if not self.start_time or not self.end_time:
            raise ValueError("Both start_time and end_time must be provided in ISO 8601 format.")

        start_dt = datetime.fromisoformat(self.start_time.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(self.end_time.replace('Z', '+00:00'))
        interval = self.calculate_time_interval()

        all_data = []

        while start_dt < end_dt:
            current_end_dt = min(start_dt + interval, end_dt)
            # Adjust time format to remove +00:00 and add Z
            self.params['from'] = start_dt.isoformat().replace('+00:00', 'Z')
            self.params['to'] = current_end_dt.isoformat().replace('+00:00', 'Z')

            # Debugging: Print the formatted parameters
            print(f"Requesting data from {self.params['from']} to {self.params['to']}")
            print(f"Params: {self.params}")

            code, data = self.get_data()

            # Debugging: Print response status and content
            print(f"Response status: {code}")
            if code != 200:
                print(f"Response content: {self.response.text}")  # Print the raw response for debugging

            if code == 200:
                ohlc = ['o', 'h', 'l', 'c']
                for candle in data['candles']:
                    if not candle['complete']:
                        continue
                    new_dict = {
                        'time': candle['time'],
                        'volume': candle['volume']
                    }
                    for price in self.prices_list:
                        for oh in ohlc:
                            new_dict[f"{price}_{oh}"] = candle[price][oh]
                    all_data.append(new_dict)
            else:
                raise RuntimeError(f"Failed to fetch data. Status code: {code}. Response: {self.response.text}")

            # Update the start date for the next iteration
            start_dt = current_end_dt

        # Concatenate all the data into a single DataFrame
        return pd.DataFrame.from_records(all_data)
