from stock import Stock
import pandas as pd


class StockPortfolio:
    def __init__(self, name="My Portfolio"):
        self.name = name
        self.stocks = {}  # {ticker: Stock object}

    def add_stock(self, ticker_symbol, quantity=1):
        """Add a Stock object to the portfolio."""
        ticker = ticker_symbol.upper()
        stock = Stock(ticker, quantity)
        if ticker in self.stocks:
            self.stocks[ticker].increase_quantity(stock.get_quantity_held())
        else:
            self.stocks[ticker] = stock

    def sell_stock(self, ticker_symbol, quantity):
        ticker = ticker_symbol.upper()
        if ticker not in self.stocks:
            raise KeyError(f"{ticker} not found in portfolio.")

        self.stocks[ticker].decrease_quantity(quantity)

    def remove_stock(self, ticker_symbol):
        """Remove a stock from the portfolio by ticker symbol."""
        ticker = ticker_symbol.upper()
        if ticker not in self.stocks:
            raise KeyError(f"{ticker} not found in portfolio.")
        del self.stocks[ticker]

    def get_stock(self, ticker_symbol):
        """Retrieve a stock by ticker symbol."""
        return self.stocks.get(ticker_symbol.upper(), None)

    def get_portfolio_value(self):
        """Calculate total market value of all holdings."""
        total_portfolio_value = 0
        for stock in self.stocks.values():
            total_portfolio_value += stock.get_total_value()

        return total_portfolio_value

    def holding_by_sector(self):
        sector_value_dict = {}  # {sector : total value held}
        total_portfolio_value = self.get_portfolio_value()

        for stock in self.stocks.values():
            sector = stock.company_info.sector
            value = stock.get_total_value()

            sector_value_dict[sector] = sector_value_dict.get(sector, 0) + value

        for key in sector_value_dict:
            sector_value_dict[key] = round(float(sector_value_dict[key]) / total_portfolio_value * 100, 2)

        return sector_value_dict

    def track_one_year_change(self):
        dollar_change = 0
        for stock in self.stocks.values():
            dollar_change += stock.change.yearly()[0]

        return round(dollar_change, 2)

    def sort_by_highest_value(self):
        return sorted(self.stocks.values(), key=lambda s: s.get_total_value(), reverse=True)

    def refresh_all_data(self):
        """Refresh all stock data using yfinance."""
        for stock in self.stocks.values():
            stock.refresh_data()

    def detailed_summary(self):
        """Return a clean, tabular summary of all holdings."""
        if not self.stocks:
            return f"Portfolio '{self.name}' is empty."

        lines = [f"\n{'=' * 70}", f"PORTFOLIO SUMMARY: {self.name}", f"{'=' * 70}",
                 f"{'Ticker':<8}{'Company':<25}{'Qty':<8}{'Price ($)':<12}{'Value ($)':<12}", "-" * 70]
        for stock in self.stocks.values():
            total_value = stock.get_total_value()
            lines.append(
                f"{stock.ticker_symbol:<8}"
                f"{stock.company_info.name[:24]:<25}"
                f"{stock.get_quantity_held():<8}"
                f"{stock.market_data.current_price:<12.2f}"
                f"{total_value:<12.2f}"
            )
        lines.append("-" * 70)
        lines.append(f"Total Portfolio Value: ${self.get_portfolio_value():,.2f}")
        lines.append(f"{'=' * 70}\n")
        return "\n".join(lines)

    def __str__(self):
        return f"Portfolio '{self.name}' | Holdings: {len(self.stocks)} | Total Value: ${self.get_portfolio_value():,.2f}"

    def get_portfolio_history(self, days=365):
        """Merges all stock histories into a single Total Value DataFrame."""
        combined_df = pd.DataFrame()

        for ticker, stock in self.stocks.items():
            hist = stock.history.get_days(days)['Close']
            if isinstance(hist, pd.DataFrame): hist = hist.iloc[:, 0]

            # Calculate value: Price * Quantity
            stock_value_series = hist * stock.get_quantity_held()

            if combined_df.empty:
                combined_df['TotalValue'] = stock_value_series
            else:
                combined_df['TotalValue'] = combined_df['TotalValue'].add(stock_value_series, fill_value=0)

            return combined_df.dropna()

    def get_risk_reward_data(self):
        """Compiles stats for all stocks for the scatter plot."""
        stats = []
        for ticker, stock in self.stocks.items():
            rm = stock.risk_metrics

            stats.append({
                'ticker': ticker,
                'return': rm.get_annualized_return(),
                'vol': rm.get_annualized_volatility(),
                'sharpe': rm.get_sharpe_ratio(),
                'treynor': rm.get_treynor_ratio()
            })
        return stats

    def get_portfolio_daily_sharpe(self):
        """Calculates the Sharpe Ratio of the entire portfolio for every day in the year."""
        portfolio_history = self.get_portfolio_history(days=365)

        # Calculate daily returns of the total portfolio value
        port_returns = portfolio_history['TotalValue'].pct_change().dropna()

        # Risk-free rate (daily)
        rf_daily = 0.04 / 252

        # Rolling 20-day Sharpe to show 'daily' movement
        rolling_mu = port_returns.rolling(window=20).mean()
        rolling_sigma = port_returns.rolling(window=20).std()

        daily_sharpe = (rolling_mu - rf_daily) / rolling_sigma
        return daily_sharpe.dropna()
