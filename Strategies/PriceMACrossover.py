import pandas as pd


class PriceMACrossover:
    def __init__(self, df, initial_capital, risk_type='constant'):
        self.df = df.copy()
        self.risk_type = risk_type
        self.atr_column = [col for col in df.columns if col.startswith("ATR")][0]

        # Convert relevant columns to numeric
        self.df['bid_c'] = pd.to_numeric(self.df['bid_c'], errors='coerce')
        self.df['bid_o'] = pd.to_numeric(self.df['bid_o'], errors='coerce')
        self.df[f'{self.atr_column}'] = pd.to_numeric(self.df[f'{self.atr_column}'], errors='coerce')

        # Drop rows with NaN values in key columns
        self.df.dropna(subset=['bid_c', 'bid_o', f'{self.atr_column}'], inplace=True)

        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.risk_percentage = 0.01
        self.risk_steps = [0.01, 0.02, 0.04, 0.08, 0.16, 0.32, 0.64, 1.0]
        self.current_risk_step = 0
        self.trade_log = []
        self.total_pure_profit = 0
        self.current_step_profit = 0

    def calculate_signals(self, MA):
        """
        Generate buy and sell signals based on price (close) crossing moving average.

        Args:
            MA (int): Moving average period.
        """
        # Calculate the moving average
        self.df[f'MA{MA}'] = self.df['bid_c'].rolling(window=MA).mean()

        # Shifted values for crossover comparison
        self.df['bid_c_prev'] = self.df['bid_c'].shift(1)
        self.df[f'MA{MA}_prev'] = self.df[f'MA{MA}'].shift(1)

        self.df['Signal'] = 0  # Default no signal

        # Long signal: Price crosses above MA
        self.df.loc[
            (self.df['bid_c_prev'] <= self.df[f'MA{MA}_prev']) & (self.df['bid_c'] > self.df[f'MA{MA}']),
            'Signal',
        ] = 1

        # Short signal: Price crosses below MA
        self.df.loc[
            (self.df['bid_c_prev'] >= self.df[f'MA{MA}_prev']) & (self.df['bid_c'] < self.df[f'MA{MA}']),
            'Signal',
        ] = -1

        # Shift signals to the next time frame
        self.df['Signal'] = self.df['Signal'].shift(-1)

    def constant_risk(self, risk_percentage=0.01):
        self.risk_percentage = risk_percentage

    def alteringrisk(self):
        current_step_profit_per = (self.current_step_profit / self.initial_capital)
        if current_step_profit_per >= 0.1:
            print('more that 10 % profit')
            self.current_step_profit = 0
            self.current_risk_step = min(self.current_risk_step + 1, len(self.risk_steps) - 1)
        elif current_step_profit_per <= -0.05:
            print('more that 5% lost')
            self.current_step_profit = 0
            self.current_risk_step = max(self.current_risk_step - 1, 0)

        self.risk_percentage = self.risk_steps[self.current_risk_step]

    def handle_position(self):
        for i in range(len(self.df) - 1):
            signal = self.df.loc[i, 'Signal']
            atr = self.df.loc[i, f'{self.atr_column}']
            next_open_price = self.df.loc[i + 1, 'bid_o']

            if signal == 1:
                stop_loss_distance = 3 * atr
                stop_loss = next_open_price - stop_loss_distance
                take_profit = next_open_price + 6 * atr
                self.execute_trade(i + 1, "long", next_open_price, stop_loss, take_profit)

            elif signal == -1:
                stop_loss_distance = 3 * atr
                stop_loss = next_open_price + stop_loss_distance
                take_profit = next_open_price - 6 * atr
                self.execute_trade(i + 1, "short", next_open_price, stop_loss, take_profit)

    def execute_trade(self, i, position_type, entry_price, stop_loss, take_profit):
        if self.risk_type == 'altering_8_step':
            self.alteringrisk()

        risk_per_trade = self.risk_percentage * self.current_capital

        for j in range(i + 1, len(self.df)):
            current_price = self.df.loc[j, 'bid_c']
            time_start = self.df.loc[i, 'time']
            time_end = self.df.loc[j, 'time']

            if position_type == "long":
                if current_price <= stop_loss or current_price >= take_profit:
                    pip_amount = current_price - entry_price
                    profit_loss = pip_amount * risk_per_trade
                    self.total_pure_profit += profit_loss
                    self.current_step_profit += profit_loss
                    self.update_trade_log(time_start, time_end, entry_price, current_price, pip_amount, profit_loss)
                    break

            elif position_type == "short":
                if current_price >= stop_loss or current_price <= take_profit:
                    pip_amount = entry_price - current_price
                    profit_loss = pip_amount * risk_per_trade
                    self.total_pure_profit += profit_loss
                    self.current_step_profit += profit_loss
                    self.update_trade_log(time_start, time_end, entry_price, current_price, pip_amount, profit_loss)
                    break

    def update_trade_log(self, start_time, end_time, entry_price, exit_price, pip_amount, profit_loss):
        self.current_capital += profit_loss
        self.trade_log.append({
            "Start Time": start_time,
            "End Time": end_time,
            "Entry Price": entry_price,
            "Exit Price": exit_price,
            "Pip Amount": pip_amount,
            "Profit/Loss": profit_loss,
            "Total Capital": self.current_capital,
            "Risk Percentage": self.risk_percentage,
        })

    def run_strategy(self, MA, constant_risk=0.01):
        if self.risk_type == 'constant':
            self.constant_risk(constant_risk)
        self.calculate_signals(MA)
        self.handle_position()
        return pd.DataFrame(self.trade_log)
