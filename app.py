from flask import Flask, jsonify, render_template
from flask_cors import CORS
import feedparser
from datetime import datetime
import dateutil.parser

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)

# Free RSS feed via RSSHub instead of rss.app (no trial)
RSS_URL = "https://rsshub.app/facebook/page/NCST.OfficialPage"

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/announcements")
def announcements():
    feed = feedparser.parse(RSS_URL)

    if not feed.entries:
        return jsonify({"error": "Failed to fetch feed"}), 500

    posts = []
    for entry in feed.entries[:10]:
        # Parse the published date safely
        try:
            published_date = dateutil.parser.parse(entry.published)
        except Exception:
            published_date = datetime.now()

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
    app.run(host="0.0.0.0", port=5000)
