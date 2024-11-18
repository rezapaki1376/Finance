class MA:
    def __init__(self, MA_size=8):
        self.MA_size = MA_size

    def calculate_MA(self, df):
        """Calculate Moving Average (MA) and include it in the DataFrame."""
        df[f'ma{self.MA_size}'] = df['ask_c'].rolling(window=self.MA_size).mean()
        df.dropna(inplace=True)
        df.reset_index(drop=True, inplace=True)
        return df
