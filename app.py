from flask import Flask, jsonify
from flask_cors import CORS
import requests
import feedparser
from bs4 import BeautifulSoup
import html
import time

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

RSS_FEED_URL = "https://rss.app/feeds/rJbibQK5cA6ohQZv.xml"

@app.route("/")
def index():
    return "NCST RSS Feed Generator is running! Use /api/announcements to fetch the feed."

@app.route("/api/announcements")
def rss_feed():
    try:
        # Enhanced headers to bypass 403 Forbidden
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/rss+xml, application/xml, text/xml, application/atom+xml, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": "https://rss.app/",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Cache-Control": "max-age=0"
        }
        
        # Create session for better connection handling
        session = requests.Session()
        session.headers.update(headers)
        
        # Small delay to avoid rate limiting
        time.sleep(0.5)
        
        # Fetch the RSS feed
        r = session.get(RSS_FEED_URL, timeout=20, allow_redirects=True)
        r.raise_for_status()
        
        # Parse the feed
        feed = feedparser.parse(r.content)
        
        if not feed.entries:
            return jsonify({
                "items": [], 
                "message": "No entries found in the feed"
            }), 200
        
        announcements = []
        for item in feed.entries[:5]:  # latest 5
            # Extract images from summary/content
            images = []
            summary_html = item.get("summary", "")
            
            if summary_html:
                soup = BeautifulSoup(summary_html, "html.parser")
                for img in soup.find_all("img"):
                    img_src = img.get("src")
                    if img_src:
                        images.append(img_src)
                
                # Clean text content
                text = html.unescape(soup.get_text().strip())
            else:
                text = ""
            
            announcements.append({
                "title": html.unescape(item.get("title", "No Title")),
                "link": item.get("link", ""),
                "text": text,
                "image": images[0] if images else "",  # take first image if exists
                "pubDate": item.get("published", ""),
                "author": item.get("author", "Unknown"),
                "guid": item.get("id", "")
            })
        
        return jsonify({
            "items": announcements,
            "count": len(announcements),
            "message": "Success"
        }), 200
        
    except requests.HTTPError as e:
        error_msg = f"HTTP Error {e.response.status_code}: {str(e)}"
        print(f"HTTP Error: {error_msg}")
        
        # Return more specific error based on status code
        if e.response.status_code == 403:
            return jsonify({
                "error": "Access forbidden to RSS feed. The feed may require authentication or the URL may be private.",
                "suggestion": "Check if the RSS feed URL is public in your RSS.app dashboard"
            }), 403
        elif e.response.status_code == 404:
            return jsonify({
                "error": "RSS feed not found. The feed URL may be incorrect or no longer exists."
            }), 404
        else:
            return jsonify({"error": error_msg}), 500
            
    except requests.RequestException as e:
        error_msg = f"Failed to fetch RSS feed: {str(e)}"
        print(f"Request Error: {error_msg}")
        return jsonify({
            "error": error_msg,
            "suggestion": "Check your internet connection and the RSS feed URL"
        }), 500
        
    except Exception as e:
        error_msg = f"Error processing feed: {str(e)}"
        print(f"Processing Error: {error_msg}")
        return jsonify({
            "error": error_msg
        }), 500

# Health check endpoint
@app.route("/api/health")
def health_check():
    return jsonify({
        "status": "healthy",
        "message": "RSS Feed API is running"
    }), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
