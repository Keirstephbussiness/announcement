from flask import Flask, jsonify, Response
from flask_cors import CORS
import requests
import feedparser
import xml.sax.saxutils as saxutils

app = Flask(__name__)
# Allow CORS from your frontend domain
CORS(app, resources={r"/api/*": {"origins": "*"}})  # Replace * with your frontend URL in production

RSS_FEED_URL = "https://fetchrss.com/feed/aMKmuNc_E0HiaMKmTQ1GMV2S.rss"

@app.route("/")
def index():
    return "NCST RSS Feed Generator is running! Use /api/announcements to fetch the feed."

@app.route("/api/announcements")
def rss_feed():
    try:
        # Fetch the RSS feed
        r = requests.get(RSS_FEED_URL, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()  # Raise exception for HTTP errors
        feed = feedparser.parse(r.text)

        # Check if feed has entries
        if not feed.entries:
            return jsonify({
                "channel": {
                    "title": "NCST Official Page",
                    "link": "https://www.facebook.com/NCST.OfficialPage",
                    "description": "Latest posts from NCST Facebook Page",
                    "items": []
                },
                "message": "No entries found in the RSS feed"
            }), 200

        # Get latest 5 entries
        items = feed.entries[:5]
        announcements = []
        for item in items:
            announcement = {
                "title": saxutils.escape(item.get("title", "No Title")),
                "link": item.get("link", ""),
                "description": saxutils.escape(item.get("summary", "")),
                "pubDate": item.get("published", ""),
                "author": item.get("author", ""),  # Include author if available
                "guid": item.get("guid", "")  # Include guid for uniqueness
            }
            announcements.append(announcement)

        # Structure the JSON response
        response_data = {
            "channel": {
                "title": feed.feed.get("title", "NCST Official Page"),
                "link": feed.feed.get("link", "https://www.facebook.com/NCST.OfficialPage"),
                "description": feed.feed.get("description", "Latest posts from NCST Facebook Page"),
                "items": announcements
            }
        }

        return jsonify(response_data)

    except requests.RequestException as e:
        return jsonify({"error": f"Failed to fetch RSS feed: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Error processing feed: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
