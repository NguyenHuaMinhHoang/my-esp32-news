import feedparser
import json
from datetime import datetime

# 1. Link RSS VnExpress
RSS_URL = "https://vnexpress.net/rss/tin-moi-nhat.rss"
feed = feedparser.parse(RSS_URL)

# 2. Lấy 10 tin mới nhất
news_items = []
for entry in feed.entries[:10]:
    # Logic tìm ảnh được viết trực tiếp tại đây
    thumbnail_url = ""
    if 'media_content' in entry:
        for media in entry.media_content:
            if media.get('type', '').startswith('image/'):
                thumbnail_url = media.get('url', '')
                break
    if not thumbnail_url and 'links' in entry:  # Nếu chưa tìm thấy
        for link in entry.links:
            if link.get('type', '').startswith('image/'):
                thumbnail_url = link.get('href', '')
                break

    news_items.append({
        "id": entry.get("id", entry.link),
        "title": entry.title,
        "link": entry.link,
        "pubDate": entry.get("published", ""),
        "description": entry.get("content", entry.get("summary", "")),
        "image": thumbnail_url  # Sử dụng biến vừa tìm được
    })

# 3. Đóng gói dữ liệu
output_data = {
    "source": "VnExpress RSS",
    "updated": datetime.utcnow().isoformat() + "Z",
    "articles": news_items,
    "total_articles": len(news_items)
}

# 4. Ghi ra file news.json
with open("news.json", "w", encoding="utf-8") as f:
    json.dump(output_data, f, ensure_ascii=False, indent=2)

print("✅ Đã tạo news.json với", len(news_items), "tin tức.")
