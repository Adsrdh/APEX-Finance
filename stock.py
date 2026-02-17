import yfinance as yf
import datetime
import pandas as pd
import numpy as np


class Stock:
    def __init__(self, ticker_symbol, quantity=1):
        self.ticker_symbol = ticker_symbol.upper()
        self._quantity_held = max(0, quantity)  # Ensure non-negative quantity

        # 1. API CONNECTION & VALIDATION
        ticker_obj = yf.Ticker(self.ticker_symbol)
        try:
            data = ticker_obj.info
            # Check for empty data or missing price (indicates invalid ticker)
            if not data or not any(k in data for k in ['currentPrice', 'regularMarketPrice', 'navPrice']):
                raise ValueError(f"Ticker '{self.ticker_symbol}' is invalid or has no market data.")
        except Exception as e:
            raise ConnectionError(f"Failed to fetch data for {self.ticker_symbol}: {str(e)}")

        # 2. DATA ENCAPSULATION WITH FALLBACKS
        self.company_info = CompanyInfo(data)
        self.valuation = ValuationMetrics(data)
        self.market_data = MarketData(data)
        self.financials = Financials(data)

        # 3. COMPONENT CLASSES
        self.change = Change(self.ticker_symbol, self.market_data.current_price)
        self.history = History(self.ticker_symbol)

        # 4. RISK METRICS VALIDATION
        try:
            hist_df = self.history.yearly()
            if hist_df is not None and not hist_df.empty:
                self.risk_metrics = RiskMetrics(hist_df, self.valuation.beta)
            else:
                self.risk_metrics = None
        except Exception:
            self.risk_metrics = None

    def get_quantity_held(self):
        return self._quantity_held

    def increase_quantity(self, amount):
        if amount <= 0:
            raise ValueError("Amount to increase must be positive.")
        self._quantity_held += amount

    def decrease_quantity(self, amount):
        if amount > self._quantity_held:
            raise ValueError("Insufficient quantity held.")
        if amount <= 0:
            raise ValueError("Amount to decrease must be positive.")
        self._quantity_held -= amount

    def get_total_value(self):
        return self.market_data.current_price * self._quantity_held

    def refresh_data(self):
        try:
            data = yf.Ticker(self.ticker_symbol).info
            self.company_info = CompanyInfo(data)
            self.valuation = ValuationMetrics(data)
            self.market_data = MarketData(data)
            self.financials = Financials(data)
        except Exception as e:
            print(f"Refresh failed for {self.ticker_symbol}: {e}")

    # Gateway methods with try-except to prevent crashing during calculation
    def get_change(self, period="daily"):
        try:
            period = str(period).lower()
            mapping = {"daily": 1, "monthly": 30, "six_month": 180, "yearly": 365}
            days = mapping.get(period, int(period) if period.isdigit() else 1)
            return self.change.calculate_change(days)
        except Exception:
            return 0.0, 0.0

    def get_historical_data(self, period="daily"):
        try:
            period = str(period).lower()
            if period == "daily":
                return self.history.daily()
            if period == "monthly":
                return self.history.monthly()
            if period == "six_month":
                return self.history.six_month()
            if period == "yearly":
                return self.history.yearly()
            return self.history.get_days(int(period))
        except Exception:
            return pd.DataFrame()


class CompanyInfo:
    def __init__(self, data):
        self.name = data.get("longName", "N/A")
        self.sector = data.get("sector", "N/A")
        self.industry = data.get("industry", "N/A")
        self.phone = data.get("phone", "N/A")
        self.summary = data.get("longBusinessSummary", "No summary available.")
        self.website = data.get("website", "N/A")
        self.employees = data.get("fullTimeEmployees", "N/A")
        self.executive_board = ExecutiveBoard(data.get("companyOfficers", []))
        self.address = Address(data)


class ExecutiveBoard:
    def __init__(self, executive_member_data):
        # Handle case where executive_member_data is None or empty
        if not executive_member_data:
            self.executive_board = []
        else:
            self.executive_board = [ExecutiveMember(member) for member in executive_member_data]


class ExecutiveMember:
    def __init__(self, member):
        self.name = member.get("name", "N/A")
        self.title = member.get("title", "N/A")
        self.age = member.get("age", "N/A")
        self.pay = member.get("totalPay", "N/A")


class Address:
    def __init__(self, data):
        self.line1 = data.get("address1", "N/A")
        self.city = data.get("city", "N/A")
        self.state = data.get("state", "N/A")
        self.country = data.get("country", "N/A")
        self.zip = data.get("zip", "N/A")

    def __str__(self):
        return f"{self.line1}, {self.city}, {self.country}"


