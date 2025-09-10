from flask import Flask, jsonify, render_template
from flask_cors import CORS
import feedparser
from datetime import datetime
import dateutil.parser
import traceback
import re

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)

# RSS URL - RSSHub for Facebook pages
RSS_URL = "https://rsshub.app/facebook/page/NCST.OfficialPage"

@app.route("/")
def home():
    try:
        return render_template("index.html")
    except Exception as e:
        print(f"Error rendering template: {e}")
        # Fallback HTML page if template is missing
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>NCST Announcements</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
                .container { max-width: 800px; margin: 0 auto; }
                .header { text-align: center; color: white; margin-bottom: 30px; }
                .post { background: white; margin: 20px 0; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>NCST Official Announcements</h1>
                    <p>Latest updates and announcements</p>
                </div>
                <div id="posts">Loading announcements...</div>
            </div>
            <script>
                // Your JavaScript code goes here
            </script>
        </body>
        </html>
        '''

@app.route("/api/announcements")
def announcements():
    global RSS_URL  # Declare RSS_URL as global to allow modification
    try:
        print(f"Fetching RSS from: {RSS_URL}")
        
        # Parse the RSS feed with custom headers
        feed = feedparser.parse(RSS_URL, agent='Mozilla/5.0 (compatible; RSS Reader)')
        
        # Check if feed parsing was successful
        if hasattr(feed, 'bozo') and feed.bozo:
            print(f"Feed parsing warning: {getattr(feed, 'bozo_exception', 'Unknown error')}")
        
        print(f"Feed title: {getattr(feed.feed, 'title', 'No title')}")
        print(f"Number of entries: {len(feed.entries)}")
        
        # If no entries found, try alternative RSS URLs
        if not feed.entries:
            alternative_urls = [
                "https://rsshub.app/facebook/page/NCST.OfficialPage/posts",
                "https://rsshub.app/facebook/page/ncst.officialpage",
                "https://rss.app/feeds/v1.1/facebook-ncst-official.xml"
            ]
            
            for alt_url in alternative_urls:
                print(f"Trying alternative URL: {alt_url}")
                feed = feedparser.parse(alt_url, agent='Mozilla/5.0 (compatible; RSS Reader)')
                if feed.entries:
                    RSS_URL = alt_url  # Update the global RSS_URL
                    break
            
            if not feed.entries:
                # Return mock data if RSS fails
                mock_posts = [
                    {
                        "title": "Welcome to NCST Announcements",
                        "link": "#",
                        "text": "This is a test announcement. RSS feed is currently unavailable. Please check back later for official announcements from NCST.",
                        "image": None,
                        "published": datetime.now().isoformat()
                    },
                    {
                        "title": "RSS Feed Information",
                        "link": "#",
                        "text": "We're experiencing issues with the RSS feed. Our team is working to resolve this. Meanwhile, you can visit the official NCST page for updates.",
                        "image": None,
                        "published": datetime.now().isoformat()
                    }
                ]
                return jsonify(mock_posts)

        posts = []
        for i, entry in enumerate(feed.entries[:10]):
            try:
                # Parse published date
                published_date = datetime.now()
                
                # Try different date fields
                date_fields = ['published', 'updated', 'created', 'pubDate', 'date']
                for field in date_fields:
                    if hasattr(entry, field) and getattr(entry, field):
                        try:
                            date_string = getattr(entry, field)
                            published_date = dateutil.parser.parse(date_string)
                            break
                        except Exception as e:
                            print(f"Date parsing error for {field}: {e}")
                            continue

                # Extract image URL from various sources
                image_url = None
                try:
                    if hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
                        image_url = entry.media_thumbnail[0].get('url')
                    elif hasattr(entry, 'media_content') and entry.media_content:
                        for media in entry.media_content:
                            if 'image' in media.get('type', ''):
                                image_url = media.get('url')
                                break
                    elif hasattr(entry, 'enclosures'):
                        for enclosure in entry.enclosures:
                            if 'image' in enclosure.get('type', ''):
                                image_url = enclosure.get('href')
                                break
                    
                    if not image_url and hasattr(entry, 'summary'):
                        img_match = re.search(r'<img[^>]+src="([^"]+)"', entry.summary)
                        if img_match:
                            image_url = img_match.group(1)
                            
                except Exception as e:
                    print(f"Image extraction error for entry {i}: {e}")

                # Get text content and clean it
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

                # Clean HTML tags from text content
                text_content = re.sub(r'<[^>]+>', '', text_content)
                text_content = re.sub(r'\s+', ' ', text_content).strip()

                # Get title and clean it
                title = getattr(entry, 'title', f'Announcement {i+1}')
                title = re.sub(r'<[^>]+>', '', title).strip()

                post = {
                    "title": title,
                    "link": getattr(entry, 'link', '#'),
                    "text": text_content if text_content else "No content available.",
                    "image": image_url,
                    "published": published_date.isoformat()
                }
                
                posts.append(post)
                print(f"Processed entry {i+1}: {post['title'][:50]}...")
                
            except Exception as e:
                print(f"Error processing entry {i}: {e}")
                posts.append({
                    "title": f"Announcement {i+1}",
                    "link": getattr(entry, 'link', '#'),
                    "text": "Unable to parse this announcement content.",
                    "image": None,
                    "published": datetime.now().isoformat()
                })
                continue

        if not posts:
            posts = [{
                "title": "No Announcements Available",
                "link": "#",
                "text": "No announcements are currently available. Please check back later.",
                "image": None,
                "published": datetime.now().isoformat()
            }]

        print(f"Successfully processed {len(posts)} posts")
        return jsonify(posts)

    except Exception as e:
        error_msg = str(e)
        error_traceback = traceback.format_exc()
        print(f"Error in announcements endpoint: {error_msg}")
        print(f"Traceback: {error_traceback}")
        
        # Return fallback data
        fallback_posts = [
            {
                "title": "Service Temporarily Unavailable",
                "link": "#",
                "text": f"We're experiencing technical difficulties with the announcement feed. Error: {error_msg}. Please try again later or visit the official NCST website for updates.",
                "image": None,
                "published": datetime.now().isoformat()
            }
        ]
        
        return jsonify(fallback_posts)

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error", "message": str(error)}), 500

@app.route("/health")
def health():
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

if __name__ == "__main__":
    print("Starting Flask RSS app...")
    print(f"RSS URL: {RSS_URL}")
    print("Available endpoints:")
    print("  GET /              - Home page")
    print("  GET /api/announcements - Get announcements JSON")
    print("  GET /health        - Health check")
    app.run(host="0.0.0.0", port=5000, debug=True)
