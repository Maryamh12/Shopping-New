import sqlite3
import os

if os.path.exists("./productdb.db"):
   os.remove("./productdb.db")
def init_db():
    conn = sqlite3.connect('productdb.db')
    dbCursor = conn.cursor()
    
    dbCursor.execute(
    """ 
        CREATE TABLE IF NOT EXISTS Users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,  -- Store hashed passwords, not plaintext
            email TEXT NOT NULL UNIQUE
        )"""
)
# ...............................
    dbCursor.execute(
        """ 
            CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            price REAL NOT NULL,
            image_url TEXT
        )"""
    )
# ...............................
    dbCursor.execute(
            """ 
                CREATE TABLE IF NOT EXISTS review (
                Review_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                product_id INTEGER,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES Users(user_id),
                FOREIGN KEY (product_id) REFERENCES Products(product_id)
            )"""
        )
# ...............................
    dbCursor.execute(
        """ 
            CREATE TABLE IF NOT EXISTS Basket (
            basket_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product_id INTEGER,
            quantity INTEGER,
            FOREIGN KEY (user_id) REFERENCES Users(user_id),
            FOREIGN KEY (product_id) REFERENCES Products(product_id)
        )"""
    )
# ...............................

    dbCursor.execute(
        """ 
            CREATE TABLE IF NOT EXISTS Orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            order_date DATETIME,
            total REAL,
            status TEXT,
            FOREIGN KEY (user_id) REFERENCES Users(user_id)
        )"""
    )
# ...............................
    dbCursor.execute(
        """ 
            CREATE TABLE IF NOT EXISTS OrderDetails (
            order_details_id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            product_id INTEGER,
            quantity INTEGER,
            price_at_time_of_order REAL,
            FOREIGN KEY (order_id) REFERENCES Orders(order_id),
            FOREIGN KEY (product_id) REFERENCES Products(product_id)
        )"""
    )
# ...............................


    dbCursor.execute(
        """ 
            CREATE TABLE IF NOT EXISTS Favorites (
            user_id INTEGER,
            product_id INTEGER,
            PRIMARY KEY (user_id, product_id),
            FOREIGN KEY (user_id) REFERENCES Users(user_id),
            FOREIGN KEY (product_id) REFERENCES Products(product_id)
        )"""
    )
# ...............................

    conn.commit()
    conn.close()
    
init_db()

def add_product(name, description, price, image_url):
    db = sqlite3.connect('./productdb.db')
    cursor = db.cursor()
    cursor.execute('''
        INSERT INTO products(name, description, price, image_url)
        VALUES(?,?,?,?)
    ''', (name, description, price, image_url))
    db.commit()
    db.close()

products = [
    ("White Long Sleeve Shirt", "Description for product 1", 15.99, "https://images.pexels.com/photos/3765976/pexels-photo-3765976.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1"),
    ("Black Shirt", "Description for product 2", 13.99, "https://images.pexels.com/photos/3586020/pexels-photo-3586020.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1"),
    (" White Earings", "Description for product 2", 12.99, "https://images.pexels.com/photos/9969730/pexels-photo-9969730.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1"),
    ("Pink Outfit", "Description for product 2", 22.99, "https://images.pexels.com/photos/19881397/pexels-photo-19881397/free-photo-of-woman-posing-in-pink-outfit.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1"),
    ("Pearl Earring", "Description for product 2", 12.99, "https://images.pexels.com/photos/9428779/pexels-photo-9428779.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1"),
    ("Earring with Diamonds and Emeralds", "Description for product 2", 12.99, "https://images.pexels.com/photos/17298631/pexels-photo-17298631/free-photo-of-earring-with-diamonds-and-emeralds.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1"),
    # Add more products as needed
]

for product in products:
    add_product(*product)
    
    

def complete_order(db, user_id):
    # Move items from basket to an order
    cur = db.cursor()
    cur.execute('INSERT INTO Orders (user_id, order_date, total, status) VALUES (?, datetime("now"), (SELECT SUM(price * quantity) FROM Basket JOIN Products ON Basket.product_id = Products.product_id WHERE user_id = ?), "Pending")', (user_id, user_id))
    order_id = cur.lastrowid
    cur.execute('INSERT INTO OrderDetails (order_id, product_id, quantity, price_at_time_of_order) SELECT ?, product_id, quantity, price FROM Basket JOIN Products ON Basket.product_id = Products.product_id WHERE user_id = ?', (order_id, user_id))
    cur.execute('DELETE FROM Basket WHERE user_id = ?', (user_id,))
    db.commit()
