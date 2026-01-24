from stock import Stock


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