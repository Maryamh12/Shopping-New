from flask import Flask, render_template, request, redirect, url_for , session , flash
import sqlite3 as sql
import bcrypt
from flask_debugtoolbar import DebugToolbarExtension
import stripe
from flask_cors import CORS
import sys
print(sys.path)

app =  Flask(__name__)
CORS(app)
app.debug = True  # Ensure debug mode is on
app.config['SECRET_KEY'] = 'your_secret_key_here'
stripe.api_key = 'your_stripe_secret_key_here'


def base():
    session['logged_out'] = True
    session['user_id'] = 0
    if 'logged_out' not in session:
        session['logged_out'] = True
    return render_template('base.html',title="Home Page")

def get_members():
    try:
        with  sql.connect('./productdb.db') as dbCon: 
           dbCursor = dbCon.cursor()
        dbCursor.execute('SELECT * FROM products')
        members = dbCursor.fetchall()
        print(f"ID: {members[0][1]}")
   
    except sql.OperationalError as oe:
        print(f"Connection faild because: {oe}")
    except sql.Error as e:
        print(f"Error occurred: {e}")
    return members


def get_member_by_id(member_id):
  
    try:
        with sql.connect('./productdb.db') as dbCon: 
            cur = dbCon.cursor()
            cur.execute("SELECT * FROM products WHERE id = ?", (member_id,))
            member = cur.fetchone()
            cur.execute("SELECT * FROM review WHERE product_id = ?", (member_id,))
            comments = cur.fetchall()
           
        return member ,comments
    except sql.Error as e:
        print(f"Error occurred: {e}")
        return None

def add_to_favorites(user_id, product_id):
    try:
        with sql.connect('./productdb.db') as dbCon: 
            cur = dbCon.cursor()
            # Check if the product is already in the basket
            cur.execute("SELECT * FROM Favorites WHERE user_id = ? AND product_id = ?", (user_id, product_id))
            exists = cur.fetchone()
            if exists:
                # If exists, remove from favorites
                cur.execute("DELETE FROM Favorites WHERE user_id = ? AND product_id = ?", (user_id, product_id))
                action = 'removed from'
            else:
                # If not exists, add to favorites
                cur.execute("INSERT INTO Favorites (user_id, product_id) VALUES (?, ?)", (user_id, product_id))
            
            dbCon.commit()
        return redirect(url_for('product', member_id=product_id))
    except sql.Error as e:
        print(f"Error occurred: {e}")
        return None
    
def add_to_basket( user_id, product_id,quantity):
    try:
        with sql.connect('./productdb.db') as dbCon: 
            cur = dbCon.cursor()
            # Check if the product is already in the basket
            cur.execute('SELECT quantity FROM Basket WHERE user_id = ? AND product_id = ?', (user_id, product_id))
            existing = cur.fetchone()
            
            if existing:
                # If the product is already in the basket, increase the quantity by 1
                new_quantity = existing[0] + quantity
                cur.execute('UPDATE Basket SET quantity = ? WHERE user_id = ? AND product_id = ?', (new_quantity, user_id, product_id))
            else:
                # If the product is not in the basket, insert a new record with quantity 1
                cur.execute('INSERT INTO Basket (user_id, product_id, quantity) VALUES (?, ?, ?)', (user_id, product_id, quantity))
                action = 'added to'
            dbCon.commit()
        return redirect(url_for('product' , member_id=product_id))
    except sql.Error as e:
        print(f"Error occurred: {e}")
        return None

