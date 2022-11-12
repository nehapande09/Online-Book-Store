from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
import random
import json
import socket



with open('config.json', 'r') as c:
    params = json.load(c)["params"]

local_server = True
app = Flask(__name__, template_folder='./templates', static_folder='./static')
app.secret_key = 'super secret key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost/readers'
app.config["SQLALCHEMY_TRACK_MODIFICATION"] = False
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
socket.getaddrinfo('localhost', 8080)
db = SQLAlchemy(app)
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT='465',
    MAIL_USE_SSL=True,
    MAIL_USERNAME=params['gmail_user'],
    MAIL_PASSWORD=params['gmail-password']
)
mail = Mail(app)


class Users(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=True)
    email_id = db.Column(db.String(50), nullable=True)
    password = db.Column(db.String(100), nullable=True)
    date = db.Column(db.DateTime, nullable=True, default=datetime.now())
    cart = db.relationship('Cart', backref='user')


class Books(db.Model):
    # __searchable__ = ['name', 'author_name']

    book_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=True)
    author_name = db.Column(db.String(50), nullable=True)
    description = db.Column(db.String(1000), nullable=True)
    category = db.Column(db.String(50), nullable=True)
    type = db.Column(db.String(50), nullable=True)
    price = db.Column(db.String(10), nullable=True)
    date = db.Column(db.DateTime, nullable=True, default=datetime.now())
    img_name = db.Column(db.String(100), nullable=True)
    language = db.Column(db.String(30), nullable=True)
    pages = db.Column(db.Integer, nullable=True)
    cart = db.relationship('Cart', backref='book')





class Contacts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=True)
    phone_num = db.Column(db.String(10), nullable=True)
    msg = db.Column(db.String(120), nullable=True)
    date = db.Column(db.DateTime, nullable=True, default=datetime.now())
    email = db.Column(db.String(20), nullable=False)


class Cart(db.Model):
    cart_id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey(Books.book_id))
    date = db.Column(db.DateTime, nullable=True, default=datetime.now())
    user_id = db.Column(db.Integer, db.ForeignKey(Users.user_id))


db.create_all()


@app.route('/')
def home():
    books = Books.query.all()
    return render_template("home.html", books=books)


@app.route('/search', methods=['POST', 'GET'])
def search():
    query = request.form.get('search')
    books = Books.query.filter((Books.name == query) | (Books.author_name == query)).all()
    if books:
        return render_template("search.html", books=books)
    else:
        return render_template("error.html")


@app.route('/about')
def about():
    return render_template("about.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = Users.query.filter_by(email_id=email).first()
        if user.password == password:
            # flash('Login Successful')
            session['login'] = True
            session['email'] = email
            return redirect('/')
        else:
            flash('Login Unsuccessful. Please check email and password')

    return render_template('login.html')


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session['login'] = False
    return redirect('/')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        user_object = Users.query.filter_by(email_id=email).first()
        if user_object:
            flash('User With this Email id is already exists!', 'error')
            return render_template("signup.html")
        else:
            user = Users(username=username, email_id=email, password=password)
            db.session.add(user)
            db.session.commit()
            if request.form.get('submit'):
                flash('Registration done!')
            return redirect(url_for('home'))

    return render_template("signup.html")


@app.route('/forgot_password', methods=['POST'])
def f_pass():
    if request.method == 'POST':
        email = request.form.get('email')
        user_object = Users.query.filter_by(email_id=email).first()
        if user_object is None:
            flash("No such account exists")
            return redirect(url_for('signup'))
        else:
            otp = random.randint(1111, 9999)
            session['otp'] = otp
            session['email'] = email
            print(type(otp), type(email))
            mail.send_message("Mail from Readers Cafe ", sender=params['gmail_user'], recipients=[email],
                              body=f"Your otp is :{otp}")
            return redirect("/otp_generation")
    return render_template("forgot_password.html")


@app.route('/otp_generation', methods=['GET', 'POST'])
def otp_gen():
    if request.method == 'POST':
        u_otp = request.form.get('otp')
        n_password = request.form.get('password')
        if u_otp == str(session["otp"]):
            user = Users.query.filter_by(email_id=session["email"]).first()
            user.password = n_password
            db.session.commit()
            flash("Password Updated")
    return render_template('otp_generation.html')


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        entry = Contacts(name=name, phone_num=phone, msg=message, date=datetime.now(), email=email)
        db.session.add(entry)
        db.session.commit()
        mail.send_message(subject=f"Mail from {name}", body=f"Name:{name}\nE-mail:{email}\nPhone:{phone}\n\n\n{message}"
                          , sender=email, recipients=[params['gmail_user']])
        if request.form.get('Submit'):
            flash('Feedback send Successfully')

    return render_template("contact.html", params=params)


@app.route('/fiction')
def fiction():
    books = Books.query.filter_by(type='fiction').all()
    return render_template("fiction.html", books=books)


@app.route('/nonfiction')
def nonfiction():
    books = Books.query.filter_by(type='nonfiction').all()
    return render_template("non_fiction.html", books=books)


@app.route('/readmore/<int:id>', methods=['GET', 'POST'])
def readmore(id):
    book = Books.query.filter_by(book_id=id).first()

    return render_template("readmore.html", book=book)


@app.route('/getotp')
def getotp():
    return render_template("forgot_password.html")


@app.route('/addcart/<int:id>', methods=['GET'])
def addcart(id):
    if session['login']:
        user = Users.query.filter_by(email_id=session['email']).first()
        book = Books.query.filter_by(book_id=id).first()
        book = Cart(book=book, user=user)
        db.session.add(book)
        db.session.commit()
        return redirect("/cart")

    return redirect('/login')


@app.route('/cart', methods=['GET'])
def cart():
    cart_books = []
    total_price = 0
    if session['login']:
        # print(session['email'])
        user = Users.query.filter_by(email_id=session['email']).first()
        carts = user.cart
        for cart in carts:
            b = {
                "book_id": cart.book.book_id,
                "name": cart.book.name,
                "author_name": cart.book.author_name,
                "description": cart.book.description,
                "category": cart.book.category,
                "type": cart.book.type,
                "price": cart.book.price,
                "date": cart.book.date,
                "img_name": cart.book.img_name,
                "language": cart.book.language,
                "pages": cart.book.pages
            }
            total_price = total_price + int(cart.book.price)
            session['total_price'] = total_price + 25
            cart_books.append(b)
            session['cart_books'] = cart_books
    return render_template("cart.html", books=cart_books, total_price=total_price)


@app.route('/removecart/<int:book_id>', methods=['GET'])
def removecart(book_id):
    print("hello")
    book = Cart.query.filter_by(book_id=book_id).first()
    print(book)
    db.session.delete(book)
    db.session.commit()
    return redirect("/cart")


@app.route('/checkout', methods=[ 'GET','POST'])
def checkout():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        mail.send_message("Mail from Readers Cafe ", sender=params['gmail_user'], recipients=[email],
                         body=f"Dear Customer, {name} Your Order is Successful! of price:{session['total_price']} ")
        if request.form.get('ok'):
            flash('Order Successful')

    return render_template("checkout.html")


@app.route('/error')
def error():
    return render_template('error.html')


@app.route('/ordered')
def ordered():
    return render_template('ordered.html')


app.run(debug=True)
