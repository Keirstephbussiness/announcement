from flask import Flask, jsonify, Response
from flask_cors import CORS
import requests
import feedparser
import xml.sax.saxutils as saxutils

app = Flask(__name__)
# Allow CORS from your frontend domain
CORS(app, resources={r"/api/*": {"origins": "*"}})  # * allows all origins, safer: put your Netlify URL

RSS_FEED_URL = "https://fetchrss.com/feed/aMKmuNc_E0HiaMKmTQ1GMV2S.rss"

@app.route("/")
def index():
    return "NCST RSS Feed Generator is running! Use /api/announcements to fetch the feed."

@app.route("/api/announcements")
def rss_feed():
    try:
        r = requests.get(RSS_FEED_URL, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        feed = feedparser.parse(r.text)

        # Get latest 5 entries
        items = feed.entries[:5]
        # Prepare JSON response
        announcements = []
        for item in items:
            announcement = {
                "title": saxutils.escape(item.get("title", "No Title")),
                "link": item.get("link", ""),
                "description": saxutils.escape(item.get("summary", "")),
                "pubDate": item.get("published", "")
            }
            announcements.append(announcement)

        # Structure the JSON response
        response_data = {
            "channel": {
                "title": "NCST Official Page",
                "link": "https://www.facebook.com/NCST.OfficialPage",
                "description": "Latest 5 posts from NCST Facebook Page",
                "items": announcements
            }
        }

        return jsonify(response_data)

    except Exception as e:
        return Response(f"Error fetching feed: {e}", status=500, mimetype="text/plain")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
