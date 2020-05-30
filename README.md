# Project 1 - Book

## Structure of Project
### Content
- The Directory **static** - css and js files (bootstrap, jquery, special styles for project in styles.css, which generated from sass). It is directory, which used Flask for loading static files.
- The Directory **templates** with html files.
- Python files.

### Static
The general style and js is bootstrap framework. I used their grid and styles and also I used jquery for it and for rating stars animation in the review form [form_review.html](templates/form_review.html).

In [style.css](static/css/styles.css) I added some styles for specific places (cards of book and rating).

### Templates

#### Base
[Base.html](templates/base.html) contains the base template and includes internal and external styles and js. I used Flask method url_for for including internal static files. Also it included [navbar.html](templates/navbar.html).

#### Navbar
[Navbar.html](templates/navbar.html) contains the navigation and includes [message.html](templates/message.html). It is simple navigation: the main page, login, logout and register pages. The view and content of the navbar depending on user status. If the user is logged in, the username and logout are displayed, else log in and register are displayed.

#### Message
[Message.html](templates/message.html) contains rules for messages displaying. I used bootstrap alerts for template and Flask method flash for forms of messages. I used the category for the definition of alerts class.

#### Index
[Index.html](templates/index.html) is the template for main page with search and book catalog. Books list view is cards with title, author, year, isbn and cover. Cover for book adds from [openlibrary.org](https://openlibrary.org/dev/docs/api/covers). The list of books is paginated and pagination included from the template [pagination.html](templates/pagination.html).

#### Pagination

[Pagination.html](templates/pagination.html) contains rules for creating page numbers for pagination.

#### Login and Register

[Login.html](templates/login.html) and [register.html](templates/register.html) are the simple templates with form for username and password. Password input needs two times on the registration page.

#### Book
[Book.html](templates/book.html) contains card of the book with cover, title, author, rating and review count from [goodreads.com](https://www.goodreads.com/), ISBN, year, reviews list, and includes [form_review.html](templates/form_review.html). Reviews list contains users reviews with the username, date, rating and text.

#### Review Form
[Form_review.html](templates/form_review.html) contains form for review of the book (rating and text). The rating's input is five stars with a step in half star.

#### 404

[404.html](templates/404.html) is the simple page with text "Page not found".

### Python files

#### Config
**Config.py not includes in project** and contains function set_variable() for setting environment variables. I had the problems with it and I used the function. I added variable ```os.environ["GOOD_KEY"]``` for api key.
```python
import os

def set_variable():
    os.environ["GOOD_KEY"] = "api_key"
    os.environ["DATABASE_URL"] = "DATABASE_URL"
    os.environ["FLASK_APP"] = "application.py"
    os.environ["FLASK_DEBUG"] = '1'
```

#### Import

[Import.py](import.py) contains scripts for creating tables (books, review, users). You can see uml-scheme [books.uml](books.uml) of the project database. The main function imports data from csv file.
**This script must be run first.**

#### Goodreads

[Goodreads.py](goodreads.py) contains the function get_rating(isbn). It works with api goodreads, gets the rating of the book, and returns dict with keys 'avg_rating' and 'reviews_count'. If the response was without data function returns the value "No data".

#### Application

[Application.py](application.py) contains functions:
- def _jinja2_filter_datetime(date, fmt=None). Custom filter for a date in templates. It used in [Book.html](templates/book.html) for reviews list.
- def login_required(f). Method for restricting access and authorization verification. Used like decorated function for index() and book().
- def index(). Function for the main page of the site. Only Get method. Route ('/'). It contains logic for queries from search and for pagination. Returns render template [index.html](templates/index.html).
- def book(book_id). Function for the book page. Method Get is for rendering template book page [book.html](templates/book.html) and Post is for saving review from [form_review.html](templates/form_review.html). Route ("/book/\<int:book_id>"). 
- def logout() is a standard function for logout.
- def login(). Get method renders the template [login.html](templates/login.html). Post method checks user data and log in user. Also return error messages if the form is incorrect.
- def register(). Get method renders the template [register.html](templates/register.html). Post method checks and save user data in users table. Also return error messages if the form is incorrect.
- def api_isbn(isbn). Only Get method returns a JSON response containing the book’s title, author, publication date, ISBN number, review count, and average score. If ISBN is incorrect returns ```{"error": "Invalid ISBN"}``` and status code 422, if isbn don't found returns ```{"error": "Book is not found"}``` and status code 404. The example of correct resulting JSON:
```json
{
  "ISBN": "0006551815", 
  "author": "Frank McCourt", 
  "average_score": 4.25, 
  "publication_date": 1999, 
  "review_count": 2, 
  "title": "'Tis: A Memoir"
}
``` 
