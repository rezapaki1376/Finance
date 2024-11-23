import pandas as pd


class MACrossover:
    def __init__(self, df, initial_capital, risk_type='constant'):
        """
        Initialize the trading strategy with required data and parameters.
        
        Args:
            df (pd.DataFrame): The DataFrame containing market data.
            initial_capital (float): Starting capital for the strategy.
            risk_type (str): The type of risk management ('constant' or 'altering_8_step').
        """
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
        self.risk_percentage = 0.01  # Default risk percentage
        self.risk_steps = [0.01, 0.02, 0.04, 0.08, 0.16, 0.32, 0.64, 1.0]  # Risk steps for altering risk
        self.current_risk_step = 0  # Start at step 0
        self.trade_log = []  # To store trade results
        self.total_pure_profit = 0
        self.current_step_profit = 0

    def calculate_signals(self, MA_minor, MA_major):
        """
        Generate buy and sell signals based on moving average crossovers using bid prices.
        """
        self.df[f'MA{MA_minor}'] = self.df['bid_c'].rolling(window=MA_minor).mean()
        self.df[f'MA{MA_major}'] = self.df['bid_c'].rolling(window=MA_major).mean()

        # Shifted values for crossover comparison
        self.df[f'MA{MA_minor}_prev'] = self.df[f'MA{MA_minor}'].shift(1)
        self.df[f'MA{MA_major}_prev'] = self.df[f'MA{MA_major}'].shift(1)

        self.df['Signal'] = 0  # Default no signal

        # Long signal: MA20 crosses above MA50
        self.df.loc[
            (self.df[f'MA{MA_minor}_prev'] <= self.df[f'MA{MA_major}_prev']) & (self.df[f'MA{MA_minor}'] > self.df[f'MA{MA_major}']),
            'Signal',
        ] = 1

        # Short signal: MA20 crosses below MA50
        self.df.loc[
            (self.df[f'MA{MA_minor}_prev'] >= self.df[f'MA{MA_major}_prev']) & (self.df[f'MA{MA_minor}'] < self.df[f'MA{MA_major}']),
            'Signal',
        ] = -1

        # Shift signals to the next time frame
        self.df['Signal'] = self.df['Signal'].shift(-1)

    def constant_risk(self, risk_percentage=0.01):
        """
        Use a constant risk percentage for position sizing.
        
        Args:
            risk_percentage (float): Percentage of capital to risk per trade.
        """
        self.risk_percentage = risk_percentage

    def alteringrisk(self):
        """
        Adjust risk dynamically based on profit or loss thresholds.
        
        Args:
            profit_loss (float): Profit or loss of the trade.
        """
        # Adjust risk step based on profit or loss thresholds
        curernt_step_profit_per = (self.current_step_profit/self.initial_capital)
        # print('self.current_step_profit',self.current_step_profit)
        # print('curernt_step_profit_per',curernt_step_profit_per)
        if curernt_step_profit_per >= 0.1:  # 10% profit
            self.current_step_profit = 0
            print('profit changed because of 0.1 profit ')
            self.current_risk_step = min(self.current_risk_step + 1, len(self.risk_steps) - 1)
        elif curernt_step_profit_per <= -0.05:  # 5% loss
            # print('current profit %',profit_loss)
            self.current_step_profit = 0
            self.current_risk_step = max(self.current_risk_step - 1, 0)
            print('profit changed because of 0.05 lost ')

        # Update risk percentage based on the current step
        self.risk_percentage = self.risk_steps[self.current_risk_step]

    def handle_position(self):
        """
        Execute trades based on signals at the next candle's open bid price.
        """
        for i in range(len(self.df) - 1):  # Iterate until the second-last row
            signal = self.df.loc[i, 'Signal']
            atr = self.df.loc[i, f'{self.atr_column}']
            next_open_price = self.df.loc[i + 1, 'bid_o']  # Next candle's open bid price
            
            if signal == 1:  # Long position
                stop_loss_distance = 3 * atr
                stop_loss = next_open_price - stop_loss_distance
                take_profit = next_open_price + 6 * atr
                self.execute_trade(i + 1, "long", next_open_price, stop_loss, take_profit)

            elif signal == -1:  # Short position
                stop_loss_distance = 3 * atr
                stop_loss = next_open_price + stop_loss_distance
                take_profit = next_open_price - 6 * atr
                self.execute_trade(i + 1, "short", next_open_price, stop_loss, take_profit)

    def execute_trade(self, i, position_type, entry_price, stop_loss, take_profit):
        """
        Simulate a trade and update the DataFrame with trade outcomes using bid prices.
        
        Args:
            i (int): The index of the trade in the DataFrame.
            position_type (str): "long" or "short".
            entry_price (float): The entry price of the trade.
            stop_loss (float): The stop-loss price.
            take_profit (float): The take-profit price.
        """
        if self.risk_type == 'altering_8_step':
            # print('(self.initial_capital-self.current_capital)/self.initial_capital',-(self.initial_capital-self.current_capital)/self.initial_capital)
            self.alteringrisk()  # Adjust risk dynamically

        risk_per_trade = self.risk_percentage * self.current_capital


        for j in range(i + 1, len(self.df)):
            current_price = self.df.loc[j, 'bid_c']
            time_start = self.df.loc[i, 'time']
            time_end = self.df.loc[j, 'time']

            if position_type == "long":
                if current_price <= stop_loss or current_price >= take_profit:
                    pip_amount = current_price - entry_price
                    profit_loss = pip_amount * risk_per_trade
                    self.total_pure_profit+=profit_loss
                    self.current_step_profit += profit_loss
                    self.update_trade_log(time_start, time_end, entry_price, current_price, pip_amount, profit_loss)
                    break

            elif position_type == "short":
                if current_price >= stop_loss or current_price <= take_profit:
                    pip_amount = entry_price - current_price
                    profit_loss = pip_amount * risk_per_trade
                    self.total_pure_profit+=profit_loss
                    self.current_step_profit += profit_loss
                    self.update_trade_log(time_start, time_end, entry_price, current_price, pip_amount, profit_loss)
                    break

    def update_trade_log(self, start_time, end_time, entry_price, exit_price, pip_amount, profit_loss):
        """
        Update trade log and adjust capital based on trade outcome.
        
        Args:
            start_time (str): Start time of the trade.
            end_time (str): End time of the trade.
            entry_price (float): Entry price of the position.
            exit_price (float): Exit price of the position.
            pip_amount (float): Difference between entry and exit price.
            profit_loss (float): Profit or loss of the trade.
        """
        self.current_capital += profit_loss  # Update current capital
        
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

    def run_strategy(self, MA_minor, MA_major, constant_risk=0.01):
        """
        Execute the complete strategy and return the trade log.
        
        Args:
            constant_risk (float): Risk percentage for constant risk management.

        Returns:
            pd.DataFrame: The trade log as a DataFrame.
        """
        if self.risk_type == 'constant':
            self.constant_risk(constant_risk)
        self.calculate_signals(MA_minor, MA_major)
        self.handle_position()
        return pd.DataFrame(self.trade_log)


# Example usage:
# Assuming `data` is your DataFrame with required columns including 'time', 'bid_c', 'bid_o', and 'ATR15'.
# strategy = TradingStrategy(data, initial_capital=10000, risk_type='altering_8_step')
# trade_log_df = strategy.run_strategy()
# print(trade_log_df)
