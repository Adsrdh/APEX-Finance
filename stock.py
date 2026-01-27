import yfinance as yf
import datetime
import pandas as pd


class Stock:
    def __init__(self, ticker_symbol, quantity=1):
        self.ticker_symbol = ticker_symbol.upper()
        data = yf.Ticker(self.ticker_symbol).info
        self.company_info = CompanyInfo(data)
        self.valuation = ValuationMetrics(data)
        self.market_data = MarketData(data)
        self.financials = Financials(data)
        self._quantity_held = quantity
        self.change = Change(self.ticker_symbol, self.market_data.current_price)
        self.history = History(self.ticker_symbol)

    def get_quantity_held(self):
        return self._quantity_held

    def increase_quantity(self, amount):
        if amount <= 0:
            raise ValueError
        else:
            self._quantity_held += amount

    def decrease_quantity(self, amount):
        """Decreases the stock quantity held"""
        if amount > self._quantity_held:
            raise ValueError
        elif amount <= 0:
            raise ValueError
        else:
            self._quantity_held -= amount

    def get_total_value(self):
        return self.market_data.current_price * self._quantity_held

    def refresh_data(self):
        data = yf.Ticker(self.ticker_symbol).info
        self.company_info = CompanyInfo(data)
        self.valuation = ValuationMetrics(data)
        self.market_data = MarketData(data)
        self.financials = Financials(data)
        print(f"Data for {self.ticker_symbol} refreshed successfully.")

    def get_change(self, period="daily"):
        """
        Gateway method to access the Change class calculations.
        Supported periods: 'daily', 'monthly', 'six_month', 'yearly'
        """
        period = period.lower()

        if period == "daily":
            return self.change.daily()
        elif period == "monthly":
            return self.change.monthly()
        elif period == "six_month":
            return self.change.six_month()
        elif period == "yearly":
            return self.change.yearly()
        else:
            # Default to specific days if a number is passed as a string
            try:
                days = int(period)
                return self.change.calculate_change(days)
            except ValueError:
                raise ValueError(f"Invalid period: {period}")

    def get_historical_data(self, period="daily"):
        """
        Gateway method to access the Change class calculations.
        Supported periods: 'daily', 'monthly', 'six_month', 'yearly'
        """
        period = period.lower()

        if period == "daily":
            return self.history.daily()
        elif period == "monthly":
            return self.history.monthly()
        elif period == "six_month":
            return self.history.six_month()
        elif period == "yearly":
            return self.history.yearly()
        else:
            # Default to specific days if a number is passed as a string
            try:
                days = int(period)
                return self.change.calculate_change(days)
            except ValueError:
                raise ValueError(f"Invalid period: {period}")

    def __str__(self):
        return (
            f"\n{'=' * 60}\n"
            f"📊 STOCK OVERVIEW: {self.ticker_symbol} ({self.company_info.name})\n"
            f"{'=' * 60}\n"
            f"Quantity Held: {self._quantity_held}\n"
            f"Current Price: ${self.market_data.current_price:,.2f}\n"
            f"Sector: {self.company_info.sector} | Industry: {self.company_info.industry}\n"
            f"Market Cap: ${self.market_data.market_cap / 1_000_000_000_000:.2f}T\n"
            f"Recommendation: {self.valuation.recommendation.capitalize()}\n"
            f"{'-' * 60}\n"
            f"{self.valuation}"
            f"{self.market_data}"
            f"{self.financials}"
            f"{'-' * 60}\n"
            f"🌐 More Info: {self.company_info.website}\n"
            f"{'=' * 60}\n"
        )


class CompanyInfo:
    def __init__(self, data):
        self.name = data["longName"]
        self.sector = data["sector"]
        self.industry = data["industry"]
        self.phone = data["phone"]
        self.summary = data["longBusinessSummary"]
        self.website = data["website"]
        self.employees = data["fullTimeEmployees"]
        self.executive_board = ExecutiveBoard(data["companyOfficers"])
        self.address = Address(data)

    def __str__(self):
        return (
            f"\n{self.name}\n"
            f"Sector: {self.sector} | Industry: {self.industry}\n"
            f"Employees: {self.employees}\n"
            f"Headquarters: {self.address}\n"
            f"Website: {self.website}\n"
        )


class ExecutiveBoard:
    def __init__(self, executive_member_data):
        self.executive_board = [ExecutiveMember(member) for member in executive_member_data]

    def __str__(self):
        top_execs = self.executive_board[:3]
        exec_lines = "\n".join(f" - {exec_}" for exec_ in top_execs)
        return f"\nExecutive Board:\n{exec_lines}\n"


class ExecutiveMember:
    def __init__(self, member):
        self.name = member.get("name", "N/A")
        self.title = member.get("title", "N/A")
        self.age = member.get("age", "N/A")
        self.birth_year = member.get("yearBorn", "N/A")
        self.pay = member.get("totalPay", "N/A")

    def __str__(self):
        pay_str = f"${self.pay:,.0f}" if isinstance(self.pay, (int, float)) else "N/A"
        return f"{self.name} ({self.age}) — {self.title} | Total Pay: {pay_str}"


class Address:
    def __init__(self, data):
        self.line1 = data["address1"]
        self.city = data["city"]
        self.state = data["state"]
        self.country = data["country"]
        self.zip = data["zip"]

    def __str__(self):
        return f"{self.line1}, {self.city}, {self.state}, {self.country}, {self.zip}"


