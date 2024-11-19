import pandas as pd

class MA:
    def __init__(self):
        pass  # No need for initialization parameters

    def calculate_MA(self, MA_size, df):
        """Calculate Moving Average (MA) dynamically and include it in the DataFrame."""
        # Initialize MA column
        df[f'ma{MA_size}'] = 0.0

        # Compute MA dynamically for the first `MA_size` rows
        for i in range(len(df)):
            window_size = min(i + 1, MA_size)  # Dynamically adjust the window size
            df.at[i, f'ma{MA_size}'] = df['ask_c'].iloc[:i + 1].rolling(window=window_size).mean().iloc[-1]

        # No need to drop rows, as we handle dynamic calculation
        df.reset_index(drop=True, inplace=True)

        return df
