from flask import Flask, jsonify
from flask_cors import CORS
import requests
import xml.etree.ElementTree as ET

app = Flask(__name__)
CORS(app)  # enable CORS for frontend requests

RSS_URL = "https://rsshub.app/facebook/page/NCST.OfficialPage"

@app.route("/api/announcements")
def announcements():
    try:
        resp = requests.get(RSS_URL, timeout=10)
        resp.raise_for_status()

        root = ET.fromstring(resp.content)
        channel = root.find("channel")
        items = channel.findall("item")

        posts = []
        for item in items[:10]:  # limit to 10 latest posts
            title = item.findtext("title")
            link = item.findtext("link")
            pub_date = item.findtext("pubDate")
            description = item.findtext("description")

            # some feeds may contain images in <media:content> or in description
            media_ns = "{http://search.yahoo.com/mrss/}"
            image_url = None
            media_content = item.find(f"{media_ns}content")
            if media_content is not None:
                image_url = media_content.attrib.get("url")

            posts.append({
                "title": title,
                "link": link,
                "date": pub_date,
                "description": description,
                "image": image_url
            })

        return jsonify(posts)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
