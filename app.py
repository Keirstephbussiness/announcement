from flask import Flask, jsonify
from flask_cors import CORS
import requests
import feedparser
from bs4 import BeautifulSoup
import html

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

RSS_FEED_URL = "https://rss.app/feeds/rJbibQK5cA6ohQZv.xml"
# Fallback source (the actual NCST announcements page, replace if needed)
FALLBACK_URL = "https://www.ncst.edu.ph/news"  # ← change this if you have a more direct source


@app.route("/")
def index():
    return "✅ NCST RSS Feed Generator is running! Use /api/announcements to fetch the feed."


@app.route("/api/announcements")
def rss_feed():
    try:
        # STEP 1: Try fetching RSS feed
        try:
            r = requests.get(RSS_FEED_URL, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
            r.raise_for_status()
            feed = feedparser.parse(r.text)

            if not feed.entries:
                raise ValueError("No entries found in RSS feed")

            announcements = []
            for item in feed.entries[:5]:
                summary_html = item.get("summary", "")
                soup = BeautifulSoup(summary_html, "html.parser")

                # Extract image
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

        except Exception as e:
            # STEP 2: Fallback to HTML scraping if RSS fails
            print(f"⚠️ RSS fetch failed: {str(e)} — using HTML fallback.")
            html_page = requests.get(FALLBACK_URL, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
            html_page.raise_for_status()
            soup = BeautifulSoup(html_page.text, "html.parser")

            # Adapt these selectors based on NCST’s website structure
            articles = soup.select("article, .news-item, .post")[:5]

            if not articles:
                raise ValueError("No articles found on fallback page")

            announcements = []
            for article in articles:
                title_el = article.select_one("h2, .title, .news-title")
                link_el = article.select_one("a[href]")
                img_el = article.select_one("img")
                date_el = article.select_one(".date, time, .post-date")
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
