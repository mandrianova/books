import os

import requests


KEY = os.getenv("GOOD_KEY")


def get_rating(isbn):
    rating = {"avg_rating": "No data", "reviews_count": "No data"}
    url = "https://www.goodreads.com/book/review_counts.json"
    req = requests.get("{}?isbns={}&key={}".format(url, isbn, KEY))
    if req.status_code != 200:
        return rating
    result = req.json()
    if result:
        rating['avg_rating'] = result["books"][0]["average_rating"]
        rating['reviews_count'] = result["books"][0]["reviews_count"]
    return rating


if __name__ == "__main__":
    print(get_rating('0439598389'))
