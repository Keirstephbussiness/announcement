from flask import Flask, jsonify
from flask_cors import CORS
import requests
import feedparser
from cachetools import TTLCache, cached
import logging

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "https://ncst-newsfeed.netlify.app"}})

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

RSS_FEED_URL = "https://fetchrss.com/feed/aMKmuNc_E0HiaMKmTQ1GMV2S.rss"

cache = TTLCache(maxsize=1, ttl=600)

@cached(cache)
def fetch_rss_feed():
    try:
        r = requests.get(RSS_FEED_URL, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        return r.text, None
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching RSS feed: {e}")
        return None, str(e)

@app.route("/api/announcements")
def rss_feed_json():
    feed_data, error = fetch_rss_feed()
    if error:
        return jsonify({"error": f"Failed to fetch RSS feed: {error}"}), 500

    feed = feedparser.parse(feed_data)
    posts = []
    for entry in feed.entries[:5]:
        posts.append({
            "title": entry.get("title", "No Title"),
            "link": entry.get("link", ""),
            "summary": entry.get("summary", ""),
            "published": entry.get("published", "")
        })

    return jsonify({"posts": posts})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
