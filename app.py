from flask import Flask, jsonify, render_template
from flask_cors import CORS
import feedparser
from datetime import datetime
import dateutil.parser

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)

RSS_URL = "https://rss.app/feeds/rJbibQK5cA6ohQZv.xml"

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/announcements")
def announcements():
    feed = feedparser.parse(RSS_URL)
    posts = []
    for entry in feed.entries[:10]:
        # Parse the published date if available, otherwise use current date as fallback
        published_date = dateutil.parser.parse(entry.published) if hasattr(entry, "published") else datetime.now()
        posts.append({
            "title": entry.title,
            "link": entry.link,
            "text": entry.summary if hasattr(entry, "summary") else "",
            "image": entry.get("media_thumbnail", [{}])[0].get("url") if entry.get("media_thumbnail") else None,
            "published": published_date.isoformat()  # ISO 8601 format for JavaScript compatibility
        })
    return jsonify(posts)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
