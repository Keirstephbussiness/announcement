from flask import Flask, Response
import requests
import feedparser

app = Flask(__name__)

# RSSHub route for NCST official page (no cookie)
RSSHUB_FEED_URL = "https://rsshub.app/facebook/page/NCST.OfficialPage"

@app.route("/")
def index():
    return "NCST RSS feed is running!"

@app.route("/rss")
def rss_feed():
    try:
        # Fetch the feed from RSSHub
        r = requests.get(RSSHUB_FEED_URL, timeout=10)
        r.raise_for_status()

        # Parse feed
        feed = feedparser.parse(r.text)

        # Take only the latest 5 posts
        items = feed.entries[:5]

        # Build RSS XML manually
        rss_items = ""
        for item in items:
            rss_items += f"""
            <item>
                <title>{item.title}</title>
                <link>{item.link}</link>
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

        return Response(rss_xml, mimetype="application/rss+xml")

    except Exception as e:
        return Response(f"Error fetching feed: {e}", status=500)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
