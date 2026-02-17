import matplotlib.pyplot as plt
import mplfinance as mpf
import pandas as pd

def apply_dark_style():
    """Applies NovaFinance Dark Theme to all Matplotlib plots."""
    plt.style.use('dark_background')
    plt.rcParams.update({
        'axes.facecolor': '#1e293b',  # Match surface-slate
        'figure.facecolor': '#1e293b',
        'axes.edgecolor': '#334155',
        'grid.color': '#334155',
        'text.color': 'white'
    })

class PortfolioVisuals:
    def __init__(self, data):
        self.data = data

    def create_benchmark_comparison(self, benchmark_ticker="^GSPC"):
        apply_dark_style()
        if self.data is None or self.data.empty or 'TotalValue' not in self.data.columns:
            return
        try:
            import yfinance as yf
            port_hist = self.data['TotalValue']
            bench_df = yf.download(benchmark_ticker, start=port_hist.index.min(), end=port_hist.index.max(), progress=False)
            if bench_df.empty: return
            bench = bench_df['Close'].reindex(port_hist.index).ffill()
            port_norm = (port_hist / port_hist.iloc[0]) * 100
            bench_norm = (bench / bench.iloc[0]) * 100
            plt.figure(figsize=(12, 6))
            plt.plot(port_norm.index, port_norm, label='Portfolio', color='#3b82f6', linewidth=2)
            plt.plot(bench_norm.index, bench_norm, label='S&P 500', color='#94a3b8', linestyle='--')
            plt.title(f"Portfolio vs {benchmark_ticker} (Growth of $100)")
            plt.legend()
            plt.grid(True, alpha=0.1)
        except Exception: pass

class StockVisuals:
    def __init__(self, data):
        self.data = data

    def create_volatility_chart(self, ticker="Stock"):
        """Neat and tidy Bollinger Bands with shaded volatility areas."""
        apply_dark_style()
        if self.data is None or self.data.empty or 'Close' not in self.data.columns or len(self.data) < 20:
            return

        try:
            df = self.data.copy()
            df['SMA'] = df['Close'].rolling(window=20).mean()
            df['STD'] = df['Close'].rolling(window=20).std()
            df['Upper'] = df['SMA'] + (df['STD'] * 2)
            df['Lower'] = df['SMA'] - (df['STD'] * 2)
            df = df.dropna()

            # Custom Style for clean look
            mc = mpf.make_marketcolors(up='#10b981', down='#ef4444', inherit=True)
            s  = mpf.make_mpf_style(base_mpl_style='dark_background', facecolor='#1e293b', marketcolors=mc)

            apds = [
                mpf.make_addplot(df['Upper'], color='#f59e0b', width=0.8, alpha=0.5),
                mpf.make_addplot(df['Lower'], color='#f59e0b', width=0.8, alpha=0.5),
                mpf.make_addplot(df['SMA'], color='#3b82f6', width=0.8, linestyle='dashed')
            ]

            mpf.plot(df, type='candle', style=s, addplot=apds,
                     fill_between=dict(y1=df['Lower'].values, y2=df['Upper'].values, color='#f59e0b', alpha=0.05),
                     title=f"{ticker} Volatility Terminal",
                     ylabel='Price (USD)', tight_layout=True, figratio=(12, 7))
        except Exception: pass

    def create_price_volume_line_chart(self, ticker="Stock"):
        apply_dark_style()
        if self.data is None or self.data.empty or 'Close' not in self.data.columns:
            return
        try:
            df = self.data.copy()
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True, gridspec_kw={'height_ratios': [3, 1]})
            ax1.plot(df.index, df['Close'], color='#3b82f6')
            ax1.set_title(f"{ticker} Performance")
            diff = df['Close'].diff().fillna(0)
            colors = ['#10b981' if d >= 0 else '#ef4444' for d in diff]
            ax2.bar(df.index, df['Volume'], color=colors, alpha=0.5)
        except Exception: pass