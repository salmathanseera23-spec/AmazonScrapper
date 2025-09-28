# 🛒 Amazon Product Scraper

This project is a **Python-based Amazon Product Scraper** that automates the process of extracting product information such as titles, prices, ratings, reviews, availability, and product images. The results are saved into a CSV, JSON, or Excel file for easy access and analysis.

---

## 🔎 Features

* Search Amazon for any product query.
* Scrape product details including:

  * Title
  * Price
  * Rating
  * Number of reviews
  * Availability
  * Image links
* Save results in multiple formats (`.csv`, `.json`, `.xlsx`).
* Robust error handling with retries and backup saving.
* Supports headless browsing using **Selenium**.

---

## ⚙️ Technologies Used

* **Python 3**
* **Selenium** (to simulate real browser behavior and bypass dynamic content restrictions)
* **BeautifulSoup** (for parsing HTML and extracting details)
* **Pandas** (for structured data storage and export)
* **Requests** (for fetching Amazon search results)

---

## 🛠️ How It Works

1. The user provides a search query (e.g., *"Laptop"*).
2. The script fetches Amazon search results using `requests`.
3. Product summary details (ASIN, title, price, URL) are collected.
4. **Selenium with ChromeDriver** is used to load each product page and extract deeper details (reviews, ratings, images, availability).
5. The scraped data is saved into a file for further analysis.

---

## 🚀 Future Enhancements

* Add proxy rotation and request throttling to avoid IP blocking.
* Build a simple web interface for non-technical users.
* Extend support to other e-commerce platforms.

---

## 📂 Output Example

A sample CSV file includes:

| ASIN       | Title               | Price  | Rating | Reviews | Availability |
| ---------- | ------------------- | ------ | ------ | ------- | ------------ |
| B09ABC1234 | Fast Charging Cable | $12.99 | 4.5/5  | 1,234   | In Stock     |

---

This project was a hands-on learning experience in **web scraping, browser automation, and handling real-world errors** while working with dynamic websites like Amazon.
