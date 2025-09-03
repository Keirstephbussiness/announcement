from flask import Flask, jsonify, render_template
from flask_cors import CORS
import feedparser

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
        posts.append({
            "title": entry.title,
            "link": entry.link,
            "text": entry.summary if hasattr(entry, "summary") else "",
            "image": entry.get("media_thumbnail", [{}])[0].get("url") if entry.get("media_thumbnail") else None
        })
    return jsonify(posts)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
