import os
import datetime

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

# ------------------ UPDATED DATABASE MODELS ------------------

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(300), nullable=False)
    # A user can have multiple portfolios
    portfolios = db.relationship("Portfolio", backref="user", lazy=True)

class Portfolio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    holdings = db.relationship("Holding", backref="portfolio", lazy=True)

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

def build_portfolio(portfolio_db_obj):
    """
    Build a StockPortfolio object from a specific Portfolio database entry.
    """
    # Create the logic object from your stockportfolio.py
    portfolio = StockPortfolio(name=portfolio_db_obj.name)

    # Loop through holdings associated with THIS portfolio ID
    for holding in portfolio_db_obj.holdings:
        try:
            portfolio.add_stock(holding.ticker, holding.quantity)
        except Exception as e:
            print(f"Error loading {holding.ticker}: {e}")
            continue

    return portfolio


# ------------------ ROUTES ------------------


@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    # If not logged in, show the login page (which is the new home)
    return render_template('login.html')

# ------------------ AUTH ------------------

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email').lower()
        password = request.form.get('password')

        if User.query.filter_by(email=email).first():
            flash("Email already registered.")
            return redirect(url_for('signup'))

        hashed = generate_password_hash(password)

        user = User(email=email, password=hashed)
        db.session.add(user)
        db.session.commit()

        flash("Account created. Please log in.")
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
        else:
            flash("Invalid credentials.")

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# ------------------ DASHBOARD ------------------

@app.route('/dashboard')
@app.route('/dashboard/<int:p_id>')
@login_required
def dashboard(p_id=None):
    # 1. Get the user's portfolios
    user_portfolios = current_user.portfolios

    # 2. If no portfolios exist, create a default one
    if not user_portfolios:
        default_p = Portfolio(name="My First Portfolio", user_id=current_user.id)
        db.session.add(default_p)
        db.session.commit()
        user_portfolios = [default_p]

    # 3. Select the active portfolio
    active_p_db = next((p for p in user_portfolios if p.id == p_id), user_portfolios[0])

    # 4. Build the logic object for calculations
    portfolio_logic = build_portfolio(active_p_db)

    total_value = portfolio_logic.get_portfolio_value()
    sector_data = portfolio_logic.holding_by_sector()

    return render_template(
        'dashboard.html',
        portfolio=portfolio_logic,  # The logic object
        active_portfolio_db=active_p_db,  # The database object
        total_value=total_value,
        sector_data=sector_data,
        all_portfolios=user_portfolios
    )

# ------------------ STOCK ACTIONS ------------------

@app.route('/add_stock', methods=['POST'])
@login_required
def add_stock():
    ticker = request.form.get('ticker').upper()
    quantity = float(request.form.get('quantity'))

    try:
        existing = Holding.query.filter_by(
            user_id=current_user.id,
            ticker=ticker
        ).first()

        if existing:
            existing.quantity += quantity
        else:
            new_holding = Holding(
                ticker=ticker,
                quantity=quantity,
                user_id=current_user.id
            )
            db.session.add(new_holding)

        db.session.commit()
        flash("Stock added successfully.")

    except Exception as e:
        flash(f"Error adding stock: {e}")

    return redirect(url_for('dashboard'))


@app.route('/remove_stock/<int:holding_id>', methods=['POST'])
@login_required
def remove_stock(holding_id):
    holding = Holding.query.get_or_404(holding_id)

    if holding.user_id != current_user.id:
        flash("Unauthorized action.")
        return redirect(url_for('dashboard'))

    db.session.delete(holding)
    db.session.commit()
    flash("Stock removed.")

    return redirect(url_for('dashboard'))


# ------------------ MAIN ------------------

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True,host='0.0.0.0',port=5001)
