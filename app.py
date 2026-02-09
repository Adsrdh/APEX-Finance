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


# ------------------ DATABASE MODELS ------------------


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.DateTime, default=datetime.datetime.now)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(300), nullable=False)

    holdings = db.relationship("Holding", backref="owner", lazy=True)


class Holding(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticker = db.Column(db.String(10), nullable=False)
    quantity = db.Column(db.Float, nullable=False, default=0)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


# ------------------ LOGIN MANAGER ------------------

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ------------------ HELPER FUNCTIONS ------------------

def build_portfolio(user):
    """
    Build a StockPortfolio object from DB holdings.
    """
    portfolio = StockPortfolio(name=f"{user.email}'s Portfolio")

    for holding in user.holdings:
        try:
            portfolio.add_stock(holding.ticker, holding.quantity)
        except Exception:
            continue

    return portfolio


# ------------------ ROUTES ------------------


@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
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
@login_required
def dashboard():
    portfolio = build_portfolio(current_user)

    total_value = portfolio.get_portfolio_value()
    sector_data = portfolio.holding_by_sector()

    return render_template(
        'dashboard.html',
        portfolio=portfolio,
        total_value=total_value,
        sector_data=sector_data,
        holdings=current_user.holdings
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
    app.run(debug=True)
