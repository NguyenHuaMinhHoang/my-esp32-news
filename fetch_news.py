import feedparser
import json
from datetime import datetime, timezone, timedelta
from time import mktime
import requests
from bs4 import BeautifulSoup
import time
import re
import sys
import os

# ================== CẤU HÌNH THỜI GIAN ==================
VN_TZ = timezone(timedelta(hours=7))


def get_vietnam_time():
    """Lấy thời gian hiện tại theo múi giờ Việt Nam"""
    return datetime.now(VN_TZ)


def get_utc_time():
    """Lấy thời gian hiện tại theo UTC"""
    return datetime.utcnow()


def format_price(price_str):
    """Định dạng giá tiền"""
    if not price_str:
        return ""

    # Loại bỏ ký tự không phải số
    digits = re.sub(r'[^\d]', '', price_str)

    if digits:
        try:
            # Thêm dấu phân cách hàng nghìn
            num = int(digits)
            return f"{num:,}"
        except:
            return price_str
    return price_str


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

    current_time = get_utc_time()
    current_time_vn = get_vietnam_time()
    output_data = {
        "source": "VnExpress RSS",
        "updated": current_time.isoformat() + "Z",
        "updated_vn": current_time_vn.isoformat(),
        "schedule_time": current_time_vn.strftime("%H:%M"),
        "articles": news_items,
        "total_articles": len(news_items)
    }

    with open("news.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"✅ Đã tạo news.json với {len(news_items)} tin tức.")
    return output_data


# ================== 2. LẤY KẾT QUẢ XỔ SỐ ==================
def fetch_lottery():
    # 1. Định nghĩa RSS feed cho 3 miền
    rss_feeds = {
        "mien_bac": "https://xskt.com.vn/rss-feed/mien-bac-xsmb.rss",
        "mien_nam": "https://xskt.com.vn/rss-feed/mien-nam-xsmn.rss",
        "mien_trung": "https://xskt.com.vn/rss-feed/mien-trung-xsmt.rss"
    }

    lottery_data = {}
    current_time_utc = get_utc_time()
    current_time_vn = get_vietnam_time()

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
                            "published_vn": current_time_vn.strftime("%H:%M %d/%m/%Y"),
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
                # Xử lý cho miền Bắc và miền Trung
                items = []
                if len(feed.entries) > 0:
                    latest_entry = feed.entries[0]
                    items.append({
                        "title": latest_entry.title,
                        "link": latest_entry.link,
                        "published": latest_entry.get("published", ""),
                        "published_vn": current_time_vn.strftime("%H:%M %d/%m/%Y"),
                        "summary": latest_entry.get("summary", ""),
                        "guid": latest_entry.get("id", latest_entry.link)
                    })
                    print(f"✅ Đã lấy kết quả gần nhất từ RSS {region}: {latest_entry.title[:50]}...")
                else:
                    print(f"⚠️ RSS {region} không có dữ liệu.")

            lottery_data[region] = {
                "source": url,
                "last_updated": current_time_utc.isoformat() + "Z",
                "last_updated_vn": current_time_vn.isoformat(),
                "items": items,
                "total_items": len(items)
            }

        except Exception as e:
            print(f"❌ Lỗi khi lấy RSS {region}: {e}")
            lottery_data[region] = {
                "error": str(e),
                "source": url,
                "last_updated": current_time_utc.isoformat() + "Z",
                "last_updated_vn": current_time_vn.isoformat(),
                "items": [],
                "total_items": 0
            }

    # 2. Ghi dữ liệu ra file lottery.json
    output_data = {
        "source": "Tổng hợp từ xskt.com.vn",
        "updated": current_time_utc.isoformat() + "Z",
        "updated_vn": current_time_vn.isoformat(),
        "schedule_time": current_time_vn.strftime("%H:%M"),
        "regions": lottery_data
    }

    with open("lottery.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"✅ Đã tạo lottery.json với kết quả MỚI NHẤT của 3 miền")
    return output_data


# ================== 3. LẤY GIÁ VÀNG TỪ GIAVANG.NET ==================
def scrape_giavang_net():
    """
    Scrape giá vàng từ giavang.net - phiên bản tối ưu cho cấu trúc data-code
    """
    print("🚀 Khởi động scraper cho giavang.net...")

    # Thử import selenium
    try:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.chrome.options import Options
        from selenium.common.exceptions import TimeoutException
    except ImportError:
        print("❌ Selenium chưa được cài đặt. Sử dụng phương pháp thay thế...")
        return fetch_gold_fallback()

    # Cấu hình Chrome
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

    driver = None
    try:
        # Thử khởi tạo trình duyệt với webdriver-manager
        try:
            from selenium.webdriver.chrome.service import Service
            from webdriver_manager.chrome import ChromeDriverManager
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            print("✅ Đã sử dụng webdriver-manager để tải ChromeDriver")
        except:
            # Fallback: thử dùng ChromeDriver có sẵn
            driver = webdriver.Chrome(options=chrome_options)
            print("✅ Đã sử dụng ChromeDriver có sẵn")

        driver.get("https://giavang.net/")

        print("⏳ Đang đợi trang tải và cập nhật giá...")

        # Chờ bảng giá xuất hiện
        wait = WebDriverWait(driver, 20)

        # Thử tìm bảng bằng ID trước
        try:
            wait.until(EC.presence_of_element_located((By.ID, "tbl")))
            table = driver.find_element(By.ID, "tbl")
            print("✅ Đã tìm thấy bảng bằng ID 'tbl'")
        except:
            # Fallback: tìm bất kỳ bảng nào
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
            tables = driver.find_elements(By.TAG_NAME, "table")
            table = tables[0] if tables else None
            print(f"✅ Đã tìm thấy {len(tables)} bảng")

        # Đợi thêm để JavaScript tải dữ liệu động
        time.sleep(3)

        # Nếu không có bảng, thử tìm bằng class
        if not table:
            tables = driver.find_elements(By.CSS_SELECTOR, "table")
            if tables:
                table = tables[0]
                print("✅ Đã tìm thấy bảng bằng CSS selector")

        if not table:
            print("❌ Không tìm thấy bảng nào")
            return fetch_gold_fallback()

        # Khởi tạo cấu trúc dữ liệu
        gold_data = []
        current_section = "Chung"

        # Duyệt qua các hàng trong bảng
        rows = table.find_elements(By.TAG_NAME, "tr")

        for row in rows:
            # Bỏ qua hàng trống hoặc chỉ có colspan
            row_text = row.text.strip()
            if not row_text:
                continue

            # Kiểm tra xem hàng này có phải là tiêu đề section không
            row_class = row.get_attribute("class") or ""

            # Phát hiện section mới
            if "GIÁ VÀNG SJC" in row_text and "VIỆT NAM" in row_text:
                current_section = "Vàng SJC Việt Nam"
                continue
            elif "CÁC THƯƠNG HIỆU VÀNG" in row_text:
                current_section = "Các thương hiệu vàng"
                continue
            elif "VÀNG THẾ GIỚI" in row_text:
                current_section = "Vàng thế giới"
                continue
            elif "THƯƠNG HIỆU" in row_text:
                current_section = "Các thương hiệu vàng"
                continue

            # Kiểm tra xem hàng có chứa dữ liệu giá không
            data_code = row.get_attribute("data-code")

            if data_code and data_code not in ["...", "", "none"]:
                # Hàng này có data-code, có thể chứa giá
                try:
                    # Tìm các ô trong hàng
                    cells = row.find_elements(By.TAG_NAME, "td")

                    if len(cells) >= 2:
                        # Mặc định lấy từ các ô
                        item_name = cells[0].text.strip() if cells[0].text.strip() else ""
                        buy_price = ""
                        sell_price = ""

                        # Thử lấy giá từ các ô
                        if len(cells) >= 3:
                            # Ô thứ 2 là giá mua, ô thứ 3 là giá bán
                            buy_price = cells[1].text.strip() if len(cells) > 1 else ""
                            sell_price = cells[2].text.strip() if len(cells) > 2 else ""
                        elif len(cells) == 2:
                            # Chỉ có 2 ô: có thể ô thứ 2 chứa cả hai giá
                            price_text = cells[1].text.strip()
                            if "/" in price_text:
                                parts = price_text.split("/")
                                buy_price = parts[0].strip() if len(parts) > 0 else ""
                                sell_price = parts[1].strip() if len(parts) > 1 else ""

                        # Nếu không có tên, tạo từ data-code
                        if not item_name:
                            data_title = row.get_attribute("data-title")
                            if data_title:
                                item_name = data_title
                            else:
                                item_name = f"Mã {data_code}"

                        # Chỉ thêm nếu có ít nhất một giá
                        if buy_price or sell_price:
                            gold_item = {
                                "section": current_section,
                                "code": data_code,
                                "name": item_name,
                                "buy": format_price(buy_price),
                                "sell": format_price(sell_price),
                                "buy_raw": buy_price,
                                "sell_raw": sell_price,
                            }
                            gold_data.append(gold_item)

                except Exception as e:
                    print(f"⚠️ Lỗi khi xử lý hàng {data_code}: {e}")
                    continue

        # Nếu không có dữ liệu, thử tìm tất cả phần tử có data-code
        if len(gold_data) < 3:
            print("⚠️ Dữ liệu ít, thử phương pháp thay thế...")

            # Tìm tất cả phần tử có data-code
            elements_with_code = driver.find_elements(By.CSS_SELECTOR, "[data-code]")

            for elem in elements_with_code:
                code = elem.get_attribute("data-code")
                if code and code not in ["...", "", "none"]:
                    # Tìm các ô giá trong cùng hàng
                    try:
                        parent_row = elem.find_element(By.XPATH, "./ancestor::tr")
                        cells = parent_row.find_elements(By.TAG_NAME, "td")

                        if len(cells) >= 3:
                            item_name = cells[0].text.strip() if cells[0].text else f"Mã {code}"
                            buy_price = cells[1].text.strip() if len(cells) > 1 else ""
                            sell_price = cells[2].text.strip() if len(cells) > 2 else ""

                            if buy_price or sell_price:
                                gold_data.append({
                                    "section": "Tự động phát hiện",
                                    "code": code,
                                    "name": item_name,
                                    "buy": format_price(buy_price),
                                    "sell": format_price(sell_price),
                                    "buy_raw": buy_price,
                                    "sell_raw": sell_price
                                })
                    except:
                        continue

        # Chuẩn bị dữ liệu đầu ra
        current_time = datetime.now()
        output_data = {
            "status": "success",
            "source": "https://giavang.net/",
            "last_updated": current_time.strftime("%Y-%m-%d %H:%M:%S"),
            "last_updated_vn": current_time.strftime("%H:%M %d/%m/%Y"),
            "total_items": len(gold_data),
            "sections": list(set([item.get("section", "Chung") for item in gold_data])),
            "data": gold_data
        }

        # Ghi vào file JSON
        with open("giavang.json", "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        print(f"✅ Đã thu thập {len(gold_data)} mục giá vàng")
        print(f"📁 Đã lưu vào: giavang.json")

        # Hiển thị thống kê
        if gold_data:
            print("\n📊 Thống kê dữ liệu:")
            sections = {}
            for item in gold_data:
                section = item.get("section", "Chung")
                sections[section] = sections.get(section, 0) + 1

            for section, count in sections.items():
                print(f"   • {section}: {count} mục")

            print("\n🔍 Mẫu dữ liệu:")
            for i, item in enumerate(gold_data[:5]):
                buy_display = item["buy"] if item["buy"] else "N/A"
                sell_display = item["sell"] if item["sell"] else "N/A"
                print(f"   {i + 1}. [{item['code']}] {item['name'][:30]}... | Mua: {buy_display} | Bán: {sell_display}")

        return output_data

    except TimeoutException:
        print("❌ Lỗi: Timeout khi chờ trang tải. Kiểm tra kết nối internet.")
        return save_gold_error("Timeout khi tải trang")
    except Exception as e:
        print(f"❌ Lỗi: {type(e).__name__}: {e}")
        return save_gold_error(str(e))
    finally:
        if driver:
            driver.quit()
            print("\n🔄 Đã đóng trình duyệt.")


def fetch_gold_fallback():
    """Phương pháp fallback nếu không dùng được Selenium"""
    print("🔄 Sử dụng phương pháp fallback cho giá vàng...")

    try:
        # Thử dùng requests và BeautifulSoup
        url = "https://giavang.net/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')

            # Tìm tất cả bảng
            tables = soup.find_all('table')
            gold_data = []

            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 3:
                        name = cells[0].text.strip() if cells[0].text else ""
                        buy = cells[1].text.strip() if len(cells) > 1 else ""
                        sell = cells[2].text.strip() if len(cells) > 2 else ""

                        if name and (buy or sell):
                            gold_data.append({
                                "section": "Fallback",
                                "code": "",
                                "name": name,
                                "buy": format_price(buy),
                                "sell": format_price(sell),
                                "buy_raw": buy,
                                "sell_raw": sell
                            })

            if gold_data:
                current_time = datetime.now()
                output_data = {
                    "status": "success",
                    "source": "https://giavang.net/ (Fallback)",
                    "last_updated": current_time.strftime("%Y-%m-d %H:%M:%S"),
                    "last_updated_vn": current_time.strftime("%H:%M %d/%m/%Y"),
                    "total_items": len(gold_data),
                    "data": gold_data
                }

                with open("giavang.json", "w", encoding="utf-8") as f:
                    json.dump(output_data, f, ensure_ascii=False, indent=2)

                print(f"✅ Đã thu thập {len(gold_data)} mục giá vàng (Fallback)")
                return output_data

    except Exception as e:
        print(f"❌ Lỗi fallback: {e}")

    # Nếu tất cả đều thất bại
    return save_gold_error("Không thể lấy dữ liệu giá vàng")


def save_gold_error(error_msg):
    """Lưu thông báo lỗi vào file JSON"""
    error_data = {
        "status": "error",
        "message": error_msg,
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "last_updated_vn": datetime.now().strftime("%H:%M %d/%m/%Y"),
        "data": []
    }

    with open("giavang.json", "w", encoding="utf-8") as f:
        json.dump(error_data, f, ensure_ascii=False, indent=2)

    return error_data


def fetch_gold_price():
    """
    Lấy giá vàng từ giavang.net
    Chạy vào lúc 7h sáng và 11h trưa giờ VN (00:00 UTC và 04:00 UTC)
    """
    current_time_vn = get_vietnam_time()
    current_time_utc = get_utc_time()

    # Chuyển đổi giờ VN sang UTC để kiểm tra
    # 7h sáng VN = 00:00 UTC, 11h trưa VN = 04:00 UTC

    # Kiểm tra xem có nên chạy không (cả 7h sáng và 11h trưa)
    if current_time_utc.hour == 0 or current_time_utc.hour == 4:
        print(
            f"⏰ {current_time_vn.strftime('%H:%M')} - Đúng giờ cập nhật giá vàng ({current_time_vn.strftime('%H:%M')} VN)")
        return scrape_giavang_net()
    else:
        # Tính toán thời gian cập nhật tiếp theo
        current_hour_vn = current_time_vn.hour

        if current_hour_vn < 7:
            next_update_vn = "07:00"
        elif current_hour_vn < 11:
            next_update_vn = "11:00"
        else:
            next_update_vn = "07:00 (ngày mai)"

        print(
            f"⏭️ {current_time_vn.strftime('%H:%M')} - Bỏ qua cập nhật giá vàng (chỉ chạy lúc 7h sáng và 11h trưa VN)")
        print(f"   ⏳ Lần cập nhật tiếp theo: {next_update_vn}")

        # Đọc file cũ nếu có
        try:
            with open("giavang.json", "r", encoding="utf-8") as f:
                old_data = json.load(f)

            # Cập nhật thời gian kiểm tra
            old_data["last_checked"] = current_time_vn.isoformat()
            old_data["next_update"] = next_update_vn
            old_data["current_time_vn"] = current_time_vn.strftime("%H:%M %d/%m/%Y")

            with open("giavang.json", "w", encoding="utf-8") as f:
                json.dump(old_data, f, ensure_ascii=False, indent=2)

            return old_data
        except:
            # Tạo file mới với thông báo
            skip_data = {
                "status": "skipped",
                "message": f"Gold price updates at 7:00 AM and 11:00 AM VN time. Current: {current_time_vn.strftime('%H:%M')}",
                "last_checked": current_time_vn.isoformat(),
                "next_scheduled": next_update_vn,
                "current_time_vn": current_time_vn.strftime("%H:%M %d/%m/%Y"),
                "data": []
            }

            with open("giavang.json", "w", encoding="utf-8") as f:
                json.dump(skip_data, f, ensure_ascii=False, indent=2)

            return skip_data


# ================== 4. CHẠY TẤT CẢ ==================
def run_all_updates():
    """Chạy tất cả các cập nhật"""
    print("=" * 60)
    print("🚀 BẮT ĐẦU CẬP NHẬT DỮ LIỆU TỰ ĐỘNG")
    print("=" * 60)

    current_time_vn = get_vietnam_time()
    print(f"⏰ Thời gian hiện tại (VN): {current_time_vn.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Thời gian hiện tại (UTC): {get_utc_time().strftime('%Y-%m-%d %H:%M:%S')}Z")

    # Kiểm tra xem có phải giờ cập nhật giá vàng không
    current_time_utc = get_utc_time()
    is_gold_update_time = current_time_utc.hour == 0 or current_time_utc.hour == 4

    # Chạy tất cả các hàm
    print("\n📰 Đang cập nhật tin tức...")
    news_data = fetch_news()

    print("\n🎱 Đang cập nhật kết quả xổ số...")
    lottery_data = fetch_lottery()

    print("\n🪙 Đang cập nhật giá vàng...")
    gold_data = fetch_gold_price()

    print("\n" + "=" * 60)
    print("✨ HOÀN TẤT CẬP NHẬT DỮ LIỆU")
    print("=" * 60)

    # Tổng kết
    print(f"\n📊 TỔNG KẾT:")
    print(f"   • Tin tức: {news_data['total_articles']} bài")

    total_lottery = 0
    for region in lottery_data['regions'].values():
        total_lottery += region.get('total_items', 0)
    print(f"   • Xổ số: {total_lottery} kết quả (3 miền)")

    if gold_data.get('status') == 'success':
        print(
            f"   • Giá vàng: {gold_data.get('total_items', 0)} mục (Cập nhật lúc {current_time_vn.strftime('%H:%M')})")
    elif gold_data.get('status') == 'skipped':
        print(f"   • Giá vàng: {gold_data.get('message', 'Đã bỏ qua')}")
        print(f"   • Lần cập nhật tiếp theo: {gold_data.get('next_scheduled', '07:00')}")
    else:
        print(f"   • Giá vàng: {gold_data.get('status', 'Lỗi')} - {gold_data.get('message', 'Không xác định')}")

    print(f"\n💾 File đã tạo: news.json, lottery.json, giavang.json")
    print(f"🕒 Hoàn thành lúc: {current_time_vn.strftime('%H:%M:%S')} (VN Time)")

    # Thông báo về lịch cập nhật giá vàng
    if is_gold_update_time:
        print(f"\n✅ ĐÃ CẬP NHẬT GIÁ VÀNG VÀO LÚC {current_time_vn.strftime('%H:%M')}")
    else:
        next_update = gold_data.get('next_scheduled', '07:00 hoặc 11:00')
        print(f"\n⏰ Giá vàng sẽ được cập nhật lần tiếp theo vào: {next_update} (giờ VN)")


# ================== 5. CHẠY CẬP NHẬT GIÁ VÀNG RIÊNG ==================
def run_gold_update_only():
    """Chỉ chạy cập nhật giá vàng (bỏ qua điều kiện thời gian)"""
    print("=" * 60)
    print("🪙 CẬP NHẬT GIÁ VÀNG THỦ CÔNG")
    print("=" * 60)

    current_time_vn = get_vietnam_time()
    print(f"⏰ Thời gian hiện tại (VN): {current_time_vn.strftime('%Y-%m-%d %H:%M:%S')}")

    print("\n🔄 Đang cập nhật giá vàng...")
    gold_data = scrape_giavang_net()

    print("\n" + "=" * 60)
    print(f"✅ HOÀN TẤT CẬP NHẬT GIÁ VÀNG LÚC {current_time_vn.strftime('%H:%M')}")
    print("=" * 60)

    return gold_data


# ================== 6. CHẠY CHÍNH ==================
if __name__ == "__main__":
    # Kiểm tra đối số dòng lệnh
    if len(sys.argv) > 1:
        if sys.argv[1] == "--gold-only":
            run_gold_update_only()
        elif sys.argv[1] == "--help":
            print("Cách sử dụng:")
            print("  python script.py           - Chạy tất cả cập nhật")
            print("  python script.py --gold-only - Chỉ cập nhật giá vàng")
            print("  python script.py --help    - Hiển thị trợ giúp")
        else:
            print(f"Đối số không hợp lệ: {sys.argv[1]}")
            print("Sử dụng: python script.py [--gold-only|--help]")
    else:
        # Chạy tất cả cập nhật
        run_all_updates()
