from flask import Flask, jsonify, render_template
from flask_cors import CORS
import feedparser
from datetime import datetime
import dateutil.parser

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)

# Use RSSHub feed instead of rss.app
RSS_URL = "https://rsshub.app/facebook/page/NCST.OfficialPage"

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/announcements")
def announcements():
    feed = feedparser.parse(RSS_URL)

    # If RSSHub didn’t return valid entries
    if not feed.entries:
        return jsonify({"error": "Feed is empty or invalid", "url": RSS_URL}), 500

    posts = []
    for entry in feed.entries[:10]:
        # Try to parse published date safely
        published_date = datetime.now()
        if hasattr(entry, "published"):
            try:
                published_date = dateutil.parser.parse(entry.published)
            except Exception:
                pass  # fallback to current time

        posts.append({
            "title": getattr(entry, "title", "No Title"),
            "link": getattr(entry, "link", "#"),
            "text": getattr(entry, "summary", ""),
            "image": (
                entry.get("media_thumbnail", [{}])[0].get("url")
                if "media_thumbnail" in entry
                else None
            ),
            "published": published_date.isoformat()
        })

    return jsonify(posts)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
