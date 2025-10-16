from flask import Flask, jsonify
from flask_cors import CORS
import requests
import feedparser
from bs4 import BeautifulSoup
import html

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# RSS feed URL
RSS_FEED_URL = "https://rss.app/feeds/rJbibQK5cA6ohQZv.xml"

@app.route("/")
def index():
    return "✅ NCST RSS Feed API is running! Use /api/announcements to fetch the latest feed."

@app.route("/api/announcements")
def rss_feed():
    try:
        # Use realistic browser headers to avoid 403/406 errors
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/125.0.0.0 Safari/537.36",
            "Accept": "application/rss+xml, application/xml, text/xml;q=0.9, */*;q=0.8",
            "Referer": "https://www.google.com/",
            "Accept-Language": "en-US,en;q=0.9"
        }

        # Fetch RSS feed safely
        response = requests.get(RSS_FEED_URL, timeout=15, headers=headers)
        response.raise_for_status()  # Raise if 4xx or 5xx

        # Parse feed content
        feed = feedparser.parse(response.text)
        if not feed.entries:
            return jsonify({"items": [], "message": "No announcements found"}), 200

        announcements = []
        for item in feed.entries[:5]:  # limit to latest 5
            summary_html = item.get("summary", "")
            soup = BeautifulSoup(summary_html, "html.parser")

            # Extract image
            img = soup.find("img")
            image_url = img["src"] if img and img.has_attr("src") else ""

            # Clean text
            text = html.unescape(soup.get_text().strip())

            announcements.append({
                "title": html.unescape(item.get("title", "No Title")),
                "link": item.get("link", ""),
                "text": text,
                "image": image_url,
                "pubDate": item.get("published", ""),
                "author": item.get("author", ""),
                "guid": item.get("id", "")
            })

        return jsonify({"items": announcements}), 200

    except requests.RequestException as e:
        return jsonify({"error": f"Failed to fetch RSS feed: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Error processing feed: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
