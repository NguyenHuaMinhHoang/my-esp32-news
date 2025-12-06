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
                            "title": latest_result["title"],
                            "link": latest_result["link"],
                            "published": latest_result["published"],
                            "summary": latest_result["summary"],
                            "full_description": latest_result.get("description", ""),
                            "guid": latest_result["guid"]
                        }]
                        print(f"✅ Đã lấy kết quả gần nhất từ RSS {region}: {latest_result['title'][:50]}...")
                    else:
                        items = []
                        print(f"⚠️ RSS {region} không có dữ liệu.")
                else:
                    items = []
                    print(f"⚠️ RSS {region} không có dữ liệu.")
            else:
                # Xử lý cho miền Bắc và miền Trung (xosothantai.mobi)
                items = []
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
                "items": items,
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
        "source": "Tổng hợp từ xskt.com.vn và xosothantai.mobi",
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
