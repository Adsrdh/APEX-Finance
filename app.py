import os
import datetime
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from stock import Stock
from visuals import StockVisuals, PortfolioVisuals
from utils import get_plot_url
import io
import base64
import matplotlib
matplotlib.use('Agg') # Required for non-GUI backend
import matplotlib.pyplot as plt
from stockportfolio import StockPortfolio

# ------------------ APP CONFIG ------------------
app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///portfolio.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"


# ------------------ DATABASE MODELS ------------------

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(300), nullable=False)
    portfolios = db.relationship("Portfolio", backref="owner", lazy=True)


class Portfolio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    holdings = db.relationship("Holding", backref="parent_portfolio", lazy=True)


class Holding(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticker = db.Column(db.String(10), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolio.id'), nullable=False)


# ------------------ LOGIN MANAGER ------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ------------------ HELPER FUNCTIONS ------------------
def build_portfolio_logic(portfolio_db_obj):
    """
    Translates DB records into your StockPortfolio logic class.
    This creates the active Stock objects that fetch yfinance data.
    """
    p_logic = StockPortfolio(name=portfolio_db_obj.name)
    for h in portfolio_db_obj.holdings:
        try:
            p_logic.add_stock(h.ticker, h.quantity)
        except Exception as e:
            print(f"Error loading {h.ticker}: {e}")
            continue
    return p_logic


# ------------------ ROUTES ------------------

@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email').lower()
        password = request.form.get('password')

        if User.query.filter_by(email=email).first():
            flash("An Account already exists for this email.")
            return redirect(url_for('signup'))

        user = User(email=email, password=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()

        flash("Secure access established. Please log in.")
        return redirect(url_for('login'))
    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email').lower()
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash("Invalid credentials.")
    return render_template('login.html')


@app.route('/dashboard')
@login_required
def dashboard():
    """
    Main landing page showing all portfolios.
    Uses portfolio_view.html as requested.
    """
    user_portfolios = current_user.portfolios
    portfolio_totals = {}

    for p in user_portfolios:
        logic = build_portfolio_logic(p)
        portfolio_totals[p.id] = logic.get_portfolio_value()

    return render_template(
        'portfolio_view.html',
        all_portfolios=user_portfolios,
        portfolio_totals=portfolio_totals
    )


@app.route('/portfolio/<int:p_id>')
@login_required
def view_portfolio(p_id):
    """
    Individual portfolio management page.
    Uses dashboard.html as requested.
    """
    active_p_db = Portfolio.query.get_or_404(p_id)
    if active_p_db.user_id != current_user.id:
        return "Unauthorized", 403

    # 1. Initialize your Logic Engine
    p_logic = build_portfolio_logic(active_p_db)

    # 2. Use your Logic Engine to get data for the UI
    total_val = p_logic.get_portfolio_value()
    sector_dist = p_logic.holding_by_sector()

    # 3. Calculate Portfolio-wide Day Change using your Change class logic
    total_dollar_change = 0
    for stock in p_logic.stocks.values():
        dollar_change, _ = stock.get_change(period="daily")
        total_dollar_change += (dollar_change * stock.get_quantity_held())

    # Calculate weighted percentage change
    previous_total_val = total_val - total_dollar_change
    day_change_pct = round((total_dollar_change / previous_total_val * 100), 2) if previous_total_val != 0 else 0

    return render_template(
        'dashboard.html',
        portfolio=p_logic,
        active_portfolio_db=active_p_db,
        total_value=total_val,
        day_change_pct=day_change_pct,
        sector_data=sector_dist
    )


@app.route('/initialize_portfolio', methods=['POST'])
@login_required
def initialize_portfolio():
    """Combined route for manual creation or CSV import."""
    p_name = request.form.get('name')
    ticker = request.form.get('ticker')
    qty_str = request.form.get('quantity')
    file = request.files.get('file')

    # 1. Create Portfolio record
    new_p = Portfolio(name=p_name, user_id=current_user.id)
    db.session.add(new_p)
    db.session.flush()

    # 2. Handle Data Source
    if file and file.filename.endswith('.csv'):
        try:
            df = pd.read_csv(file)
            df.columns = [c.lower().strip() for c in df.columns]
            for _, row in df.iterrows():
                new_h = Holding(ticker=str(row['ticker']).upper(), quantity=float(row['quantity']), portfolio_id=new_p.id)
                db.session.add(new_h)
            db.session.commit()
            flash(f"Portfolio {p_name} initialized via CSV.")
        except Exception as e:
            flash(f"CSV Parse Error: {e}")
            return redirect(url_for('dashboard'))
    elif ticker and qty_str:
        try:
            new_h = Holding(ticker=ticker.upper(), quantity=float(qty_str), portfolio_id=new_p.id)
            db.session.add(new_h)
            db.session.commit()
            flash(f"Portfolio {p_name} initialized successfully.")
        except ValueError:
            flash("Invalid quantity entered.")
    else:
        db.session.commit()
        flash(f"Empty Portfolio {p_name} created.")

    return redirect(url_for('dashboard'))


@app.route('/add_stock', methods=['POST'])
@login_required
def add_stock():
    p_id = request.form.get('portfolio_id')
    ticker_symbol = request.form.get('ticker').upper().strip()
    qty_str = request.form.get('quantity')

    try:
        # 1. Validation using your Stock class (from Stock.py)
        # This will raise a ValueError if the ticker is invalid
        temp_stock = Stock(ticker_symbol, quantity=0)

        quantity = float(qty_str)

        existing = Holding.query.filter_by(portfolio_id=p_id, ticker=ticker_symbol).first()
        if existing:
            existing.quantity += quantity
        else:
            new_h = Holding(ticker=ticker_symbol, quantity=quantity, portfolio_id=p_id)
            db.session.add(new_h)

        db.session.commit()
        flash(f"Verified and added {ticker_symbol}.")
    except (ValueError, ConnectionError) as e:
        flash(f"Invalid Ticker: {str(e)}")
    except Exception as e:
        flash("An error occurred during addition.")

    return redirect(url_for('view_portfolio', p_id=p_id))


@app.route('/sell_stock', methods=['POST'])
@login_required
def sell_stock():
    holding_id = request.form.get('holding_id')
    sell_all = request.form.get('sell_all') == 'true'
    qty_input = request.form.get('quantity')

    holding = Holding.query.get_or_404(holding_id)
    p_id = holding.portfolio_id

    if sell_all:
        db.session.delete(holding)
        flash("Position liquidated.")
    else:
        try:
            # Ensure we can convert to float only if we aren't selling all
            sell_qty = float(qty_input) if qty_input else 0
            if sell_qty >= holding.quantity:
                db.session.delete(holding)
            else:
                holding.quantity -= sell_qty
            flash("Portfolio updated.")
        except ValueError:
            flash("Please enter a valid quantity.")

    db.session.commit()
    return redirect(url_for('view_portfolio', p_id=p_id))


def get_plot_url():
    img = io.BytesIO()
    # Set facecolor to match your --surface-slate (#1e293b)
    plt.savefig(img, format='png', bbox_inches='tight', facecolor='#1e293b')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode('utf-8')
    plt.close()
    return plot_url


@app.route('/stock/<ticker>')
@login_required
def stock_detail(ticker):
    try:
        stock_obj = Stock(ticker)
        dollar_change, pct_change = stock_obj.get_change(period="daily")

        # Initialize Visuals with yearly data
        hist_df = stock_obj.history.yearly()
        visualizer = StockVisuals(hist_df)

        # Apply dark styling globally for the session
        plt.style.use('dark_background')

        # Generate Bollinger Chart
        visualizer.create_volatility_chart(ticker=ticker)
        bollinger_url = get_plot_url()

        # Generate Price/Volume Chart
        visualizer.create_price_volume_line_chart(ticker=ticker)
        volume_url = get_plot_url()

        return render_template(
            'stock_detail.html',
            stock=stock_obj,
            dollar_change=dollar_change,
            pct_change=pct_change,
            bollinger_chart=bollinger_url,
            volume_chart=volume_url
        )
    except Exception as e:
        flash(f"Error loading visuals: {e}")
        return redirect(url_for('dashboard'))
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5001)