from flask import Flask, render_template, request, url_for, redirect
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
        SELECT o.Order_ID, o.Date, o.Status, o.Total_Price, o.Customer_ID, c.First_Name || ' ' || c.Last_Name AS Customer
        FROM "Order" o
        JOIN Customer c ON o.Customer_ID = c.Customer_ID
        ORDER BY o.Date DESC
    ''').fetchall()

    return render_template('dashboard.html', orders=orders)

@app.route('/order/<int:order_id>')
def order_details(order_id):
    db = get_db()

    # Get order with matching order_id
    order = db.execute('''
        SELECT o.Order_ID, o.Date, o.Status, o.Total_Price, c.Customer_ID, c.First_Name || ' ' || c.Last_Name AS Customer
        FROM "Order" o
        JOIN Customer c ON o.Customer_ID = c.Customer_ID
        WHERE o.Order_ID = ?
    ''', (order_id,)).fetchone()

    # Get order_items
    items = db.execute('''
        SELECT oi.Quantity, oi.Price, b.Title, b.ISBN
        FROM Order_Item oi
        JOIN Book b ON b.ISBN = oi.Book_ID
        WHERE oi.Order_ID = ?
    ''', (order_id,)).fetchall()

    return render_template('order_details.html', order=order, items=items)

@app.route('/update_inventory', methods=['POST'])
def update_inventory():
    db = get_db()
    try:
        isbn = request.form['isbn']
        new_quantity = int(request.form['quantity'])
        
        db.execute('''
            UPDATE Inventory 
            SET Quantity = ?
            WHERE Book_ID = ?
        ''', (new_quantity, isbn))
        db.commit()
        
        return redirect(url_for('inventory'))
    except Exception as e:
        print(f"Error updating inventory: {e}")
        return redirect(url_for('inventory'))
    
@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    if request.method == 'POST':
        db = get_db()
        try:
            isbn = request.form['isbn']
            title = request.form['title']
            year = int(request.form['year'])
            price = float(request.form['price'])
            quantity = int(request.form['quantity'])
            
            # First add to Book table
            db.execute('''
                INSERT INTO Book (ISBN, Title, Year, Price)
                VALUES (?, ?, ?, ?)
            ''', (isbn, title, year, price))
            
            # Then add to Inventory
            db.execute('''
                INSERT INTO Inventory (Book_ID, Quantity)
                VALUES (?, ?)
            ''', (isbn, quantity))
            
            db.commit()
            return redirect(url_for('inventory'))
        except Exception as e:
            print(f"Error adding book: {e}")
            db.rollback()
            return redirect(url_for('add_book'))
            
    return render_template('add_book.html')

@app.route('/remove_book/<string:isbn>', methods=['POST'])
def remove_book(isbn):
    db = get_db()
    try:
        # Remove from Inventory first (foreign key constraint)
        db.execute('DELETE FROM Inventory WHERE Book_ID = ?', (isbn,))
        # Then remove from Book
        db.execute('DELETE FROM Book WHERE ISBN = ?', (isbn,))
        db.commit()
    except Exception as e:
        print(f"Error removing book: {e}")
    return redirect(url_for('inventory'))

if __name__ == '__main__':
    app.run(debug=True, port=3241)
