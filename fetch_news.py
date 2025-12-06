import feedparser
import json
from datetime import datetime

# 1. Link RSS VnExpress
RSS_URL = "https://vnexpress.net/rss/tin-moi-nhat.rss"
feed = feedparser.parse(RSS_URL)

# 2. Lấy 10 tin mới nhất
news_items = []
for entry in feed.entries[:10]:  # <-- Thay đổi từ 5 thành 10 ở đây
    news_items.append({
        "id": entry.get("id", entry.link),
        "title": entry.title,
        "link": entry.link,
        "pubDate": entry.get("published", ""),
        # Ưu tiên lấy 'content' hoặc 'summary' cho mô tả chi tiết
        "description": entry.get("content", entry.get("summary", "")),
        # Cố gắng lấy ảnh đại diện đầu tiên từ các liên kết media
        "image": get_thumbnail(entry)
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

# Hàm hỗ trợ: Tìm ảnh thumbnail từ entry RSS
def get_thumbnail(entry):
    """Trích xuất URL ảnh đầu tiên từ entry RSS."""
    # Thử tìm trong 'media_content' (nếu có)
    if 'media_content' in entry:
        for media in entry.media_content:
            if media.get('type', '').startswith('image/'):
                return media.get('url', '')
    
    # Thử tìm trong 'links' (nếu có)
    if 'links' in entry:
        for link in entry.links:
            if link.get('type', '').startswith('image/'):
                return link.get('href', '')
    
    # Nếu không tìm thấy, trả về chuỗi rỗng
    return ""
