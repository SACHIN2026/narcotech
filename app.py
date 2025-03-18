from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file
from flask import session, redirect
import os
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from reportlab.pdfgen import canvas
from io import BytesIO
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'your_secret_key'
db = SQLAlchemy(app)
# Add at the top of app.py
# app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product = db.Column(db.String(100))
    amount = db.Column(db.Float)
    wallet = db.Column(db.String(100))
    date = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

# Add these imports at the top
from flask import session, redirect
import os

# Add this route for logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('admin'))

# Modify the download_pdf route
@app.route('/download_pdf')
def download_pdf():
    download_type = request.args.get('type', 'all')
    
    if download_type == 'latest':
        transactions = [Transaction.query.order_by(Transaction.id.desc()).first()]
    else:
        transactions = Transaction.query.all()
    
    buffer = BytesIO()
    p = canvas.Canvas(buffer)
    
    # Add header
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, 800, "NarcoTech Transaction Report")
    p.setFont("Helvetica", 12)
    p.drawString(50, 780, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    # Add transactions
    y = 740
    for t in transactions:
        p.drawString(50, y, f"Date: {t.date.strftime('%Y-%m-%d %H:%M')}")
        p.drawString(50, y-20, f"Product: {t.product}")
        p.drawString(50, y-40, f"Amount: {t.amount} BTC")
        p.drawString(50, y-60, f"Wallet: {t.wallet}")
        y -= 100
    
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
            return render_template('admin.html', transactions=transactions)
    return render_template('admin.html', transactions=None)

@app.route('/process_transaction', methods=['POST'])
def process_transaction():
    data = request.json
    new_transaction = Transaction(
        product=data['product'],
        amount=float(data['amount']),
        wallet=data['wallet']
    )
    db.session.add(new_transaction)
    db.session.commit()
    return jsonify({"status": "success"})

if __name__ == '__main__':
    app.run(debug=True)