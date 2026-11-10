# scrape_books.py
import time
import csv
import sqlite3
import re
from urllib.parse import urljoin
from requests import Session
from bs4 import BeautifulSoup
from requests.exceptions import RequestException

# xlsx writing
from openpyxl import Workbook
from openpyxl.styles import numbers
from openpyxl.utils import get_column_letter

BASE_URL = "http://books.toscrape.com/"

session = Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (compatible; tutorial-bot/1.0; +https://example.local)"
})

RATING_MAP = {"One":1,"Two":2,"Three":3,"Four":4,"Five":5}

def parse_book_element(elem, page_url):
    a = elem.select_one("h3 a")
    title = a.get("title", "").strip()
    rel_link = a.get("href", "")
    link = urljoin(page_url, rel_link)

    price_elem = elem.select_one("p.price_color")
    price_text = price_elem.get_text(strip=True) if price_elem else ""

    availability_elem = elem.select_one("p.instock.availability")
    availability = availability_elem.get_text(strip=True) if availability_elem else ""

    rating_p = elem.select_one("p.star-rating")
    rating_classes = rating_p.get("class", []) if rating_p else []
    rating_word = next((c for c in rating_classes if c != "star-rating"), None)
    rating = RATING_MAP.get(rating_word, None)

    return {"title": title, "price": price_text, "availability": availability, "rating": rating, "link": link}

def scrape_page(url, max_retries=3):
    for attempt in range(max_retries):
        try:
            resp = session.get(url, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            items = [parse_book_element(el, url) for el in soup.select("article.product_pod")]
            next_a = soup.select_one("li.next a")
            next_url = urljoin(url, next_a["href"]) if next_a else None
            return items, next_url
        except RequestException as e:
            wait = 2 ** attempt
            print(f"Request error: {e}. Retrying in {wait}s...")
            time.sleep(wait)
    raise SystemExit(f"Failed to fetch {url} after {max_retries} attempts")

def save_to_csv(rows, filename="books.csv"):
    keys = ["title","price","availability","rating","link"]
    with open(filename, "w", newline="", encoding="utf-8-sig") as f:  # utf-8-sig for Excel
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved {len(rows)} rows to {filename}")

def save_to_sqlite(rows, dbname="books.db"):
    conn = sqlite3.connect(dbname)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            price TEXT,
            availability TEXT,
            rating INTEGER,
            link TEXT UNIQUE
        )
    """)
    for r in rows:
        cur.execute("""
            INSERT OR IGNORE INTO books (title, price, availability, rating, link)
            VALUES (?, ?, ?, ?, ?)
        """, (r["title"], r["price"], r["availability"], r["rating"], r["link"]))
    conn.commit()
    conn.close()
    print(f"Saved {len(rows)} rows to {dbname} (duplicates ignored)")

def parse_price_to_float(price_str):
    """Remove currency symbols and thousands separators and return float or None."""
    if price_str is None:
        return None
    # remove everything except digits, dot and minus
    cleaned = re.sub(r"[^\d\.\-]", "", price_str)
    try:
        return float(cleaned) if cleaned != "" else None
    except ValueError:
        return None

def save_to_excel_with_numeric_price(rows, filename="books_price_for_excel.xlsx"):
    """Write an .xlsx where price is numeric and formatted as £ currency."""
    if not rows:
        print("No rows to write to Excel.")
        return

    # Determine column order from keys
    keys = ["title","price","availability","rating","link"]
    wb = Workbook()
    ws = wb.active
    ws.title = "books"

    # Write header
    ws.append(keys)

    # Write rows, converting price to numeric
    price_col_index = keys.index("price") + 1  # 1-based
    for r in rows:
        row_values = []
        for k in keys:
            if k == "price":
                price_num = parse_price_to_float(r.get("price", ""))
                row_values.append(price_num)
            else:
                row_values.append(r.get(k, ""))
        ws.append(row_values)

    # Apply currency number format to the price column
    col_letter = get_column_letter(price_col_index)
    # apply to all data cells in that column
    for row in range(2, ws.max_row + 1):
        cell = ws[f"{col_letter}{row}"]
        # Only set format if the cell contains a number
        if isinstance(cell.value, (int, float)):
            cell.number_format = '"£"#,##0.00'  # forces pound formatting

    wb.save(filename)
    print(f"Wrote Excel file: {filename} (price column numeric + formatted)")

def main():
    url = BASE_URL
    all_books = []
    while url:
        print("Fetching:", url)
        items, url = scrape_page(url)
        all_books.extend(items)
        time.sleep(1)
    print("Total books scraped:", len(all_books))

    # Save to outputs
    save_to_csv(all_books, "books.csv")
    save_to_sqlite(all_books, "books.db")
    save_to_excel_with_numeric_price(all_books, "books_price_for_excel.xlsx")

if __name__ == "__main__":
    main()
