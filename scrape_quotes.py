from requests import Session
from bs4 import BeautifulSoup
import csv
import time
from urllib.parse import urljoin

BASE_URL = "http://quotes.toscrape.com"

session = Session()
session.headers.update({'User-Agent': 'Mozilla/5.0 (compatible; tutorial-bot/1.0)'})

def scrape_page(url):
    resp = session.get(url, timeout=10)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")  # avoids lxml install issues
    items = []
    for q in soup.select('div.quote'):
        text = q.select_one('span.text').get_text(strip=True)
        author = q.select_one('small.author').get_text(strip=True)
        tags = [t.get_text(strip=True) for t in q.select('div.tags a.tag')]
        items.append({'text': text, 'author': author, 'tags': ",".join(tags)})
    next_link = soup.select_one('li.next a')
    next_url = urljoin(url, next_link['href']) if next_link else None
    return items, next_url

def main():
    url = BASE_URL
    all_quotes = []
    while url:
        print("Fetching:", url)
        try:
            items, url = scrape_page(url)
        except Exception as e:
            print("Error fetching", url, "->", e)
            break
        all_quotes.extend(items)
        time.sleep(1)  # polite delay

    keys = ['text', 'author', 'tags']
    with open('quotes_all_pages.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(all_quotes)

    print(f"Saved {len(all_quotes)} quotes to quotes_all_pages.csv")

if __name__ == "__main__":
    main()
