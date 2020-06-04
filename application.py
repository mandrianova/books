import os

from functools import wraps

from flask import Flask, session, render_template, request, redirect, url_for, flash, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.security import check_password_hash, generate_password_hash
from goodreads import get_rating


app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.template_filter('strftime')
def _jinja2_filter_datetime(date, fmt=None):
    """Custom filter for date"""
    format = "%H:%M:%S | %A %b %d %Y"
    return date.strftime(format)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated_function


@app.route("/", methods=["GET"])
@login_required
def index():

    # Search
    query = "%%"
    if request.args.get('q'):
        query = "%{q}%".format(q=request.args.get('q'))

    # Pagination variables
    limit = 20  # elements on page
    offset = 0
    if request.args.get('p'):  # the current page
        page = int(request.args.get('p'))
        offset = page * limit
    else:
        page = 1

    # Get objects for page
    page_objects = db.execute("SELECT * FROM books WHERE author like :q OR title like :q OR isbn like :q "
                              "ORDER BY title LIMIT :limit OFFSET :offset",
                              {'q': query, 'limit': limit, 'offset': offset}).fetchall()
    element_count = db.execute("SELECT * FROM books WHERE author like :q OR title like :q "
                               "OR isbn like :q",
                               {"q": query}).rowcount
    page_count = element_count // limit

    # Pagination conditions for view
    if element_count % limit == 0:
        page_count -= 1
    first_page = page - 3
    last_page = page + 4
    if page - 3 < 1:
        first_page = 1
    if page + 3 > page_count:
        last_page = page_count + 1
    page_range_view = range(first_page, last_page)
    return render_template("index.html", books=page_objects, page_range_view=page_range_view, page=page,
                           page_count=page_count, q=request.args.get('q'))


@app.route("/book/<int:book_id>", methods=["GET", "POST"])
@login_required
def book(book_id):

    if request.method == "POST":

        # Check review fields
        print(request.form.get("rating"))
        if not request.form.get("review") or not request.form.get("rating"):
            flash(u'Review or rating is empty', 'danger')
        elif float(request.form.get("rating")) < 0 or float(request.form.get("rating")) > 5.0:
            flash(u'Invalid rating', 'danger')
        else:
            user_id = int(session.get("user_id"))
            review = request.form.get("review")
            user_rating = float(request.form.get("rating"))

            # Check saved review from this user for the book
            check_review = db.execute("SELECT * FROM reviews WHERE user_id = :user_id AND book_id = :book_id",
                       {'user_id': user_id, 'book_id': book_id}).fetchone()
            if check_review:
                flash(u'Your already have review for this book', 'warning')

            # Save review if it is first
            else:
                try:
                    db.execute("INSERT INTO reviews (review, user_id, book_id, rating) "
                               "VALUES (:review, :user_id, :book_id, :rating)",
                               {"review": review, 'user_id': user_id, 'book_id': book_id, 'rating': user_rating})
                    db.commit()
                    flash(u'Review saved', 'success')
                except:
                    flash(u'Review did not save', 'danger')
                return redirect(url_for("book", book_id=book_id))

    # Get content for page
    book_page = db.execute("SELECT * FROM books WHERE id = :id", {'id': book_id}).fetchone()
    if not book_page:
        return render_template("404.html"), 404
    reviews = db.execute("SELECT review, rating, date, username FROM reviews "
                         "join users u on reviews.user_id = u.id WHERE book_id = :id "
                         "ORDER BY date DESC", {'id': book_id}).fetchall()
    review_rating = db.execute("SELECT AVG(rating) as ar FROM reviews WHERE book_id = :book_id",
                               {'book_id': book_id}).fetchone()['ar']
    if review_rating:
        review_rating = round(review_rating, 2)
    rating = get_rating(book_page['isbn'])
    return render_template("book.html", book=book_page, reviews=reviews, rating=rating, review_rating=review_rating)


@app.route("/logout")
def logout():
    """Function for logout"""
    session.clear()
    return redirect(url_for('index'))


@app.route("/login", methods=["GET", "POST"])
def login():
    """Login function"""

    session.clear()
    if request.method == "POST":

        # Check login fields
        if not request.form.get("username"):
            flash(u'must provide username', 'danger')
            return render_template("login.html")
        elif not request.form.get("password"):
            flash(u'must provide password', 'danger')
            return render_template("login.html")

        # Check the username and the password
        row = db.execute("SELECT * FROM users WHERE username = :username",
                         {'username': request.form.get("username")}).fetchone()
        if not row or not check_password_hash(row["hash"], request.form.get("password")):
            flash(u'invalid username and/or password', 'danger')
            return render_template("login.html")

        # Set session
        session["user_id"] = row["id"]
        session["username"] = row["username"]
        return redirect(url_for('index'))
    else:
        return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":

        # Check fields
        if not request.form.get("username"):
            flash(u'must provide username', 'danger')
            return render_template("register.html")

        elif not request.form.get("password"):
            flash(u'must provide password', 'danger')
            return render_template("register.html")

        elif request.form.get("password") != request.form.get("password_repeat"):
            flash(u'the passwords do not match', 'danger')
            return render_template("register.html")

        # Check username is unique
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          {'username': request.form.get("username")}).fetchall()
        if len(rows) > 0:
            flash(u'username already registered', 'danger')
            return render_template("register.html")

        # Add new user into db
        hash_password = generate_password_hash(request.form.get("password"))
        db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)",
                   {'username': request.form.get("username"), 'hash': hash_password})
        db.commit()
        flash(u'Success registered', 'success')
        return redirect(url_for('index'))
    else:
        return render_template("register.html")


@app.route("/api/<string:isbn>", methods=["GET"])
def api_isbn(isbn):
    if len(isbn) != 10:
        return jsonify({"error": "Invalid ISBN"}), 422
    result = db.execute("SELECT title, author, year, COUNT(review) AS review_count, "
                        "ROUND(AVG(rating), 2) AS average_rating FROM books "
                        "LEFT JOIN reviews r ON books.id = r.book_id "
                        "WHERE isbn = :isbn GROUP BY title, author, year, isbn", {'isbn': isbn}).fetchone()
    if not result:
        return jsonify({"error": "Book is not found"}), 404
    return jsonify({
        "title": result['title'],
        "author": result['author'],
        "ISBN": isbn,
        "publication_date": result['year'],
        "review_count": result['review_count'],
        "average_score": result['average_rating']
    })

