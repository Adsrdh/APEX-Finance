from stock import Stock
import pandas as pd
import numpy as np


class StockPortfolio:
    def __init__(self, name="My Portfolio"):
        self.name = name
        self.stocks = {}  # {ticker: Stock object}

    def add_stock(self, ticker_symbol, quantity=1):
        """Add a Stock object with error catching for invalid tickers."""
        try:
            ticker = ticker_symbol.upper()
            if ticker in self.stocks:
                self.stocks[ticker].increase_quantity(quantity)
            else:
                # This will trigger the ValueError in Stock.__init__ if ticker is fake
                self.stocks[ticker] = Stock(ticker, quantity)
        except Exception as e:
            print(f"Failed to add {ticker_symbol}: {e}")
            raise  # Re-raise so the Frontend can show an error message

    def sell_stock(self, ticker_symbol, quantity):
        ticker = ticker_symbol.upper()
        if ticker not in self.stocks:
            raise KeyError(f"Ticker {ticker} not found in portfolio.")

        try:
            self.stocks[ticker].decrease_quantity(quantity)
            # If quantity hits 0, we might want to keep it or remove it.
            # Usually, in a tracker, we keep it with 0 qty unless explicitly removed.
        except ValueError as e:
            raise ValueError(f"Transaction failed: {e}")

    def get_portfolio_value(self):
        """Safe calculation of total value."""
        if not self.stocks:
            return 0.0
        return sum(stock.get_total_value() for stock in self.stocks.values())

    def holding_by_sector(self):
        """Calculates sector distribution with ZeroDivision protection."""
        if not self.stocks:
            return {}

        sector_value_dict = {}
        total_value = self.get_portfolio_value()

        if total_value == 0:
            return {stock.company_info.sector: 0.0 for stock in self.stocks.values()}

        for stock in self.stocks.values():
            sector = stock.company_info.sector or "Unknown"
            value = stock.get_total_value()
            sector_value_dict[sector] = sector_value_dict.get(sector, 0) + value

        # Convert to percentages
        return {k: round((v / total_value) * 100, 2) for k, v in sector_value_dict.items()}

    def get_portfolio_history(self, days=365):
        """
        Merges histories. Uses 'outer' join to prevent missing data in one stock
        from deleting the entire portfolio's history.
        """
        if not self.stocks:
            return pd.DataFrame(columns=['TotalValue'])

        combined_df = pd.DataFrame()

        for ticker, stock in self.stocks.items():
            try:
                # Fetch history and handle potential Empty DataFrames
                hist_data = stock.history.get_days(days)
                if hist_data.empty:
                    continue

                prices = hist_data['Close']
                if isinstance(prices, pd.DataFrame):
                    prices = prices.iloc[:, 0]

                stock_value_series = prices * stock.get_quantity_held()

                if combined_df.empty:
                    combined_df['TotalValue'] = stock_value_series
                else:
                    combined_df['TotalValue'] = combined_df['TotalValue'].add(stock_value_series, fill_value=0)
            except Exception as e:
                print(f"Warning: Could not include {ticker} in history: {e}")
                continue

        return combined_df.sort_index().ffill().dropna()

    def get_risk_reward_data(self):
        """Safe compilation of risk metrics for scatter plots."""
        stats = []
        for ticker, stock in self.stocks.items():
            # Check if risk_metrics exists (might be None if history fetch failed)
            rm = stock.risk_metrics
            if rm is None:
                continue

            try:
                stats.append({
                    'ticker': ticker,
                    'return': rm.get_annualized_return() or 0.0,
                    'vol': rm.get_annualized_volatility() or 0.0,
                    'sharpe': rm.get_sharpe_ratio() or 0.0,
                    'treynor': rm.get_treynor_ratio() or 0.0
                })
            except Exception:
                continue
        return stats

    def get_portfolio_daily_sharpe(self):
        """Calculates daily Sharpe with protection against empty history or low volatility."""
        try:
            portfolio_history = self.get_portfolio_history(days=365)
            if portfolio_history.empty or len(portfolio_history) < 20:
                return pd.Series(dtype='float64')

            port_returns = portfolio_history['TotalValue'].pct_change().fillna(0)
            rf_daily = 0.04 / 252

            rolling_mu = port_returns.rolling(window=20).mean()
            rolling_sigma = port_returns.rolling(window=20).std()

            # Replace 0 sigma with NaN to avoid division by zero, then fill with 0
            daily_sharpe = (rolling_mu - rf_daily) / rolling_sigma.replace(0, np.nan)
            return daily_sharpe.fillna(0).dropna()
        except Exception as e:
            print(f"Daily Sharpe calculation error: {e}")
            return pd.Series(dtype='float64')

    def detailed_summary(self):
        """Clean summary with formatting protection."""
        if not self.stocks:
            return f"Portfolio '{self.name}' is currently empty."

        header = f"\n{'=' * 85}\nPORTFOLIO SUMMARY: {self.name}\n{'=' * 85}\n"
        columns = f"{'Ticker':<8}{'Company':<30}{'Qty':<10}{'Price ($)':<15}{'Value ($)':<15}\n"
        divider = "-" * 85 + "\n"

        lines = [header, columns, divider]

        for stock in self.stocks.values():
            try:
                name = (stock.company_info.name[:28] + '..') if len(
                    stock.company_info.name) > 30 else stock.company_info.name
                lines.append(
                    f"{stock.ticker_symbol:<8}"
                    f"{name:<30}"
                    f"{stock.get_quantity_held():<10}"
                    f"{stock.market_data.current_price:<15,.2f}"
                    f"{stock.get_total_value():<15,.2f}\n"
                )
            except Exception:
                continue

        lines.append(divider)
        lines.append(f"TOTAL PORTFOLIO VALUE: ${self.get_portfolio_value():,.2f}\n")
        lines.append('=' * 85 + "\n")
        return "".join(lines)