@app.route('/update-basket/<int:user_id>/<int:product_id>', methods=['POST'])
def update_basket(user_id, product_id):
    action = request.form.get('action')
    if action == 'update':
        new_quantity = request.form.get('quantity', type=int)
        try:
            with sql.connect('./productdb.db') as dbCon:
                cur = dbCon.cursor()
                # Update the quantity of the product in the basket
                if new_quantity > 0:
                    cur.execute('UPDATE Basket SET quantity = ? WHERE user_id = ? AND product_id = ?',
                                (new_quantity, user_id, product_id))
                    dbCon.commit()
                    flash('Basket updated successfully.', 'success')
                else:
                    flash('Quantity must be at least 1.', 'error')
        except Exception as e:
            flash(f'An error occurred: {e}', 'error')
        
    elif action == 'remove':
        try:
            with sql.connect('./productdb.db') as dbCon:
                cur = dbCon.cursor()
                # Remove the product from the basket
                cur.execute('DELETE FROM Basket WHERE user_id = ? AND product_id = ?',
                            (user_id, product_id))
                dbCon.commit()
                flash('Product removed from basket.', 'success')
        except Exception as e:
            flash(f'An error occurred: {e}', 'error')
    
    return redirect(url_for('basket', user_id=user_id))
 
 
@app.route('/update_comments/<int:user_id>/<int:product_id>', methods=['POST'])
def update_comments(user_id, product_id):
    action = request.form.get('action')
    if action == 'update':
        name = request.form.get('name')
        description = request.form.get('description')
        print(name)
        print(description)
        try:
            with sql.connect('./productdb.db') as dbCon:
                cur = dbCon.cursor()
                # Update the quantity of the product in the basket
                cur.execute('INSERT INTO review (user_id, product_id, name,description) VALUES (?, ?, ?,?)', (user_id, product_id, name,description))
                cur.execute("SELECT * FROM review WHERE product_id = ?", (product_id,))
                comments = cur.fetchall()
                print(comments)
                dbCon.commit()
                flash('review updated successfully.', 'success')
        except Exception as e:
            flash(f'An error occurred: {e}', 'error')  
    return redirect(url_for('product', member_id=product_id))

@app.route('/update-favorite/<int:user_id>/<int:product_id>', methods=['POST'])
def update_favorite(user_id, product_id):
    action = request.form.get('action')
    if action == 'update':
        
        try:
            with sql.connect('./productdb.db') as dbCon:
                cur = dbCon.cursor()
                cur.execute('SELECT quantity FROM Basket WHERE user_id = ? AND product_id = ?', (user_id, product_id))
                existing = cur.fetchone()
            
                if existing:
                        # If the product is already in the basket, increase the quantity by 1
                        new_quantity = existing[0] + 1
                        cur.execute('UPDATE Basket SET quantity = ? WHERE user_id = ? AND product_id = ?', (new_quantity, user_id, product_id))
                        cur.execute('DELETE FROM Favorites WHERE user_id = ? AND product_id = ?',
                            (user_id, product_id))
                else:
                        # If the product is not in the basket, insert a new record with quantity 1
                        cur.execute('INSERT INTO Basket (user_id, product_id, quantity) VALUES (?, ?, ?)', (user_id, product_id, 1))
                        cur.execute('DELETE FROM Favorites WHERE user_id = ? AND product_id = ?',
                            (user_id, product_id))
                        
                
            dbCon.commit()
        except Exception as e:
            flash(f'An error occurred: {e}', 'error')
    elif action == 'remove':
        try:
            with sql.connect('./productdb.db') as dbCon:
                cur = dbCon.cursor()
               
                cur.execute('DELETE FROM Favorites WHERE user_id = ? AND product_id = ?',
                            (user_id, product_id))
                dbCon.commit()
                flash('Product removed from basket.', 'success')
        except Exception as e:
            flash(f'An error occurred: {e}', 'error')
    
    return redirect(url_for('favorite', user_id=user_id))
                
               

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if request.method == 'POST':
        # Process payment
        customer = stripe.Customer.create(
            email=request.form['email'],
            source=request.form['stripeToken']  # Obtained with Stripe.js
        )
        
        charge = stripe.Charge.create(
            customer=customer.id,
            amount=int(session['total_price'] * 100),  # Total price in cents
            currency='usd',
            description='Purchase Description'
        )
        
        # Clear the session cart
        session['cart'] = {}
        return render_template('confirmation.html', charge=charge)

    # Display checkout form
    return render_template('checkout.html', cart=session.get('cart', {}))




@app.route('/')
def home():
    return render_template('home.html',title="Home Page")

@app.route('/logout')
def logout():
    session['logged_out'] = True
    session['user_id'] = 0
    return redirect(url_for('home'))

