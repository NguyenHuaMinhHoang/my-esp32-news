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
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(GOLD_URL, timeout=15, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        gold_data = []
        
        # 1. Tìm TẤT CẢ các bảng trong trang
        all_tables = soup.find_all('table')
        print(f"🔍 Tìm thấy {len(all_tables)} bảng trên trang.")

        for table_index, table in enumerate(all_tables):
            # 2. Tìm tất cả hàng <tr> trong bảng hiện tại
            rows = table.find_all('tr')
            
            # 3. Lọc và xử lý từng hàng có dữ liệu (có thuộc tính data-code)
            for row in rows:
                # Bỏ qua các hàng trống, hàng tiêu đề, hàng quảng cáo
                if row.get('data-code') and row.get('data-code') != 'data-title':
                    # Tìm tất cả ô <td> hoặc <th> trong hàng
                    cols = row.find_all(['td', 'th'])
                    
                    # Chỉ xử lý hàng có đủ dữ liệu (ít nhất 4 cột)
                    if len(cols) >= 4:
                        # Lấy văn bản từ các cột, loại bỏ khoảng trắng thừa
                        col_texts = [col.get_text(strip=True) for col in cols]
                        
                        gold_data.append({
                            "ma": row.get('data-code', ''),  # Mã sản phẩm, ví dụ: SJL1L10
                            "loai_vang": col_texts[0],       # Cột 1: Loại vàng (vd: SJC 1L 10L)
                            "ham_luong": col_texts[1],       # Cột 2: Hàm lượng
                            "mua_vao": col_texts[2],         # Cột 3: Giá mua vào
                            "ban_ra": col_texts[3]           # Cột 4: Giá bán ra
                        })
                        print(f"   ➕ Đã thêm: {col_texts[0]} - Mua: {col_texts[2]}, Bán: {col_texts[3]}")

        # 4. Đóng gói và ghi file JSON
        gold_output = {
            "source": "GiaVang.net",
            "updated": datetime.utcnow().isoformat() + "Z",
            "data": gold_data,
            "total_items": len(gold_data)
        }

        with open("giavang.json", "w", encoding="utf-8") as f:
            json.dump(gold_output, f, ensure_ascii=False, indent=2)
            
        print(f"✅ Đã tạo giavang.json với {len(gold_data)} mục giá vàng.")
        
    except requests.RequestException as e:
        print(f"❌ Lỗi kết nối: {e}")
    except Exception as e:
        print(f"❌ Lỗi xử lý: {e}")
# ================== 3. CHẠY CHÍNH ==================
if __name__ == "__main__":
    fetch_news()
    fetch_gold_price()
    print("✨ Hoàn tất tất cả công việc!")
