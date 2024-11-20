import pandas as pd
import numpy as np

class TPO:
    def __init__(self ):
        
        pass

    def calculate_TPO(self, df, NOfCandles, step=0.0001):
        """Calculate TPO using a sliding window over the DataFrame."""
        if len(df) < NOfCandles:
            raise ValueError("Not enough candles in the DataFrame to calculate TPO.")
        
        # Prepare a list to store results
        results = []

        # Iterate over each candle with a sliding window
        for i in range(NOfCandles, len(df)):
            # Select the last NOfCandles before the current candle
            df_window = df.iloc[i - NOfCandles:i]

            # Determine the time of the current candle
            current_time = df.iloc[i]['time']

            # Determine price bins (min to max of high/low in the last N candles)
            min_price = df_window['ask_l'].min()
            max_price = df_window['ask_h'].max()
            price_bins = np.arange(min_price, max_price + step, step)

            # Initialize TPO counts for price bins
            tpo_counts = {price: 0 for price in price_bins}

            # Count TPO occurrences for each bin
            for _, row in df_window.iterrows():
                low, high = row['ask_l'], row['ask_h']
                for price in price_bins:
                    if low <= price <= high:
                        tpo_counts[price] += 1

            # Sort TPO counts by value
            sorted_tpo = sorted(tpo_counts.items(), key=lambda x: x[1], reverse=True)

            # Select only the top 30 levels
            top_tpo = sorted_tpo[:30]

            # Convert to a DataFrame for this sliding window
            tpo_df = pd.DataFrame(top_tpo, columns=['Price', 'TPO'])
            tpo_df['Time'] = current_time

            # Append the results for this time step
            results.append(tpo_df)

        return results
