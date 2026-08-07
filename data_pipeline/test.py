import requests
from bs4 import BeautifulSoup

category_urls = {
    "Travel": "https://books.toscrape.com/catalogue/category/books/travel_2/index.html",
    "Mystery": "https://books.toscrape.com/catalogue/category/books/mystery_3/index.html",
    "Historical Fiction": "https://books.toscrape.com/catalogue/category/books/historical-fiction_4/index.html",
    "Classics": "https://books.toscrape.com/catalogue/category/books/classics_6/index.html",
}

#step 1: scrape the data 
all_books_data = []

for category_name, url in category_urls.items():
    response = requests.get(url)
    response.encoding = "utf-8"
    soup = BeautifulSoup(response.text, "html.parser")
    books = soup.find_all("article", class_="product_pod")

    for book in books:
        title = book.h3.a["title"]
        price_text = book.find("p", class_="price_color").text
        rating_text = book.find("p", class_="star-rating")["class"][1]
        availability_text = book.find("p", class_="instock availability").text.strip()

        book_data = {
            "title": title,
            "price": price_text,
            "star_rating": rating_text,
            "availability": availability_text,
            "category": category_name
        }
        all_books_data.append(book_data)

    print(f"{category_name}: scraped {len(books)} books")

print("\nGrand total:", len(all_books_data))


import pandas as pd

df = pd.DataFrame(all_books_data)
print(df.head())
print(df.dtypes)

#step 2.1: convert price to float
df["price_gbp"] = df["price"].str.replace("£", "", regex=False).astype(float)

print(df[["price", "price_gbp"]].head())
print(df["price_gbp"].dtype)

#step 2.2: convert star_rating to numeric
rating_map = {
    "One": 1,
    "Two": 2,
    "Three": 3,
    "Four": 4,
    "Five": 5
}

df["rating"] = df["star_rating"].map(rating_map)


print(df[["star_rating", "rating"]].head())
print(df["rating"].dtype)
print(df["rating"].isnull().sum())  

#step 2.3: clean availability 
# "In stock" -> True, anything else -> False
df["in_stock"] = df["availability"].str.contains("In stock")

print(df[["availability", "in_stock"]].head())
print(df["in_stock"].dtype)
print(df["in_stock"].value_counts())

#step 2.4: Check for any rows where price_gbp or rating failed to parse
broken_rows = df[df["price_gbp"].isnull() | df["rating"].isnull()]
print("Broken rows found:", len(broken_rows))

if len(broken_rows) > 0:
    # Fill missing numeric values with the median of that column
    df["price_gbp"] = df["price_gbp"].fillna(df["price_gbp"].median())
    df["rating"] = df["rating"].fillna(df["rating"].median())
    print("Filled missing values with median.")
else:
    print("No broken rows — nothing to fix.")

#step 3 : convert to price INR 
GBP_TO_INR = 105.50

df["price_inr"] = df["price_gbp"] * GBP_TO_INR

print(df[["price_gbp", "price_inr"]].head())
print(df["price_inr"].dtype)

#step 4: create atleast 2 sqlite databases 
import sqlite3

# Connect to (or create) the database file
conn = sqlite3.connect("books.db")
cursor = conn.cursor()

# Clear old data every time we run, so re-running never creates duplicates
cursor.execute("DELETE FROM books")
cursor.execute("DELETE FROM categories")
conn.commit()

# Create the categories table
cursor.execute("""
CREATE TABLE IF NOT EXISTS categories (
    category_id INTEGER PRIMARY KEY,
    category_name TEXT UNIQUE
)
""")

# Create the books table, linked to categories via category_id
cursor.execute("""
CREATE TABLE IF NOT EXISTS books (
    book_id INTEGER PRIMARY KEY,
    title TEXT,
    price_gbp REAL,
    price_inr REAL,
    rating INTEGER,
    in_stock INTEGER,
    category_id INTEGER REFERENCES categories(category_id)
)
""")

conn.commit()
print("Tables created successfully")

#step 5: insert data into the tables

# Insert unique categories first
unique_categories = df["category"].unique()

for cat in unique_categories:
    cursor.execute("INSERT OR IGNORE INTO categories (category_name) VALUES (?)", (cat,))

conn.commit()
print("Inserted", len(unique_categories), "categories")

# Now insert books, looking up each book's category_id
for _, row in df.iterrows():
    cursor.execute("SELECT category_id FROM categories WHERE category_name = ?", (row["category"],))
    category_id = cursor.fetchone()[0]

    cursor.execute("""
        INSERT INTO books (title, price_gbp, price_inr, rating, in_stock, category_id)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (row["title"], row["price_gbp"], row["price_inr"], row["rating"], int(row["in_stock"]), category_id))

conn.commit()
print("Inserted", len(df), "books")

#step 6: run required SQL queries
def run_query(description, query):
    print("\n---", description, "---")
    print("QUERY:", query.strip())
    cursor.execute(query)
    results = cursor.fetchall()
    for row in results:
        print(row)
    return results

# step 6.1 SELECT + WHERE — books priced above 40 GBP
q1 = run_query(
    "Books priced above £40",
    "SELECT title, price_gbp FROM books WHERE price_gbp > 40"
)

# step 6.2 ORDER BY + LIMIT — top 5 most expensive books
q2 = run_query(
    "Top 5 most expensive books",
    "SELECT title, price_gbp FROM books ORDER BY price_gbp DESC LIMIT 5"
)

# step 6.3 DISTINCT — list all distinct category names
q3 = run_query(
    "Distinct category names",
    "SELECT DISTINCT category_name FROM categories"
)

# step 6.4 BETWEEN — books priced between £20 and £30
q4 = run_query(
    "Books priced between £20 and £30",
    "SELECT title, price_gbp FROM books WHERE price_gbp BETWEEN 20 AND 30"
)

# step 6.5 JOIN — 10 highest-rated books per category (with category name shown)
q5 = run_query(
    "Top 10 highest-rated books with category name (JOIN)",
    """
    SELECT books.title, books.rating, categories.category_name
    FROM books
    JOIN categories ON books.category_id = categories.category_id
    ORDER BY books.rating DESC
    LIMIT 10
    """
)

#step 7: read back with pandas + reproduce JOIN using pd.merge

# Read two query results into DataFrames using pd.read_sql
df_expensive = pd.read_sql("SELECT title, price_gbp FROM books ORDER BY price_gbp DESC LIMIT 5", conn)
df_categories = pd.read_sql("SELECT * FROM categories", conn)

print("Top 5 expensive (via pd.read_sql):")
print(df_expensive)

# Read the full books table too, so we can do our own merge
df_books_full = pd.read_sql("SELECT * FROM books", conn)

# Reproduce the JOIN query using pd.merge instead of SQL
df_joined = pd.merge(df_books_full, df_categories, on="category_id")
df_joined_top10 = df_joined[["title", "rating", "category_name"]].sort_values("rating", ascending=False).head(10)

print("\nTop 10 highest-rated (via pd.merge):")
print(df_joined_top10)

# Compare with the original SQL JOIN result (q5) to show they match
print("\nOriginal SQL JOIN result (q5) for comparison:")
for row in q5:
    print(row)