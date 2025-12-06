import feedparser
import json
from datetime import datetime
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

def fetch_lottery():
    # 1. Định nghĩa 3 RSS feed
    rss_feeds = {
        "mien_bac": "https://xosothantai.mobi/rss/xo-so-mien-bac.rss",
        "mien_nam": "https://xosothantai.mobi/rss/xo-so-mien-nam.rss",
        "mien_trung": "https://xosothantai.mobi/rss/xo-so-mien-trung.rss"
    }
    
    lottery_data = {}
    
    for region, url in rss_feeds.items():
        try:
            feed = feedparser.parse(url)
            items = []
            
            # QUAN TRỌNG: Thay đổi ở đây - Chỉ lấy kết quả MỚI NHẤT (entry đầu tiên)
            if len(feed.entries) > 0:
                latest_entry = feed.entries[0]
                items.append({
                    "title": latest_entry.title,
                    "link": latest_entry.link,
                    "published": latest_entry.get("published", ""),
                    "summary": latest_entry.get("summary", ""),
                    "guid": latest_entry.get("id", latest_entry.link)
                })
                print(f"✅ Đã lấy kết quả gần nhất từ RSS {region}: {latest_entry.title[:50]}...")
            else:
                print(f"⚠️ RSS {region} không có dữ liệu.")
            
            lottery_data[region] = {
                "source": url,
                "last_updated": datetime.utcnow().isoformat() + "Z",
                "items": items,  # Mảng giờ chỉ có 0 hoặc 1 phần tử
                "total_items": len(items)
            }
            
        except Exception as e:
            print(f"❌ Lỗi khi lấy RSS {region}: {e}")
            lottery_data[region] = {
                "error": str(e),
                "source": url,
                "last_updated": datetime.utcnow().isoformat() + "Z",
                "items": [],
                "total_items": 0
            }
    
    # 2. Ghi dữ liệu ra file lottery.json
    output_data = {
        "source": "xosothantai.mobi RSS",
        "updated": datetime.utcnow().isoformat() + "Z",
        "regions": lottery_data
    }
    
    with open("lottery.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Đã tạo lottery.json với kết quả MỚI NHẤT của 3 miền")
# ================== 3. CHẠY CHÍNH ==================
if __name__ == "__main__":
    fetch_news()
    fetch_lottery()
    print("✨ Hoàn tất tất cả công việc!")
