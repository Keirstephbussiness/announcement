from flask import Flask, jsonify, render_template
from flask_cors import CORS
import feedparser

app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app)

# Change this to the real NCST RSS feed or an RSSHub link
rss_url = "https://rsshub.app/facebook/page/NCST.OfficialPage"

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/announcements")
def get_announcements():
    feed = feedparser.parse(rss_url)
    announcements = []

    for entry in feed.entries[:10]:  # latest 10 posts
        announcements.append({
            "title": entry.title if "title" in entry else "No title",
            "text": entry.summary if "summary" in entry else "",
            "link": entry.link if "link" in entry else "#",
            "image": entry.media_content[0]["url"] if "media_content" in entry else None
        })

    return jsonify(announcements)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
