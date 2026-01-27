import matplotlib.pyplot as plt
import pandas as pd
import mplfinance as mpf


class PortfolioVisuals:

    def __init__(self, data):
        self.data = data

    def create_pie_chart(self):  # data is dictionary
        labels = list(self.data.keys())
        values = list(self.data.values())

        fig, ax = plt.subplots()
        ax.pie(values, labels=labels)
        plt.show()


class StockVisuals:
    def __init__(self, data):
        self.data = data

    def create_line_graph(self):  # data is Pandas dataframe
        df = self.data.copy()
        df = df['Close']
        fig, ax = plt.subplots(figsize=(10, 6))
        df.plot(ax=ax)

        ax.set_title("Stock Closing Prices")
        ax.set_xlabel("Date")
        ax.set_ylabel("Price (USD)")
        plt.show()

    def create_volatility_chart(self, ticker="Stock"):
        df = self.data.copy()

        # 1. Calculate Bollinger Bands
        # Standard period of 20, with 2 standard deviations
        df['SMA'] = df['Close'].rolling(window=20).mean()
        df['STD'] = df['Close'].rolling(window=20).std()
        df['Upper'] = df['SMA'] + (df['STD'] * 2)
        df['Lower'] = df['SMA'] - (df['STD'] * 2)

        # 2. Logic for Overbought/Oversold Markers
        # We only want to label a few points so the chart isn't messy
        df['Marker'] = None
        for i in range(len(df)):
            if df['Close'].iloc[i] > df['Upper'].iloc[i]:
                df.at[df.index[i], 'Marker'] = df['High'].iloc[i] * 1.02  # Point above
            elif df['Close'].iloc[i] < df['Lower'].iloc[i]:
                df.at[df.index[i], 'Marker'] = df['Low'].iloc[i] * 0.98  # Point below

        # 3. Define the Plotting Elements (Add-ons)
        # Gold lines for the bands and a shaded region
        apds = [
            mpf.make_addplot(df['Upper'], color='#B8860B', width=1.5),  # DarkGold
            mpf.make_addplot(df['Lower'], color='#B8860B', width=1.5),
            mpf.make_addplot(df['SMA'], color='#808080', width=0.8, alpha=0.5)  # Middle line
        ]

        # 4. Create the Plot
        # 'charles' is the theme for green/red candles
        # 'fill_between' creates that gray cloud effect
        fig, axlist = mpf.plot(
            df,
            type='candle',
            style='charles',
            addplot=apds,
            fill_between=dict(y1=df['Lower'].values, y2=df['Upper'].values, color='gray', alpha=0.1),
            title=f"\n{ticker} Volatility Analysis",
            ylabel='Price (USD)',
            volume=False,
            tight_layout=True,
            datetime_format='%b %Y',
            returnfig=True,
            figscale=1.2
        )

        # 5. Add Custom Text Labels (Overbought/Oversold)
        # We find where markers exist and draw the little boxes from your image
        ax = axlist[0]
        for i in range(len(df)):
            if df['Close'].iloc[i] > df['Upper'].iloc[i] and i % 5 == 0:  # label every 5th to avoid clutter
                ax.text(i, df['High'].iloc[i], 'Overbought', fontsize=8, color='white',
                        bbox=dict(facecolor='#FF4500', alpha=0.8, boxstyle='round,pad=0.3'))
            elif df['Close'].iloc[i] < df['Lower'].iloc[i] and i % 5 == 0:
                ax.text(i, df['Low'].iloc[i], 'Oversold', fontsize=8, color='white',
                        bbox=dict(facecolor='#1E90FF', alpha=0.8, boxstyle='round,pad=0.3'))

        plt.show()

    def create_rsi_analysis(self):
        df = self.data.copy()

        # 1. Calculate RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))

        # 2. Setup Subplots (2 Rows: Price/Volume and RSI)
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), gridspec_kw={'height_ratios': [3, 1]})

        # Top Plot: Price and Moving Averages
        ax1.plot(df.index, df['Close'], label='Price', color='black', alpha=0.7)
        ax1.set_title(f"Advanced Analysis")
        ax1.legend(loc='upper left')
        ax1.grid(True, alpha=0.3)

        # Bottom Plot: RSI
        ax2.plot(df.index, df['RSI'], label='RSI (14)', color='purple')
        ax2.axhline(70, color='red', linestyle='--', alpha=0.5)  # Overbought line
        ax2.axhline(30, color='green', linestyle='--', alpha=0.5)  # Oversold line
        ax2.set_ylim(0, 100)
        ax2.set_ylabel('RSI')
        ax2.legend(loc='upper left')

        plt.tight_layout()
        plt.show()
    def create_price_volume_line_chart(self, ticker="Stock"):
        df = self.data.copy()

        # 1. Setup the figure with two rows (Price on top, Volume on bottom)
        # sharex=True ensures that zooming/panning on one chart moves the other
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True,
                                       gridspec_kw={'height_ratios': [3, 1]})

        # --- TOP PLOT: PRICE ---
        ax1.plot(df.index, df['Close'], color='#007bff', linewidth=2, label='Price')
        ax1.fill_between(df.index, df['Close'], df['Close'].min() * 0.99, color='#007bff', alpha=0.1)

        ax1.set_title(f"{ticker} Performance & Volume", fontsize=14, pad=15)
        ax1.set_ylabel('Price (USD)', fontweight='bold')
        ax1.grid(True, linestyle=':', alpha=0.6)
        ax1.legend(loc='upper left')

        # --- BOTTOM PLOT: VOLUME ---
        # Color-code: Green if price increased from yesterday, Red if it decreased
        price_diff = df['Close'].diff()
        colors = ['green' if diff >= 0 else 'red' for diff in price_diff]
        if len(colors) > 0: colors[0] = 'green'  # Default first bar

        ax2.bar(df.index, df['Volume'], color=colors, alpha=0.6, width=0.8)

        ax2.set_ylabel('Volume', fontweight='bold')
        ax2.grid(True, linestyle=':', alpha=0.4)

        # Clean up date formatting
        fig.autofmt_xdate()

        plt.tight_layout()
        # Adjust space between subplots to be minimal
        plt.subplots_adjust(hspace=0.05)
        plt.show()