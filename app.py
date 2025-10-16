from flask import Flask, jsonify
from flask_cors import CORS
import requests
import feedparser
from bs4 import BeautifulSoup
import html
import random

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

RSS_FEED_URL = "https://rss.app/feeds/rJbibQK5cA6ohQZv.xml"
FALLBACK_URL = "https://www.ncst.edu.ph/news"  # official news/announcements page


# realistic desktop browser headers to bypass WAF
BROWSER_HEADERS = [
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/",
        "Connection": "keep-alive",
        "Accept-Encoding": "gzip, deflate, br"
    },
    {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
        "Accept": "*/*",
        "Referer": "https://www.google.com/"
    }
]


@app.route("/")
def index():
    return "✅ NCST Announcements API is online! Use /api/announcements to fetch data."


@app.route("/api/announcements")
def rss_feed():
    try:
        # STEP 1: Try RSS first
        try:
            headers = random.choice(BROWSER_HEADERS)
            r = requests.get(RSS_FEED_URL, timeout=15, headers=headers)
            r.raise_for_status()
            feed = feedparser.parse(r.text)

            if feed.entries:
                announcements = []
                for item in feed.entries[:5]:
                    summary_html = item.get("summary", "")
                    soup = BeautifulSoup(summary_html, "html.parser")

                    images = [img.get("src") for img in soup.find_all("img") if img.get("src")]
                    text = html.unescape(soup.get_text().strip())

                    announcements.append({
                        "title": html.unescape(item.get("title", "No Title")),
                        "link": item.get("link", ""),
                        "text": text,
                        "image": images[0] if images else "",
                        "pubDate": item.get("published", ""),
                        "author": item.get("author", ""),
                        "guid": item.get("id", "")
                    })

                return jsonify({"items": announcements, "source": "rss"}), 200

            raise ValueError("No valid RSS entries found")

        except Exception as e:
            print(f"⚠️ RSS failed: {e} — trying HTML fallback.")

            # STEP 2: Fallback — Scrape HTML directly
            headers = random.choice(BROWSER_HEADERS)
            page = requests.get(FALLBACK_URL, timeout=20, headers=headers)
            page.raise_for_status()

            soup = BeautifulSoup(page.text, "html.parser")
            articles = soup.select("article, .news-item, .post, .views-row")[:5]

            if not articles:
                raise ValueError("No recognizable announcements found in HTML fallback.")

            announcements = []
            for article in articles:
                title_el = article.select_one("h2, .title, a, .news-title")
                link_el = article.select_one("a[href]")
                img_el = article.select_one("img")
                date_el = article.select_one("time, .date, .post-date")
                desc_el = article.select_one("p, .summary, .excerpt")

                announcements.append({
                    "title": title_el.get_text(strip=True) if title_el else "No Title",
                    "link": link_el["href"] if link_el and link_el.has_attr("href") else "",
                    "text": desc_el.get_text(strip=True) if desc_el else "",
                    "image": img_el["src"] if img_el and img_el.has_attr("src") else "",
                    "pubDate": date_el.get_text(strip=True) if date_el else "",
                    "author": "NCST Official",
                    "guid": ""
                })

            return jsonify({"items": announcements, "source": "html_fallback"}), 200

    except requests.RequestException as e:
        return jsonify({"error": f"Network error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
