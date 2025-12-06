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
            
            # Lấy 5 kết quả gần nhất cho mỗi miền
            for entry in feed.entries[:5]:
                items.append({
                    "title": entry.title,
                    "link": entry.link,
                    "published": entry.get("published", ""),
                    "summary": entry.get("summary", ""),
                    "guid": entry.get("id", entry.link)
                })
            
            lottery_data[region] = {
                "source": url,
                "last_updated": datetime.utcnow().isoformat() + "Z",
                "items": items,
                "total_items": len(items)
            }
            print(f"✅ Đã lấy {len(items)} kết quả từ RSS {region}")
            
        except Exception as e:
            print(f"❌ Lỗi khi lấy RSS {region}: {e}")
            lottery_data[region] = {
                "error": str(e),
                "source": url,
                "last_updated": datetime.utcnow().isoformat() + "Z"
            }
    
    # 2. Ghi dữ liệu ra file lottery.json
    output_data = {
        "source": "xosothantai.mobi RSS",
        "updated": datetime.utcnow().isoformat() + "Z",
        "regions": lottery_data
    }
    
    with open("lottery.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Đã tạo lottery.json với dữ liệu 3 miền")
# ================== 3. CHẠY CHÍNH ==================
if __name__ == "__main__":
    fetch_news()
    fetch_lottery()
    print("✨ Hoàn tất tất cả công việc!")
