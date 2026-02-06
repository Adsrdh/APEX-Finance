import matplotlib.pyplot as plt
import mplfinance as mpf
import pandas as pd


class PortfolioVisuals:
    def __init__(self, data):
        self.data = data

    def create_pie_chart(self):
        if not self.data or sum(self.data.values()) == 0:
            print("⚠️ No portfolio data available for Pie Chart.")
            return

        try:
            labels = list(self.data.keys())
            values = list(self.data.values())
            fig, ax = plt.subplots(figsize=(8, 8))
            ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=140)
            ax.set_title("Sector Distribution")
            plt.show()
        except Exception as e:
            print(f"❌ Error rendering Pie Chart: {e}")

    def create_benchmark_comparison(self, benchmark_ticker="^GSPC"):
        if self.data is None or self.data.empty or 'TotalValue' not in self.data.columns:
            print("⚠️ Insufficient history for benchmark comparison.")
            return

        try:
            import yfinance as yf
            port_hist = self.data['TotalValue']

            # Fetch benchmark with timeout protection
            bench_df = yf.download(benchmark_ticker, start=port_hist.index.min(),
                                   end=port_hist.index.max(), progress=False)

            if bench_df.empty:
                print(f"⚠️ Could not fetch benchmark data for {benchmark_ticker}")
                return

            bench = bench_df['Close']
            if isinstance(bench, pd.DataFrame):
                bench = bench.iloc[:, 0]

            # Reindex benchmark to match portfolio dates to avoid NaN gaps
            bench = bench.reindex(port_hist.index).ffill()

            # Normalize and handle division by zero
            port_start = port_hist.iloc[0]
            bench_start = bench.iloc[0]

            if port_start == 0 or bench_start == 0:
                print("⚠️ Start value is zero, cannot normalize.")
                return

            port_norm = (port_hist / port_start) * 100
            bench_norm = (bench / bench_start) * 100

            plt.figure(figsize=(12, 6))
            plt.plot(port_norm.index, port_norm, label='Portfolio', color='#007bff')
            plt.plot(bench_norm.index, bench_norm, label='S&P 500', color='orange', linestyle='--')
            plt.title(f"Portfolio vs {benchmark_ticker} (Growth of $100)")
            plt.ylabel("Value")
            plt.legend()
            plt.grid(True, alpha=0.3)
            plt.show()
        except Exception as e:
            print(f"❌ Error rendering Benchmark Chart: {e}")

    def create_risk_reward_scatter(self):
        if not self.data or len(self.data) < 1:
            print("⚠️ Not enough stock data for Risk-Reward scatter.")
            return

        try:
            tickers = [s.get('ticker', 'Unknown') for s in self.data]
            vols = [s.get('vol', 0) for s in self.data]
            returns = [s.get('return', 0) for s in self.data]
            sharpes = [s.get('sharpe', 0) for s in self.data]

            plt.figure(figsize=(10, 6))
            scatter = plt.scatter(vols, returns, c=sharpes, cmap='RdYlGn', s=100, edgecolors='black')

            for i, txt in enumerate(tickers):
                plt.annotate(txt, (vols[i], returns[i]), xytext=(5, 5), textcoords='offset points')

            plt.colorbar(scatter, label='Sharpe Ratio')
            plt.xlabel('Risk (Volatility)')
            plt.ylabel('Return (Annualized)')
            plt.title('Portfolio Risk-Reward Analysis')
            plt.axhline(0, color='black', alpha=0.2)
            plt.axvline(0, color='black', alpha=0.2)
            plt.show()
        except Exception as e:
            print(f"❌ Error rendering Scatter Plot: {e}")


class StockVisuals:
    def __init__(self, data):
        self.data = data

    def _validate_data(self):
        """Internal helper to check if data is valid for plotting."""
        if self.data is None or self.data.empty:
            print("⚠️ No data available to plot.")
            return False
        if 'Close' not in self.data.columns:
            print("⚠️ Data is missing 'Close' column.")
            return False
        return True

    def create_line_graph(self):
        if not self._validate_data():
            return

        try:
            df = self.data['Close'].copy()
            fig, ax = plt.subplots(figsize=(10, 6))
            df.plot(ax=ax, color='#007bff')
            ax.set_title("Stock Closing Prices")
            ax.set_ylabel("Price (USD)")
            ax.grid(True, alpha=0.3)
            plt.show()
        except Exception as e:
            print(f"❌ Error in Line Graph: {e}")

    def create_volatility_chart(self, ticker="Stock"):
        if not self._validate_data() or len(self.data) < 20:
            print("⚠️ Need at least 20 days of data for Volatility Chart.")
            return

        try:
            df = self.data.copy()
            df['SMA'] = df['Close'].rolling(window=20).mean()
            df['STD'] = df['Close'].rolling(window=20).std()
            df['Upper'] = df['SMA'] + (df['STD'] * 2)
            df['Lower'] = df['SMA'] - (df['STD'] * 2)

            # Drop NaN rows for cleaner mpf plotting
            df = df.dropna()

            apds = [
                mpf.make_addplot(df['Upper'], color='#B8860B', width=1.0),
                mpf.make_addplot(df['Lower'], color='#B8860B', width=1.0),
                mpf.make_addplot(df['SMA'], color='#808080', width=0.8, alpha=0.5)
            ]

            mpf.plot(df, type='candle', style='charles', addplot=apds,
                     fill_between=dict(y1=df['Lower'].values, y2=df['Upper'].values, color='gray', alpha=0.1),
                     title=f"{ticker} Volatility (Bollinger Bands)",
                     ylabel='Price (USD)', tight_layout=True)
        except Exception as e:
            print(f"❌ Error in Volatility Chart: {e}")

    def create_price_volume_line_chart(self, ticker="Stock"):
        if not self._validate_data() or 'Volume' not in self.data.columns:
            print("⚠️ Missing Price or Volume data.")
            return

        try:
            df = self.data.copy()
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True,
                                           gridspec_kw={'height_ratios': [3, 1]})

            ax1.plot(df.index, df['Close'], color='#007bff', linewidth=1.5)
            ax1.fill_between(df.index, df['Close'], df['Close'].min() * 0.98, alpha=0.1)
            ax1.set_title(f"{ticker} Performance")
            ax1.set_ylabel("Price ($)")

            # Volume coloring logic
            diff = df['Close'].diff().fillna(0)
            colors = ['green' if d >= 0 else 'red' for d in diff]
            ax2.bar(df.index, df['Volume'], color=colors, alpha=0.5)
            ax2.set_ylabel("Volume")

            plt.subplots_adjust(hspace=0.05)
            plt.gcf().autofmt_xdate()
            plt.show()
        except Exception as e:
            print(f"❌ Error in Price/Volume Chart: {e}")
