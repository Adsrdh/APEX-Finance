import os
import io
import base64
import datetime
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash

# Logic Imports
from stock import Stock
from stockportfolio import StockPortfolio
from visuals import StockVisuals, PortfolioVisuals

app = Flask(__name__)
app.config['SECRET_KEY'] = 'nova-terminal-secret-2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///portfolio.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

# --- Models ---
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(300), nullable=False)
    portfolios = db.relationship("Portfolio", backref="owner", lazy=True, cascade="all, delete-orphan")

class Portfolio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    holdings = db.relationship("Holding", backref="parent_portfolio", lazy=True, cascade="all, delete-orphan")

class Holding(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticker = db.Column(db.String(10), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolio.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Helpers ---
def build_portfolio_logic(portfolio_db_obj):
    p_logic = StockPortfolio(name=portfolio_db_obj.name)
    for h in portfolio_db_obj.holdings:
        try:
            p_logic.add_stock(h.ticker, h.quantity)
        except: continue
    return p_logic

def get_plot_url():
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight', facecolor='#1e293b')
    img.seek(0)
    url = base64.b64encode(img.getvalue()).decode('utf-8')
    plt.close('all')
    return url

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
    """Main hub showing all portfolios (portfolio_view.html)"""
    user_portfolios = current_user.portfolios
    # We name this portfolio_totals so the HTML template can find it
    portfolio_totals = {p.id: build_portfolio_logic(p).get_portfolio_value() for p in user_portfolios}
    return render_template('portfolio_view.html', portfolios=user_portfolios, portfolio_totals=portfolio_totals)



@app.route('/portfolio/<int:p_id>')
@login_required
def view_portfolio(p_id):
    """Detailed management page for one portfolio (dashboard.html)"""
    p_db = Portfolio.query.get_or_404(p_id)
    if p_db.user_id != current_user.id: return "Unauthorized", 403

    p_logic = build_portfolio_logic(p_db)
    total_val = p_logic.get_portfolio_value()

    # Calculate Day Change
    total_diff = 0
    for s in p_logic.stocks.values():
        diff, _ = s.get_change(period="daily")
        total_diff += (diff * s.get_quantity_held())
    prev_val = total_val - total_diff
    pct_change = round((total_diff / prev_val * 100), 2) if prev_val != 0 else 0

    benchmark_url = None
    try:
        hist = p_logic.get_portfolio_history()
        if not hist.empty:
            vis = PortfolioVisuals(hist)
            vis.create_benchmark_comparison()
            benchmark_url = get_plot_url()
    except:
        pass

    return render_template('dashboard.html', portfolio=p_logic, active_portfolio_db=p_db, total_value=total_val,
                           day_change_pct=pct_change, sector_data=p_logic.holding_by_sector(),
                           benchmark_chart=benchmark_url)


# --- ADDED MISSING ROUTE ---
@app.route('/initialize_portfolio', methods=['POST'])
@login_required
def initialize_portfolio():
    """Creates a new portfolio and redirects back to the hub"""
    name = request.form.get('name')
    ticker = request.form.get('ticker').upper().strip()

    new_p = Portfolio(name=name, user_id=current_user.id)
    db.session.add(new_p)
    db.session.flush()

    try:
        qty = float(request.form.get('quantity'))
        # Use Stock class to validate ticker exists
        Stock(ticker, quantity=0)
        db.session.add(Holding(ticker=ticker, quantity=qty, portfolio_id=new_p.id))
        db.session.commit()
        flash(f"Portfolio {name} created successfully.")
    except Exception as e:
        db.session.rollback()
        flash(f"Initialization error: {str(e)}")

    # Redirect to the 'dashboard' function which loads portfolio_view.html
    return redirect(url_for('dashboard'))

# --- FIXED REDIRECTS FROM 'portfolio_view' TO 'view_portfolio' ---
@app.route('/add_stock', methods=['POST'])
@login_required
def add_stock():
    p_id = request.form.get('portfolio_id')
    ticker_symbol = request.form.get('ticker').upper().strip()
    qty_str = request.form.get('quantity')
    try:
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
    except Exception as e:
        flash(f"Error: {str(e)}")
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
    else:
        try:
            sell_qty = float(qty_input) if qty_input else 0
            if sell_qty >= holding.quantity:
                db.session.delete(holding)
            else:
                holding.quantity -= sell_qty
        except ValueError:
            flash("Invalid quantity.")
    db.session.commit()
    return redirect(url_for('view_portfolio', p_id=p_id))


@app.route('/delete_portfolio/<int:p_id>', methods=['POST'])
@login_required
def delete_portfolio(p_id):
    p = Portfolio.query.get_or_404(p_id)
    # Security: Ensure only the owner can delete
    if p.user_id != current_user.id:
        flash("Unauthorized deletion attempt.")
        return redirect(url_for('dashboard'))

    db.session.delete(p)
    db.session.commit()
    flash(f"Portfolio '{p.name}' and all its assets have been liquidated.")
    return redirect(url_for('dashboard'))


@app.route('/stock/<ticker>')
@login_required
def stock_detail(ticker):
    try:
        stock_obj = Stock(ticker)
        dollar_change, pct_change = stock_obj.get_change(period="daily")
        hist_df = stock_obj.history.yearly()
        visualizer = StockVisuals(hist_df)
        plt.style.use('dark_background')
        visualizer.create_volatility_chart(ticker=ticker)
        bollinger_url = get_plot_url()
        visualizer.create_price_volume_line_chart(ticker=ticker)
        volume_url = get_plot_url()
        return render_template('stock_detail.html', stock=stock_obj, dollar_change=dollar_change,
                               pct_change=pct_change, bollinger_chart=bollinger_url, volume_chart=volume_url)
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