class ValuationMetrics:
    def __init__(self, data):
        self.pe = data.get("trailingPE")
        self.forward_pe = data.get("forwardPE")
        self.pb_ratio = data.get("priceToBook")
        self.dividend_yield = data.get("dividendYield", 0)
        self.beta = data.get("beta", 1.0)  # Default to market beta
        self.eps = data.get("trailingEps")
        self.target_mean_price = data.get("targetMeanPrice")
        self.recommendation = data.get("recommendationKey", "N/A")


class MarketData:
    def __init__(self, data):
        # Pick the most reliable price source available
        self.current_price = data.get("currentPrice") or data.get("regularMarketPrice") or data.get("navPrice") or 0.0
        self.previous_close = data.get("previousClose", self.current_price)
        self.open_price = data.get("open", self.current_price)
        self.day_high = data.get("dayHigh", self.current_price)
        self.day_low = data.get("dayLow", self.current_price)
        self.volume = data.get("volume", 0)
        self.fifty_two_week_range = data.get("fiftyTwoWeekRange", "N/A")
        self.market_cap = data.get("marketCap", 0)


class Financials:
    def __init__(self, data):
        # Convert all to floats/ints or default to 0
        self.revenue = data.get("totalRevenue", 0)
        self.net_income = data.get("netIncomeToCommon", 0)
        self.total_cash = data.get("totalCash", 0)
        self.total_debt = data.get("totalDebt", 0)
        self.free_cash_flow = data.get("freeCashflow", 0)
        self.gross_margin = data.get("grossMargins", 0)
        self.operating_margin = data.get("operatingMargins", 0)
        self.return_on_equity = data.get("returnOnEquity", 0)
        self.return_on_assets = data.get("returnOnAssets", 0)
        self.debt_to_equity = data.get("debtToEquity", 0)


class Change:
    def __init__(self, ticker, current_price):
        self.ticker = ticker
        self.current_price = current_price

    def calculate_change(self, days=1):
        try:
            # period="max" or "2y" is safer to ensure we find enough data
            ticker_obj = yf.Ticker(self.ticker)
            hist = ticker_obj.history(period="2y")
            if hist.empty or len(hist) < 2:
                return 0.0, 0.0

            # Find the closest date available
            idx = -min(days + 1, len(hist))
            start_price = hist['Close'].iloc[idx]

            dollar = round(float(self.current_price - start_price), 2)
            percent = round(float((dollar / start_price) * 100), 2) if start_price != 0 else 0.0
            return dollar, percent
        except Exception:
            return 0.0, 0.0


class History:
    def __init__(self, ticker):
        self.ticker = ticker

    def create_df(self, days):
        try:
            end = datetime.datetime.now()
            start = end - datetime.timedelta(days=days)
            df = yf.download(self.ticker, start=start, end=end, progress=False)

            if df.empty:
                return pd.DataFrame()

            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            df.index.name = 'Date'
            return df
        except Exception:
            return pd.DataFrame()

    def daily(self):
        return self.create_df(5)

    def monthly(self):
        return self.create_df(30)

    def six_month(self):
        return self.create_df(180)

    def yearly(self):
        return self.create_df(365)

    def get_days(self, days):
        return self.create_df(days)


class RiskMetrics:
    def __init__(self, history_df, beta):
        self.df = history_df
        self.beta = beta if (beta is not None and beta != 0) else 1.0

        if not self.df.empty and 'Close' in self.df.columns:
            self.returns = self.df['Close'].pct_change().fillna(0)
        else:
            self.returns = pd.Series(dtype='float64')

    def get_annualized_return(self):
        if self.returns.empty:
            return 0.0
        return float(self.returns.mean() * 252)

    def get_annualized_volatility(self):
        if self.returns.empty:
            return 0.0
        return float(self.returns.std() * (252 ** 0.5))

    def get_sharpe_ratio(self, rf=0.04):
        vol = self.get_annualized_volatility()
        if vol == 0 or np.isnan(vol):
            return 0.0
        return (self.get_annualized_return() - rf) / vol

    def get_treynor_ratio(self, rf=0.04):
        if self.beta == 0 or np.isnan(self.beta):
            return 0.0
        return (self.get_annualized_return() - rf) / self.beta

    def get_daily_sharpe_series(self, rf_daily=0.00016):
        if len(self.returns) < 20:
            return pd.Series(dtype='float64')
        rolling_return = self.returns.rolling(window=20).mean()
        rolling_std = self.returns.rolling(window=20).std()

        # Avoid division by zero in series
        daily_sharpe = (rolling_return - rf_daily) / rolling_std.replace(0, np.inf)
        return daily_sharpe.replace([np.inf, -np.inf], 0).dropna()