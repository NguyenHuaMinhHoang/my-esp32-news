import feedparser
import json
from datetime import datetime

# 1. Link RSS VnExpress
RSS_URL = "https://vnexpress.net/rss/tin-moi-nhat.rss"
feed = feedparser.parse(RSS_URL)

# 2. Lấy 10 tin mới nhất
news_items = []
for entry in feed.entries[:10]:
    news_items.append({
        "id": entry.get("id", entry.link),
        "title": entry.title,
        "link": entry.link,
        "pubDate": entry.get("published", ""),
        "description": entry.get("summary", ""),
        "image": ""  # RSS VnExpress thường không có ảnh trực tiếp, để trống
    })

# 3. Đóng gói dữ liệu giống cấu trúc cũ
output_data = {
    "source": "VnExpress RSS",
    "updated": datetime.utcnow().isoformat() + "Z",
    "articles": news_items,
    "total_articles": len(news_items)
}

# 4. Ghi ra file news.json
with open("news.json", "w", encoding="utf-8") as f:
    json.dump(output_data, f, ensure_ascii=False, indent=2)

print("Done! Created news.json with", len(news_items), "articles.")
