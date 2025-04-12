from flask import Flask, render_template, request, url_for
import sqlite3

app = Flask(__name__)

# Gets database
def get_db():
    db = sqlite3.connect('bookstore.sqlite')
    db.row_factory = sqlite3.Row
    return db

# Homepage
@app.route('/')
def index():
    return render_template('index.html')

# Inventory
@app.route('/inventory')
def inventory():
    db = get_db()

    inventories = db.execute('''
        SELECT b.ISBN, b.Title, b.Year, i.Quantity
        FROM Inventory i
        JOIN Book b ON b.ISBN = i.Book_ID
    ''')

    return render_template('inventory.html', inventories=inventories)

# Dashboard
# Post request updates order status
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    db = get_db()

    # Update if post
    if request.method == 'POST':
        order_id = request.form['order_id']
        new_status = request.form['status']
        db.execute('UPDATE "Order" SET Status = ? WHERE Order_ID = ?', (new_status, order_id))
        db.commit()

    # Update dashboard
    orders = db.execute('''
        SELECT o.Order_ID, o.Date, o.Status, o.Total_Price, o.Customer_ID,
               c.First_Name || ' ' || c.Last_Name AS Customer
        FROM "Order" o
        JOIN Customer c ON o.Customer_ID = c.Customer_ID
        ORDER BY o.Date DESC
    ''').fetchall()

    return render_template('dashboard.html', orders=orders)

if __name__ == '__main__':
    app.run(debug=True, port=3241)
