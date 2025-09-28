import argparse
import time
import random
import re
import requests
from bs4 import BeautifulSoup
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import os

# ----------------- Configuration -----------------
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
]
HEADERS = {"Accept-Language": "en-US,en;q=0.9"}

def random_headers():
    h = HEADERS.copy()
    h["User-Agent"] = random.choice(USER_AGENTS)
    return h

def safe_sleep(min_sec=2, max_sec=5):
    time.sleep(random.uniform(min_sec, max_sec))

# ----------------- Selenium setup -----------------
def init_driver(chrome_driver_path):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    # Randomize Selenium User-Agent
    user_agent = random.choice(USER_AGENTS)
    options.add_argument(f"user-agent={user_agent}")
    service = Service(chrome_driver_path)
    driver = webdriver.Chrome(service=service, options=options)
    return driver

# ----------------- Requests for search -----------------
def fetch_url(url, session=None):
    session = session or requests.Session()
    for _ in range(3):
        try:
            r = session.get(url, headers=random_headers(), timeout=20)
            if r.status_code == 200:
                return r.text
        except Exception:
            time.sleep(3)
    return None

def build_search_url(query, page=1):
    from urllib.parse import quote_plus
    return f"https://www.amazon.com/s?k={quote_plus(query)}&page={page}"

# ----------------- Parse search results -----------------
def parse_search_results(html):
    soup = BeautifulSoup(html, "html.parser")
    results = []

    for container in soup.select("[data-asin]"):
        asin = container.get("data-asin", "").strip()
        if not asin:
            continue

        # Title
        title_tag = container.select_one("h2 a span")
        title = title_tag.get_text(strip=True) if title_tag else None

        # Short clean URL
        url = f"https://www.amazon.com/dp/{asin}"

        # Price
        price = None
        price_tag = container.select_one("span.a-price span.a-offscreen")
        if price_tag:
            price = price_tag.get_text(strip=True)

        results.append({
            "asin": asin,
            "title": title,
            "url": url,
            "price": price
        })

    return results

def scrape_search(query, pages=1):
    results = []
    session = requests.Session()
    for p in range(1, pages + 1):
        url = build_search_url(query, p)
        print(f"🔎 Fetching page {p}: {url}")
        html = fetch_url(url, session=session)
        if not html:
            print(f"❌ Failed to fetch page {p}")
            continue

        page_results = parse_search_results(html)
        print(f"✅ Found {len(page_results)} products on page {p}")
        results.extend(page_results)

        safe_sleep(5, 10)  # bigger delay helps avoid blocking

    return results

# ----------------- Parse product pages -----------------
def parse_product_page(html):
    soup = BeautifulSoup(html, "html.parser")
    data = {}

    # Title
    title_tag = soup.select_one("#productTitle")
    data["title"] = title_tag.get_text(strip=True) if title_tag else None

    # Price (multiple fallbacks)
    price_tag = (
        soup.select_one("span.a-price span.a-offscreen")
        or soup.select_one("#priceblock_ourprice")
        or soup.select_one("#priceblock_dealprice")
    )
    data["price"] = price_tag.get_text(strip=True) if price_tag else None

    # Rating
    rating_tag = soup.select_one("span[data-asin][data-asin-rating]") or soup.select_one("i.a-icon-star span")
    data["rating"] = rating_tag.get_text(strip=True) if rating_tag else None

    # Review count
    review_tag = soup.select_one("#acrCustomerReviewText")
    data["review_count"] = review_tag.get_text(strip=True) if review_tag else None

    # Availability
    avail_tag = soup.select_one("#availability")
    data["availability"] = avail_tag.get_text(strip=True) if avail_tag else None

    # Images
    images = []
    for img in soup.select("#altImages img"):
        src = img.get("src")
        if src:
            images.append(re.sub(r"\._[A-Z0-9,]+_\.", ".", src))
    data["images"] = images

    return data

# ----------------- Fetch product details via Selenium -----------------
def fetch_product_details(products, driver):
    details = []

    def fetch(item):
        try:
            if not item.get("url"):
                return {**item, "error": "no_url"}
            driver.get(item["url"])
            time.sleep(random.uniform(3, 6))  # random delay to mimic human browsing
            html = driver.page_source
            data = parse_product_page(html)
            return {**item, **data}
        except Exception:
            return {**item, "error": "failed"}

    with ThreadPoolExecutor(max_workers=3) as executor:  # safer concurrency
        futures = [executor.submit(fetch, p) for p in products]
        for f in futures:
            try:
                details.append(f.result())
            except Exception:
                continue
    return details

# ----------------- Save results (robust) -----------------
def save_results(rows, out_path="results.csv"):
    """
    Tries to save results to out_path. If PermissionError (file locked), increments
    filename: base_1.csv, base_2.csv, ...
    Returns the final path that was written (or None on failure).
    """
    df = pd.DataFrame(rows)
    base, ext = os.path.splitext(out_path)
    if ext == "":
        ext = ".csv"
    attempt = 0
    max_attempts = 10

    while attempt < max_attempts:
        target = out_path if attempt == 0 else f"{base}_{attempt}{ext}"
        try:
            if ext.lower() == ".csv":
                df.to_csv(target, index=False)
            elif ext.lower() == ".json":
                df.to_json(target, orient="records", indent=2, force_ascii=False)
            elif ext.lower() == ".xlsx":
                df.to_excel(target, index=False)
            else:
                df.to_csv(target, index=False)

            print(f"✅ Saved results to {target}")
            return target
        except PermissionError:
            attempt += 1
            print(f"⚠️  PermissionError while writing {target}. Trying {base}_{attempt}{ext} ...")
            time.sleep(0.5)
            continue
        except Exception as e:
            attempt += 1
            print(f"❌ Error saving to {target}: {e}. Retrying with {base}_{attempt}{ext} ...")
            time.sleep(0.5)
            continue

    print("❌ Failed to save results after multiple attempts.")
    return None

# ----------------- Main -----------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", help="Search query")
    parser.add_argument("--pages", type=int, default=1, help="Number of search pages")
    parser.add_argument("--out", default="results.csv", help="Output file")
    args = parser.parse_args()

    if not args.query:
        args.query = input("Enter search query: ")

    driver = init_driver("C:/Users/Dell/Documents/chromedriver.exe")  # <-- your actual path

    summaries = []
    details = []
    saved_path = None

    try:
        summaries = scrape_search(args.query, pages=args.pages)
        details = fetch_product_details(summaries, driver)
        saved_path = save_results(details, args.out)
        print(f"✅ Scraped {len(details)} products. Saved to {saved_path or args.out}")
    except KeyboardInterrupt:
        # Save partial results if user hits Ctrl+C
        print("\n⏸️  Interrupted by user — saving partial results...")
        saved_path = save_results(details or summaries, args.out)
        print(f"Partial results saved to {saved_path or args.out}")
    except Exception as e:
        # Save what we have and print error
        print(f"\n❌ Unexpected error: {e}\nAttempting to save collected results...")
        saved_path = save_results(details or summaries, args.out)
        print(f"Saved partial results to {saved_path or args.out}")
    finally:
        try:
            driver.quit()
        except Exception:
            pass

if __name__ == "__main__":
    main()
