from flask import Flask, jsonify, render_template
from flask_cors import CORS
import feedparser
from datetime import datetime
import dateutil.parser
import traceback

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)

# RSS URL
RSS_URL = "https://rsshub.app/facebook/page/NCST.OfficialPage"

@app.route("/")
def home():
    try:
        return render_template("index.html")
    except Exception:
        # If template doesn't exist, return a simple HTML page
        return '''
        <html>
        <head><title>RSS Feed App</title></head>
        <body>
            <h1>RSS Feed App</h1>
            <p>API endpoint: <a href="/api/announcements">/api/announcements</a></p>
        </body>
        </html>
        '''

@app.route("/api/announcements")
def announcements():
    try:
        print(f"Fetching RSS from: {RSS_URL}")
        
        # Parse the RSS feed
        feed = feedparser.parse(RSS_URL)
        
        # Check if feed parsing was successful
        if hasattr(feed, 'bozo') and feed.bozo:
            print(f"Feed parsing warning: {getattr(feed, 'bozo_exception', 'Unknown error')}")
        
        print(f"Feed title: {getattr(feed.feed, 'title', 'No title')}")
        print(f"Number of entries: {len(feed.entries)}")
        
        # If no entries found
        if not feed.entries:
            return jsonify({
                "error": "No entries found in RSS feed",
                "url": RSS_URL,
                "feed_title": getattr(feed.feed, 'title', 'Unknown'),
                "entries_count": len(feed.entries)
            }), 404

        posts = []
        for i, entry in enumerate(feed.entries[:10]):
            try:
                # Parse published date
                published_date = datetime.now()
                date_string = None
                
                if hasattr(entry, 'published') and entry.published:
                    date_string = entry.published
                elif hasattr(entry, 'updated') and entry.updated:
                    date_string = entry.updated
                elif hasattr(entry, 'created') and entry.created:
                    date_string = entry.created
                
                if date_string:
                    try:
                        published_date = dateutil.parser.parse(date_string)
                    except Exception as e:
                        print(f"Date parsing error for entry {i}: {e}")

                # Extract image URL
                image_url = None
                try:
                    # Try different image sources
                    if hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
                        image_url = entry.media_thumbnail[0].get('url')
                    elif hasattr(entry, 'media_content') and entry.media_content:
                        image_url = entry.media_content[0].get('url')
                    elif hasattr(entry, 'links'):
                        for link in entry.links:
                            if 'image' in link.get('type', ''):
                                image_url = link.get('href')
                                break
                except Exception as e:
                    print(f"Image extraction error for entry {i}: {e}")

                # Get text content
                text_content = ""
                if hasattr(entry, 'summary') and entry.summary:
                    text_content = entry.summary
                elif hasattr(entry, 'description') and entry.description:
                    text_content = entry.description
                elif hasattr(entry, 'content') and entry.content:
                    if isinstance(entry.content, list) and len(entry.content) > 0:
                        text_content = entry.content[0].get('value', '')
                    else:
                        text_content = str(entry.content)

                post = {
                    "title": getattr(entry, 'title', f'Post {i+1}'),
                    "link": getattr(entry, 'link', '#'),
                    "text": text_content,
                    "image": image_url,
                    "published": published_date.isoformat()
                }
                
                posts.append(post)
                print(f"Processed entry {i+1}: {post['title'][:50]}...")
                
            except Exception as e:
                print(f"Error processing entry {i}: {e}")
                print(f"Entry data: {entry}")
                continue

        print(f"Successfully processed {len(posts)} posts")
        return jsonify(posts)

    except Exception as e:
        error_msg = str(e)
        error_traceback = traceback.format_exc()
        print(f"Error in announcements endpoint: {error_msg}")
        print(f"Traceback: {error_traceback}")
        
        return jsonify({
            "error": "Failed to fetch announcements",
            "message": error_msg,
            "url": RSS_URL
        }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    print("Starting Flask RSS app...")
    print(f"RSS URL: {RSS_URL}")
    app.run(host="0.0.0.0", port=5000, debug=True)
