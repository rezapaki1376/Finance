import pandas as pd

class ATR:
    def __init__(self, ATR_period=14):
        self.ATR_period = ATR_period

    def calculate_ATR(self, df):
        """Calculate the Average True Range (ATR) for the given DataFrame."""
        df['High-Low'] = df['ask_h'] - df['ask_l']
        df['High-Close'] = abs(df['ask_h'] - df['ask_c'].shift(1))
        df['Low-Close'] = abs(df['ask_l'] - df['ask_c'].shift(1))
        df['TrueRange'] = df[['High-Low', 'High-Close', 'Low-Close']].max(axis=1)
        df['ATR'] = df['TrueRange'].rolling(window=self.ATR_period).mean()
        df = df.drop(['High-Low', 'High-Close', 'Low-Close', 'TrueRange'], axis=1)
        df.dropna(inplace=True)
        df.reset_index(drop=True, inplace=True)
        return df
