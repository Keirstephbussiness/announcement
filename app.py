from flask import Flask, Response
from flask_cors import CORS
import requests
import feedparser

app = Flask(__name__)
CORS(app)

# Correct RSSHub route for NCST Facebook page
RSSHUB_FEED_URL = "https://rsshub.app/facebook/page/NCST.OfficialPage"

@app.route("/")
def index():
    return "NCST RSS Feed Generator is running! Use /rss to fetch the feed."

@app.route("/rss")
def rss_feed():
    try:
        # Fetch from RSSHub
        r = requests.get(RSSHUB_FEED_URL, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        
        # Parse feed
        feed = feedparser.parse(r.text)
        if not feed.entries:
            return Response("No entries found in feed.", status=404)
        
        # Limit to 5 posts
        items = feed.entries[:5]
        
        # Build RSS XML
        rss_items = ""
        for item in items:
            rss_items += f"""
            <item>
                <title>{item.get("title", "No Title")}</title>
                <link>{item.get("link", "")}</link>
                <description><![CDATA[{item.get("summary", "")}]]></description>
                <pubDate>{item.get("published", "")}</pubDate>
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
        
        # Return with CORS headers
        response = Response(rss_xml, mimetype="application/rss+xml")
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        return response
        
    except Exception as e:
        return Response(f"Error fetching feed: {e}", status=500)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
