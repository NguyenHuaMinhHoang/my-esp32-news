import feedparser
import json
from datetime import datetime
from time import mktime
import requests
from bs4 import BeautifulSoup

# ================== 1. LẤY TIN TỨC TỪ RSS ==================
def fetch_news():
    RSS_URL = "https://vnexpress.net/rss/tin-moi-nhat.rss"
    feed = feedparser.parse(RSS_URL)

    news_items = []
    for entry in feed.entries[:5]:
        news_items.append({
            "id": entry.get("id", entry.link),
            "title": entry.title,
            "link": entry.link,
            "pubDate": entry.get("published", ""),
            "description": entry.get("summary", ""),
            "image": ""
        })

    output_data = {
        "source": "VnExpress RSS",
        "updated": datetime.utcnow().isoformat() + "Z",
        "articles": news_items,
        "total_articles": len(news_items)
    }

    with open("news.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    print("✅ Đã tạo news.json với", len(news_items), "tin tức.")

# ================== 2. LẤY KẾT QUẢ XỔ SỐ ==================
def fetch_lottery():
    # 1. Định nghĩa RSS feed cho 3 miền
    rss_feeds = {
        "mien_bac": "https://xskt.com.vn/rss-feed/mien-bac-xsmb.rss",
        "mien_nam": "https://xskt.com.vn/rss-feed/mien-nam-xsmn.rss",  # Đã thay đổi
        "mien_trung": "https://xskt.com.vn/rss-feed/mien-trung-xsmt.rss"
    }
    
    lottery_data = {}
    
    for region, url in rss_feeds.items():
        try:
            feed = feedparser.parse(url)
            
            if region == "mien_nam":
                # Xử lý đặc biệt cho miền Nam (xskt.com.vn)
                if len(feed.entries) > 0:
                    # Tìm kết quả có ngày gần nhất
                    all_results = []
                    for entry in feed.entries:
                        published_time = entry.get('published_parsed')
                        if published_time:
                            published_dt = datetime.fromtimestamp(mktime(published_time))
                        else:
                            published_dt = datetime.min
                        
                        all_results.append({
                            "title": entry.title,
                            "link": entry.link,
                            "published": entry.get("published", ""),
                            "published_dt": published_dt,
                            "summary": entry.get("summary", ""),
                            "description": entry.get("description", ""),
                            "guid": entry.get("id", entry.link)
                        })
                    
                    if all_results:
                        # Lấy kết quả mới nhất
                        latest_result = max(all_results, key=lambda x: x["published_dt"])
                        
                        items = [{
