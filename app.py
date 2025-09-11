from flask import Flask, Response
from flask_cors import CORS
import requests
import feedparser
import logging

app = Flask(__name__)
# Configure CORS to allow only the specific origin
CORS(app, resources={r"/api/*": {"origins": "https://ncst-newsfeed.netlify.app"}})

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Correct RSSHub route for NCST Facebook page
RSSHUB_FEED_URL = "https://rsshub.app/facebook/page/NCST.OfficialPage"

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@app.route("/")
def index():
    return "NCST RSS Feed Generator is running! Use /api/announcements to fetch the feed."

@app.route("/api/announcements")
def rss_feed():
    try:
        # Fetch from RSSHub with a slightly increased timeout
        r = requests.get(RSSHUB_FEED_URL, timeout=15, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
        r.raise_for_status()  # Raises an HTTPError for bad responses
        logger.info("Successfully fetched RSS feed from RSSHub")

        # Parse feed
        feed = feedparser.parse(r.text)
        if feed.bozo:
            logger.error(f"Feed parsing error: {feed.bozo_exception}")
            return Response(f"Error parsing feed: {feed.bozo_exception}", status=500)
        if not feed.entries:
            logger.warning("No entries found in feed")
            return Response("No entries found in feed.", status=404)

        # Limit to 5 posts
        items = feed.entries[:5]

        # Build RSS XML
        rss_items = ""
        for item in items:
            title = item.get("title", "No Title").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            summary = item.get("summary", "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            rss_items += f"""
            <item>
                <title>{title}</title>
                <link>{item.get("link", "")}</link>
                <description><![CDATA[{summary}]]></description>
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
        return response

    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error fetching RSS feed: {http_err}")
        return Response(f"Error fetching feed: HTTP {http_err.response.status_code}", status=500)
    except requests.exceptions.RequestException as req_err:
        logger.error(f"Network error fetching RSS feed: {req_err}")
        return Response(f"Error fetching feed: Network issue - {req_err}", status=500)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return Response(f"Error fetching feed: {e}", status=500)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
