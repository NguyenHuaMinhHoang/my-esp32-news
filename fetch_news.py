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

# ================== 2. LẤY GIÁ VÀNG TỪ WEB ==================
def fetch_gold_price():
    GOLD_URL = "https://giavang.net/bang-gia-vang-trong-nuoc"
    
    try:
        # Gửi yêu cầu HTTP để lấy HTML
        response = requests.get(GOLD_URL, timeout=15)
        response.raise_for_status()  # Kiểm tra lỗi HTTP
        html_content = response.text

        # Phân tích HTML với BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # TÌM KIẾM BẢNG GIÁ VÀNG TRONG HTML
        # Lưu ý: Cấu trúc HTML có thể thay đổi, cần điều chỉnh selector nếu cần
        gold_data = []
        # Ví dụ: tìm tất cả các hàng (<tr>) trong bảng
        # Bạn cần kiểm tra cấu trúc HTML thực tế của trang để điều chỉnh cho phù hợp
        table = soup.find('table', {'class': 'gold-price-table'})  # Cần xác định class chính xác
        if table:
            rows = table.find_all('tr')[1:6]  # Bỏ hàng tiêu đề, lấy 5 hàng đầu
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 4:
                    gold_data.append({
                        "loai_vang": cols[0].text.strip(),
                        "ham_luong": cols[1].text.strip(),
                        "mua_vao": cols[2].text.strip(),
                        "ban_ra": cols[3].text.strip()
                    })
        else:
            # Fallback nếu không tìm thấy bảng theo class
            # Tìm bảng đầu tiên trên trang
            table = soup.find('table')
            if table:
                rows = table.find_all('tr')[1:6]
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 4:
                        gold_data.append({
                            "loai_vang": cols[0].text.strip(),
                            "ham_luong": cols[1].text.strip(),
                            "mua_vao": cols[2].text.strip(),
                            "ban_ra": cols[3].text.strip()
                        })

        # Đóng gói dữ liệu giá vàng
        gold_output = {
            "source": "GiaVang.net",
            "updated": datetime.utcnow().isoformat() + "Z",
            "data": gold_data,
            "total_items": len(gold_data)
        }

        # Ghi ra file JSON
        with open("giavang.json", "w", encoding="utf-8") as f:
            json.dump(gold_output, f, ensure_ascii=False, indent=2)
        print("✅ Đã tạo giavang.json với", len(gold_data), "mục giá vàng.")
        
    except requests.RequestException as e:
        print(f"❌ Lỗi khi kết nối đến {GOLD_URL}: {e}")
    except Exception as e:
        print(f"❌ Lỗi khi xử lý dữ liệu giá vàng: {e}")

# ================== 3. CHẠY CHÍNH ==================
if __name__ == "__main__":
    fetch_news()
    fetch_gold_price()
    print("✨ Hoàn tất tất cả công việc!")
