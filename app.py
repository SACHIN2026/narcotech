from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from reportlab.pdfgen import canvas
from io import BytesIO
import random

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'your_secret_key'
db = SQLAlchemy(app)


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product = db.Column(db.String(100))
    amount = db.Column(db.Float)
    wallet = db.Column(db.String(100))
    date = db.Column(db.DateTime, default=datetime.utcnow)


with app.app_context():
    db.create_all()


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('admin'))


@app.route('/download_pdf')
def download_pdf():
    download_type = request.args.get('type', 'all')

    if download_type == 'latest':
        transactions = [Transaction.query.order_by(
            Transaction.id.desc()).first()]
    else:
        transactions = Transaction.query.all()

    buffer = BytesIO()
    p = canvas.Canvas(buffer)
    p.setFont("Helvetica-Bold", 16)

    # Add header
    p.drawString(50, 800, "NarcoTech Transaction Report")
    p.setFont("Helvetica", 12)
    p.drawString(
        50, 780, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    # Pagination settings
    y = 740  # Initial y-position for content
    transactions_per_page = 6  # Number of transactions per page
    count = 0  # Track transactions per page

    for t in transactions:
        if count >= transactions_per_page:  # If the page limit is reached, create a new page
            p.showPage()  # Move to the next page
            p.setFont("Helvetica", 12)
            y = 800  # Reset y-position
            count = 0  # Reset count

        # Print transaction details
        p.drawString(50, y, f"Date: {t.date.strftime('%Y-%m-%d %H:%M')}")
        p.drawString(50, y-20, f"Product: {t.product}")
        p.drawString(50, y-40, f"Amount: {t.amount} BTC")
        p.drawString(50, y-60, f"Wallet: {t.wallet}")
        y -= 100  # Move down for next transaction
        count += 1  # Increment transaction count

    p.save()
    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f'transactions_{download_type}.pdf'
    )


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/products')
def products():
    return render_template('products.html')


@app.route('/checkout')
def checkout():
    return render_template('checkout.html')


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == "admin" and password == "admin123":
            transactions = Transaction.query.all()
            latest_transaction = Transaction.query.order_by(
                Transaction.id.desc()).first()
            return render_template('admin.html', transactions=transactions, latest_transaction=latest_transaction)
    return render_template('admin.html', transactions=None, latest_transaction=None)


@app.route('/process_transaction', methods=['POST'])
def process_transaction():
    data = request.json

    # Generate a random past date (between 1 and 365 days ago)
    # Random number of days in the past
    random_days_ago = random.randint(1, 365)
    random_seconds = random.randint(0, 86400)  # Random seconds within the day
    transaction_date = datetime.utcnow() - timedelta(days=random_days_ago,
                                                     seconds=random_seconds)

    new_transaction = Transaction(
        product=data['product'],
        amount=float(data['amount']),
        wallet=data['wallet'],
        date=transaction_date
    )

    db.session.add(new_transaction)
    db.session.commit()

    return jsonify({"status": "success", "transaction_date": transaction_date.strftime("%Y-%m-%d %H:%M:%S")})


if __name__ == '__main__':
    app.run(debug=True)
