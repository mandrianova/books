import csv
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker


engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

db.execute("CREATE TABLE IF NOT EXISTS books (id serial PRIMARY KEY, "
           "isbn VARCHAR(10) UNIQUE NOT NULL , "
           "title VARCHAR(255) NOT NULL, "
           "author VARCHAR(255) NOT NULL, "
           "year INTEGER NOT NULL)")
db.commit()


db.execute("CREATE TABLE IF NOT EXISTS users (id serial PRIMARY KEY, "
           "username VARCHAR(255) UNIQUE NOT NULL , "
           "hash VARCHAR(255) NOT NULL)")
db.commit()


db.execute("CREATE TABLE IF NOT EXISTS reviews (id serial PRIMARY KEY, "
           "review TEXT NOT NULL, user_id int NOT NULL, book_id int NOT NULL, date TIMESTAMP DEFAULT NOW(),"
           "rating NUMERIC CHECK ( rating > 0 AND rating <= 5) NOT NULL,"
           "constraint FK_reviews_user foreign key (user_id) references users(id),"
           "constraint FK_reviews_book foreign key (book_id) references books(id))")
db.commit()


def main():
    with open("books.csv", 'r') as books:
        reader = csv.DictReader(books)
        for row in reader:
            row['year'] = int(row['year'])
            db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)",
                       row)
        db.commit()


if __name__ == "__main__":
    main()