@app.route('/products')
def products():
    members = get_members()
    return render_template('products.html',title="Products Page"  ,members=members)


@app.route('/products/<int:user_id>/<int:product_id>', methods=['POST'])
def addtobasket(user_id, product_id):
    quantity = request.form.get('quantity', type=int)
    add_to_basket(user_id, product_id,quantity)
    return redirect(url_for('product' , member_id=product_id))


@app.route('/favorite/<int:user_id>/<int:product_id>')
def addtofavorites(user_id, product_id):
    add_to_favorites(user_id, product_id)
    return redirect(url_for('product', member_id=product_id))


@app.route('/basket/<int:user_id>')
def basket(user_id):
    print(user_id)
    try:
        with sql.connect('./productdb.db') as con:
            cur = con.cursor()
            cur.execute("SELECT username FROM users WHERE user_id = ?", (user_id,))
            username = cur.fetchone()  # Fetch the stored hash
            print(username)
            if not username:
                 return render_template('basket.html',title="Products Page"  ,basketItems=[],username=username)
            else:
                cur.execute("""
            SELECT p.name, p.description, b.quantity, p.price , p.image_url, p.id
            FROM Basket b
            JOIN Products p ON b.product_id = p.id
            WHERE b.user_id = ?
        """, (user_id,))
        basketItems = cur.fetchall()
    except Exception as e:
        return str(e), 500

    return render_template('basket.html',title="Products Page"  ,basketItems=basketItems,username=username)


@app.route('/favorite/<int:user_id>')
def favorite(user_id):
    print(user_id)
    try:
        with sql.connect('./productdb.db') as con:
            cur = con.cursor()
            cur.execute("SELECT username FROM users WHERE user_id = ?", (user_id,))
            username = cur.fetchone()  # Fetch the stored hash
            print(username)
            if not username:
                 return render_template('favorite.html',title="Products Page"  ,favoritesItems=[],username=username)
            else:
                cur.execute("""
                SELECT p.name, p.description,  p.price , p.image_url, p.id
                FROM Favorites f
                JOIN Products p ON f.product_id = p.id
                WHERE f.user_id = ?
            """, (user_id,))
            favoritesItems = cur.fetchall()
    except Exception as e:
        return str(e), 500

    return render_template('favorite.html',title="Products Page"  ,favoritesItems=favoritesItems,username=username)


@app.route('/product/<int:member_id>')
def product(member_id):
    [member , comments] = get_member_by_id(member_id)
    
    if member:
        return render_template('product.html',title="Product Page"  ,member=member, comments=comments)
    else:
        return "Member not found", 404
    

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password'].encode('utf-8')

        try:
            with sql.connect('./productdb.db') as con:
                cur = con.cursor()
                cur.execute("SELECT password FROM users WHERE username = ?", (username,))
                user_pass = cur.fetchone()  # Fetch the stored hash
                cur.execute("SELECT user_id FROM users WHERE username = ?", (username,))
                user_id = cur.fetchone()[0] 
                print(f"password: {user_pass}")
                if user_pass and bcrypt.checkpw(password, user_pass[0]) and user_id :
                    session['logged_out'] = False
                    session['user_id'] = user_id
                    return redirect(url_for('products'))  # Redirect to the home page if login is successful
                else:
                    return "Invalid username or password", 401
        except Exception as e:
            return str(e), 500

    return render_template('login.html')
    
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('Passwords do not match! Please try again.')
            return redirect(url_for('register'))
        # Generate a salt and hash the password
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        try:
            with sql.connect('./productdb.db') as con:
                cur = con.cursor()
                cur.execute("INSERT INTO users (username, password, email) VALUES (?, ?, ?)", (username, hashed, email))
                con.commit()
                return redirect(url_for('login'))  # Redirect to the login page after successful registration
        except sql.IntegrityError:
            return "That username or email already exists!", 400
        except Exception as e:
            return str(e), 500

    return render_template('register.html')

def footer():
    return render_template('footer.html',title="Home Page")

# to run the flask app
if __name__ == "__main__":
    
    app.run()