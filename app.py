from flask import Flask, jsonify
from flask_cors import CORS
import requests
import feedparser
from bs4 import BeautifulSoup
import html

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Primary RSS feed (blocked sometimes)
RSS_FEED_URL = "https://rss.app/feeds/rJbibQK5cA6ohQZv.xml"
# Fallback RSS-to-JSON proxy
RSS_PROXY_URL = f"https://api.rss2json.com/v1/api.json?rss_url={RSS_FEED_URL}"

@app.route("/")
def index():
    return "✅ NCST RSS Feed Generator is running! Use /api/announcements to fetch the feed."

@app.route("/api/announcements")
def rss_feed():
    try:
        # Try direct fetch first
        try:
            r = requests.get(RSS_FEED_URL, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
            r.raise_for_status()
            feed = feedparser.parse(r.text)

            if not feed.entries:
                raise ValueError("No entries found in direct RSS")

            data_source = "direct"
        except Exception as e:
            # Fall back to rss2json proxy if direct RSS fails (403, timeout, etc.)
            r = requests.get(RSS_PROXY_URL, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
            r.raise_for_status()
            json_data = r.json()

            if "items" not in json_data or not json_data["items"]:
                raise ValueError("No entries found in proxy RSS")

            # Convert rss2json items into standard format
            feed = {"entries": []}
            for item in json_data["items"]:
                feed["entries"].append({
                    "title": item.get("title", "No Title"),
                    "link": item.get("link", ""),
                    "summary": item.get("description", ""),
                    "published": item.get("pubDate", ""),
                    "author": item.get("author", ""),
                    "id": item.get("guid", "")
                })
            data_source = "proxy"

        # Parse and clean the feed
        announcements = []
        for item in feed["entries"][:5]:  # limit to latest 5
            summary_html = item.get("summary", "")
            soup = BeautifulSoup(summary_html, "html.parser")

            # Extract images
            images = [img.get("src") for img in soup.find_all("img") if img.get("src")]

            # Clean text
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

        return jsonify({
            "items": announcements,
            "source": data_source
        }), 200

    except requests.RequestException as e:
        return jsonify({"error": f"Failed to fetch RSS feed: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Error processing feed: {str(e)}"}), 500


if __name__ == "__main__":
    # Run on all interfaces, suitable for production or deployment on Render, Vercel, or Replit
    app.run(host="0.0.0.0", port=5000, debug=True)
