from flask import Flask, jsonify
from flask_cors import CORS
import requests
import feedparser
from bs4 import BeautifulSoup
import html

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

RSS_FEED_URL = "https://rss.app/feeds/rJbibQK5cA6ohQZv.xml"

@app.route("/")
def index():
    return "NCST RSS Feed Generator is running! Use /api/announcements to fetch the feed."

@app.route("/api/announcements")
def rss_feed():
    try:
        r = requests.get(RSS_FEED_URL, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        feed = feedparser.parse(r.text)

        if not feed.entries:
            return jsonify({"items": [], "message": "No entries found"}), 200

        announcements = []
        for item in feed.entries[:5]:  # latest 5
            # Extract images from summary/content
            images = []
            summary_html = item.get("summary", "")
            soup = BeautifulSoup(summary_html, "html.parser")
            for img in soup.find_all("img"):
                images.append(img.get("src"))

            # Clean text content
            text = html.unescape(soup.get_text())

            announcements.append({
                "title": html.unescape(item.get("title", "No Title")),
                "link": item.get("link", ""),
                "text": text,
                "image": images[0] if images else "",  # take first image if exists
                "pubDate": item.get("published", ""),
                "author": item.get("author", ""),
                "guid": item.get("id", "")
            })

        return jsonify({"items": announcements})

    except requests.RequestException as e:
        return jsonify({"error": f"Failed to fetch RSS feed: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Error processing feed: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
