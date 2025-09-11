from flask import Flask, Response
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

        items = feed.entries[:5]  # get latest 5
        rss_items = ""
        for item in items:
            title = saxutils.escape(item.get("title", "No Title"))
            summary = saxutils.escape(item.get("summary", ""))
            link = item.get("link", "")
            pubDate = item.get("published", "")

            rss_items += f"""
            <item>
                <title>{title}</title>
                <link>{link}</link>
                <description><![CDATA[{summary}]]></description>
                <pubDate>{pubDate}</pubDate>
            </item>
            """

        rss_xml = f"""<?xml version="1.0" encoding="UTF-8" ?>
        <rss version="2.0">
            <channel>
                <title>NCST Official Page</title>
                <link>https://www.facebook.com/NCST.OfficialPage</link>
                <description>Latest 5 posts from NCST Facebook Page</description>
                {rss_items}
            </channel>
        </rss>
        """

        return Response(rss_xml, mimetype="application/rss+xml")

    except Exception as e:
        return Response(f"Error fetching feed: {e}", status=500, mimetype="text/plain")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
