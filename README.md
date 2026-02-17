# NovaFinance Terminal

**NovaFinance Terminal** is a high-fidelity, full-stack financial management application designed for professional-grade portfolio tracking and technical analysis. Built with a "Slate-Dark" institutional aesthetic, it bridges the gap between raw market data and actionable investment insights using Python's robust data ecosystem.

---

## 🚀 Key Features

* **Multi-Portfolio Architecture**: Initialize and manage distinct investment terminals with dedicated tracking for various strategies.
* **Performance vs. Benchmark**: Automated "Growth of $100" visualization comparing total portfolio performance against the S&P 500 (^GSPC).
* **Technical Analysis Suite**: Dedicated deep-dives for individual assets featuring:
    * **Bollinger Bands**: Shaded volatility areas for trend analysis.
    * **Price/Volume Analysis**: Dual-axis performance tracking.
* **Sector Distribution**: Dynamic donut charts providing instant feedback on portfolio diversification.
* **Fundamental Terminal**: Access to real-time P/E ratios, Beta, Market Cap, and Executive summaries.
* **Secure Authentication**: Full user lifecycle management with encrypted password hashing and session-protected routes.

---

## 🛠️ Technical Stack

* **Backend**: Python 3 / Flask
* **Database**: SQLAlchemy (SQLite) with cascade-delete logic
* **Data Engine**: YFinance API, Pandas, NumPy
* **Frontend**: Jinja2 Templates, Bootstrap 5, Chart.js
* **Visualization**: Matplotlib, Mplfinance (Agg Backend)

---

## 📂 System Architecture

The application is built using a strict Object-Oriented Programming (OOP) approach to ensure data encapsulation and reliability:

* `app.py`: The central Flask controller managing routes and the logic bridge.
* `stock.py`: Encapsulates ticker-level data (Financials, Valuation, MarketData).
* `stockportfolio.py`: The mathematical engine for portfolio-wide history and value aggregation.
* `visuals.py`: Specialized classes for rendering high-density dark-theme charts.

---

## ⚙️ Installation & Setup

1.  **Clone the Repository**
    ```bash
    git clone [https://github.com/Adsrdh/APEX-Finance.git](https://github.com/Adsrdh/APEX-Finance.git)
    cd APEX-Finance
    ```

2.  **Install Dependencies**
    ```bash
    pip install flask flask_sqlalchemy flask_login pandas yfinance matplotlib mplfinance numpy
    ```

3.  **Initialize the Terminal**
    ```python
    # In a Python shell
    from app import db, app
    with app.app_context():
        db.create_all()
    ```

4.  **Launch the App**
    ```bash
    python app.py
    ```
    *Open `http://localhost:5001` in your browser.*

---

## 📈 Future Roadmap

* **RSI Implementation**: Integrating Relative Strength Index indicators into the visuals suite.
* **CSV Batch Import**: Enabling bulk asset uploading via CSV files.
* **Live Streaming**: Transitioning to WebSockets for real-time price updates.

---

**Author**: Aditya Valecha  
**Education**: Ithaca College, Computer Science & Finance
