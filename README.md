# Web Data Extraction

Python scrapers that collect structured data from websites, built and tested on two sandbox sites designed for scraping: [Books to Scrape](http://books.toscrape.com/) and [Quotes to Scrape](http://quotes.toscrape.com/).

This is part of a series: static sites first, then a JavaScript-rendered site, then a real-world scraping project (coming next).

## What's here

| Script | What it does | Output |
|---|---|---|
| `scrape_books.py` | Walks through all 50 catalogue pages and collects each book's title, price, stock status, star rating and link | `books.csv`, `books.db` (SQLite), `books_price_for_excel.xlsx` |
| `scrape_quotes.py` | Walks through every page and collects each quote, its author and its tags | `quotes_all_pages.csv` |

### JavaScript-rendered quotes (`quotes-js/`)

The [JavaScript version of Quotes to Scrape](https://quotes.toscrape.com/js/) doesn't put the quotes in the page's HTML, so the usual approach finds nothing. Instead, the quotes sit inside the page's JavaScript as a block of data (`var data = [...]`). These notebooks find that block, cut it out, convert it into Python data with `json.loads`, and follow the pages until there are none left. No browser automation needed.

| Notebook | What it does | Output |
|---|---|---|
| `quotes_js_two_pages_clean.ipynb` | Scrapes the first two pages and cleans the result into separate columns (author name, Goodreads link, tags) | `twopages_quotes_js_clean.csv` |
| `quotes_js_all_pages.ipynb` | Scrapes all 10 pages (100 quotes), rewritten from memory as a test of what I'd learned | `allpages_quotes_js.csv` |

## Techniques used

- **Following pagination:** finding the "next" link on each page until there are no more pages
- **Parsing HTML** with BeautifulSoup and CSS selectors
- **Extracting data hidden in JavaScript:** finding the data inside a `<script>` tag and turning it into Python data with `json.loads`
- **Being polite to the server:** a one-second pause between requests and a clear User-Agent
- **Handling failures:** retrying failed requests with an increasing wait (exponential backoff)
- **Cleaning data:** converting star ratings from words to numbers, and prices from text to numbers
- **Saving to different formats:** CSV, a SQLite database (skipping duplicates), and Excel with the price formatted as currency

## Running it

```
pip install -r requirements.txt
python scrape_books.py
python scrape_quotes.py
```

The `quotes-js/` notebooks run in Jupyter.
