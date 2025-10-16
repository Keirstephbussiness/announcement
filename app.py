from flask import Flask, jsonify
from flask_cors import CORS
import requests
import feedparser
from bs4 import BeautifulSoup
import html
import time

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Use the new FetchRSS feed URL
RSS_FEED_URL = "https://fetchrss.com/feed/aPCvHIJ2trTSaPCu6VTnPmhj.rss"

@app.route("/")
def index():
    return "NCST RSS Feed Generator is running! Use /api/announcements to fetch the feed."

@app.route("/api/announcements")
def rss_feed():
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0.0.0 Safari/537.36"
        }

        # Small delay to avoid rate limiting
        time.sleep(0.5)

        # Fetch the RSS feed
        r = requests.get(RSS_FEED_URL, headers=headers, timeout=20)
        r.raise_for_status()

        # Parse the feed
        feed = feedparser.parse(r.content)

        if not feed.entries:
            return jsonify({
                "items": [],
                "message": "No entries found in the feed"
            }), 200

        announcements = []
        for item in feed.entries[:5]:  # latest 5
            summary_html = item.get("summary", "")
            text = ""
            images = []

            if summary_html:
                soup = BeautifulSoup(summary_html, "html.parser")
                for img in soup.find_all("img"):
                    if img.get("src"):
                        images.append(img["src"])
                text = html.unescape(soup.get_text().strip())

            announcements.append({
                "title": html.unescape(item.get("title", "No Title")),
                "link": item.get("link", ""),
                "text": text,
                "image": images[0] if images else "",
                "pubDate": item.get("published", ""),
                "author": item.get("author", "Unknown"),
                "guid": item.get("id", "")
            })

        return jsonify({
            "items": announcements,
            "count": len(announcements),
            "message": "Success"
        }), 200

    except requests.HTTPError as e:
        return jsonify({"error": f"HTTP Error {e.response.status_code}: {str(e)}"}), e.response.status_code
    except requests.RequestException as e:
        return jsonify({"error": f"Failed to fetch RSS feed: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Error processing feed: {str(e)}"}), 500

@app.route("/api/health")
def health_check():
    return jsonify({
        "status": "healthy",
        "message": "RSS Feed API is running"
    }), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
