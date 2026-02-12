import os
import datetime
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash

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
    # Link to portfolios: User can have many
    portfolios = db.relationship("Portfolio", backref="owner", lazy=True)


class Portfolio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # Link to holdings: Portfolio contains many stock tickers/quantities
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
    """Translates DB records into the StockPortfolio logic class."""
    p_logic = StockPortfolio(name=portfolio_db_obj.name)
    for h in portfolio_db_obj.holdings:
        try:
            p_logic.add_stock(h.ticker, h.quantity)
        except Exception as e:
            print(f"Error loading ticker {h.ticker}: {e}")
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
    user_portfolios = current_user.portfolios
    portfolio_totals = {}

    # Calculate values for the Home Card view
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
    """Individual portfolio management page (your previous dashboard view)"""
    active_p_db = Portfolio.query.get_or_404(p_id)
    if active_p_db.user_id != current_user.id:
        return "Unauthorized", 403

    p_logic = build_portfolio_logic(active_p_db)
    return render_template(
        'portfolio_view.html',  # Rename your old portfolio_view.html to this
        portfolio=p_logic,
        active_portfolio_db=active_p_db,
        total_value=p_logic.get_portfolio_value(),
        sector_data=p_logic.holding_by_sector()
    )


@app.route('/initialize_portfolio', methods=['POST'])
@login_required
def initialize_portfolio():
    p_name = request.form.get('name')
    ticker = request.form.get('ticker').upper()
    qty = float(request.form.get('quantity'))

    # 1. Create Portfolio
    new_p = Portfolio(name=p_name, user_id=current_user.id)
    db.session.add(new_p)
    db.session.flush()  # Get the ID before committing

    # 2. Add first stock
    first_holding = Holding(ticker=ticker, quantity=qty, portfolio_id=new_p.id)
    db.session.add(first_holding)
    db.session.commit()

    flash(f"Terminal {p_name} initialized successfully.")
    return redirect(url_for('dashboard'))


@app.route('/add_stock', methods=['POST'])
@login_required
def add_stock():
    p_id = request.form.get('portfolio_id')
    ticker = request.form.get('ticker').upper()
    quantity = float(request.form.get('quantity'))

    existing = Holding.query.filter_by(portfolio_id=p_id, ticker=ticker).first()
    if existing:
        existing.quantity += quantity
    else:
        new_h = Holding(ticker=ticker, quantity=quantity, portfolio_id=p_id)
        db.session.add(new_h)

    db.session.commit()
    return redirect(url_for('dashboard', p_id=p_id))


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5001)