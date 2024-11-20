import pandas as pd

class ATR:
    def __init__(self):
        pass  # No need to initialize ATR_period globally

    def calculate_ATR(self, ATR_period, df):
        """Calculate the Average True Range (ATR) for the given DataFrame."""
        # Ensure columns are numeric
        df['ask_h'] = pd.to_numeric(df['ask_h'], errors='coerce')
        df['ask_l'] = pd.to_numeric(df['ask_l'], errors='coerce')
        df['ask_c'] = pd.to_numeric(df['ask_c'], errors='coerce')

        # Handle NaN values
        df.dropna(inplace=True)

        # Calculate True Range components
        df['High-Low'] = df['ask_h'] - df['ask_l']
        df['High-Close'] = abs(df['ask_h'] - df['ask_c'].shift(1))
        df['Low-Close'] = abs(df['ask_l'] - df['ask_c'].shift(1))
        df['TrueRange'] = df[['High-Low', 'High-Close', 'Low-Close']].max(axis=1)

        # Initialize ATR column
        df[f'ATR{ATR_period}'] = 0.0

        # Compute ATR dynamically for the first `ATR_period` rows
        for i in range(len(df)):
            window_size = min(i + 1, ATR_period)  # Dynamically adjust the window size
            df.at[i, f'ATR{ATR_period}'] = df['TrueRange'].iloc[:i + 1].rolling(window=window_size).mean().iloc[-1]

        # Drop intermediate columns
        df.drop(['High-Low', 'High-Close', 'Low-Close', 'TrueRange'], axis=1, inplace=True)
        df.reset_index(drop=True, inplace=True)

        return df
