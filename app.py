from flask import Flask, Response
from flask_cors import CORS
import requests
import feedparser
import logging
import xml.sax.saxutils as saxutils
from cachetools import TTLCache, cached

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "https://ncst-newsfeed.netlify.app"}})

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Use your FetchRSS feed URL
RSS_FEED_URL = "https://fetchrss.com/feed/aMKmuNc_E0HiaMKmTQ1GMV2S.rss"

# Cache RSS feed for 10 minutes
cache = TTLCache(maxsize=1, ttl=600)

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@app.route("/")
def index():
    return "NCST RSS Feed Generator is running! Use /api/announcements to fetch the feed."

@cached(cache)
def fetch_rss_feed():
    try:
        logger.info(f"Fetching RSS feed from {RSS_FEED_URL}")
        r = requests.get(RSS_FEED_URL, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        logger.info("Successfully fetched RSS feed")
        return r.text, None
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error: {http_err}")
        retry_after = http_err.response.headers.get('Retry-After')
        return None, (http_err.response.status_code, str(http_err), retry_after)
    except requests.exceptions.RequestException as req_err:
        logger.error(f"Network error: {req_err}")
        return None, (500, f"Network issue - {req_err}", None)

@app.route("/api/announcements")
def rss_feed():
    try:
        feed_data, error = fetch_rss_feed()
        if error:
            status_code, error_msg, retry_after = error
            response = Response(f"Error fetching feed: {error_msg}", status=status_code, mimetype="text/plain")
            if retry_after:
                response.headers.add('Retry-After', retry_after)
            return response

        feed = feedparser.parse(feed_data)
        if feed.bozo:
            logger.error(f"Feed parsing error: {feed.bozo_exception}")
            return Response(f"Error parsing feed: {feed.bozo_exception}", status=500, mimetype="text/plain")
        if not feed.entries:
            logger.warning("No entries found in feed")
            return Response("No entries found in feed.", status=404, mimetype="text/plain")

        items = feed.entries[:5]
        rss_items = ""
        for item in items:
            title = saxutils.escape(item.get("title", "No Title"))
            summary = saxutils.escape(item.get("summary", ""))
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

        return Response(rss_xml, mimetype="application/rss+xml")

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return Response(f"Error processing feed: {e}", status=500, mimetype="text/plain")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