class ValuationMetrics:
    def __init__(self, data):
        self.pe = data["trailingPE"]
        self.forward_pe = data["forwardPE"]
        self.pb_ratio = data["priceToBook"]
        self.dividend_yield = data["dividendYield"]
        self.dividend_rate = data["dividendRate"]
        self.beta = data["beta"]
        self.eps = data["trailingEps"]
        self.target_mean_price = data["targetMeanPrice"]
        self.recommendation = data["recommendationKey"]

    def pe_difference(self):
        return self.pe - self.forward_pe

    def dividend_yield_percent(self):
        return self.dividend_yield * 100

    def __str__(self):
        return (
            f"\nValuation Metrics:\n"
            f"P/E: {self.pe:.2f} | Forward P/E: {self.forward_pe:.2f} | P/B: {self.pb_ratio:.2f}\n"
            f"Dividend Yield: {self.dividend_yield * 100:.2f}% | Beta: {self.beta:.2f}\n"
            f"EPS (Trailing): {self.eps:.2f} | Target Mean Price: ${self.target_mean_price:,.2f}\n"
            f"Recommendation: {self.recommendation.capitalize()}\n"
        )


class MarketData:
    def __init__(self, data):
        self.current_price = data["currentPrice"]
        self.previous_close = data["previousClose"]
        self.open_price = data["open"]
        self.day_high = data["dayHigh"]
        self.day_low = data["dayLow"]
        self.volume = data["volume"]
        self.fifty_two_week_range = data["fiftyTwoWeekRange"]
        self.market_cap = data["marketCap"]

    def daily_range(self):
        return self.day_high - self.day_low

    def is_bullish(self):
        if self.current_price > self.previous_close:
            return True
        else:
            return False

    def __str__(self):
        return (
            f"\nMarket Data:\n"
            f"Current Price: ${self.current_price:,.2f} | Previous Close: ${self.previous_close:,.2f}\n"
            f"Open: ${self.open_price:,.2f} | Day Range: {self.day_low} - {self.day_high}\n"
            f"52-Week Range: {self.fifty_two_week_range} | Volume: {self.volume:,}\n"
            f"Market Cap: ${self.market_cap / 1_000_000_000_000:.2f}T\n"
        )


class Financials:
    def __init__(self, data):
        self.revenue = data["totalRevenue"]
        self.net_income = data["netIncomeToCommon"]
        self.total_cash = data["totalCash"]
        self.total_debt = data["totalDebt"]
        self.free_cash_flow = data["freeCashflow"]
        self.gross_margin = data["grossMargins"]
        self.operating_margin = data["operatingMargins"]
        self.return_on_equity = data["returnOnEquity"]
        self.return_on_assets = data["returnOnAssets"]
        self.debt_to_equity = data["debtToEquity"]

    def __str__(self):
        return (
            f"\nFinancials:\n"
            f"Revenue: ${self.revenue / 1_000_000_000:.1f}B | Net Income: ${self.net_income / 1_000_000_000:.1f}B\n"
            f"Total Cash: ${self.total_cash / 1_000_000_000:.1f}B | Total Debt: ${self.total_debt / 1_000_000_000:.1f}B\n"
            f"Free Cash Flow: ${self.free_cash_flow / 1_000_000_000:.1f}B\n"
            f"Gross Margin: {self.gross_margin * 100:.1f}% | Operating Margin: {self.operating_margin * 100:.1f}%\n"
            f"ROE: {self.return_on_equity * 100:.1f}% | ROA: {self.return_on_assets * 100:.1f}% | "
            f"Debt/Equity: {self.debt_to_equity:.2f}\n"
        )


class Change:
    def __init__(self, ticker, current_price, days=1):
        self.ticker = ticker
        self.current_price = current_price
        self.current_date = datetime.datetime.now()

    def calculate_change(self, days=1):
        change_price = \
            yf.Ticker(self.ticker).history(start=self.current_date - datetime.timedelta(days), end=self.current_date)[
                'Close'].iloc[0]
        dollar = round(float(self.current_price - change_price), 2)
        percent = round(float((dollar / change_price) * 100), 2)
        return dollar, percent

    def yearly(self):
        return self.calculate_change(365)

    def monthly(self):
        return self.calculate_change(30)

    def six_month(self):
        return self.calculate_change(180)

    def daily(self):
        return self.calculate_change(1)


class History:
    def __init__(self, ticker):
        self.ticker = ticker
        self.current_date = datetime.datetime.now()

    def create_df(self, days=1):
        df = pd.DataFrame(
            yf.download(self.ticker, start=self.current_date - datetime.timedelta(days), end=self.current_date)[
                "Close"])
        return df

    def yearly(self):
        return self.create_df(365)

    def monthly(self):
        return self.create_df(30)

    def six_month(self):
        return self.create_df(180)

    def daily(self):
        return self.create_df(1)

    def get_clean_data(self, days):
        start = self.current_date - datetime.timedelta(days=days)
        # Download full OHLC data
        df = yf.download(self.ticker, start=start, end=self.current_date, progress=False)

        # FIX: If yfinance returns a MultiIndex (common in newer versions), flatten it
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        return df

    def df_1_year(self):
        return self.get_clean_data(365)

    def df_1_month(self):
        return self.get_clean_data(30)
