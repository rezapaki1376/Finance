import pandas as pd
import numpy as np

class TPO:
    def __init__(self, step=0.01):
        self.step = step  # Step size for price levels (e.g., 0.01 for granular bins)

    def calculate_TPO(self, df, NOfCandles):
        """Calculate TPO for the last N candles and associate it with the current candle's time."""
        # Get the last N candles
        df_last_n = df.iloc[-NOfCandles:]

        # Determine the time of the current (most recent) candle
        current_time = df_last_n.iloc[-1]['time']

        # Determine price bins (min to max of high/low in the last N candles)
        min_price = df_last_n['ask_l'].min()
        max_price = df_last_n['ask_h'].max()

        # Generate bins
        price_bins = np.arange(min_price, max_price + self.step, self.step)
        tpo_counts = {price: 0 for price in price_bins}

        # Count TPO occurrences for each bin
        for _, row in df_last_n.iterrows():
            low, high = row['ask_l'], row['ask_h']
            for price in price_bins:
                if low <= price <= high:
                    tpo_counts[price] += 1

        # Convert to a DataFrame
        tpo_df = pd.DataFrame({
            'Price': list(tpo_counts.keys()),
            'TPO': list(tpo_counts.values())
        })

        # Add the time of the current candle
        tpo_df['Time'] = current_time

        # Sort by TPO count descending
        tpo_df.sort_values(by='TPO', ascending=False, inplace=True)

        # Select only the top 30 levels
        tpo_df = tpo_df.head(30)
        tpo_df.reset_index(drop=True, inplace=True)

        return tpo_df