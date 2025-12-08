import json
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException


def scrape_giavang_net():
    """
    Scrape giá vàng từ giavang.net - phiên bản tối ưu cho cấu trúc data-code
    """
    print("🚀 Khởi động scraper cho giavang.net...")

    # Cấu hình Chrome
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

    driver = None
    try:
        # Khởi tạo trình duyệt
        driver = webdriver.Chrome(options=chrome_options)
        driver.get("https://giavang.net/")

        print("⏳ Đang đợi trang tải và cập nhật giá...")

        # Chờ bảng giá xuất hiện
        wait = WebDriverWait(driver, 15)
        wait.until(EC.presence_of_element_located((By.ID, "tbl")))

        # Đợi thêm để JavaScript tải dữ liệu động
        time.sleep(5)

        # Tìm bảng chính
        table = driver.find_element(By.ID, "tbl")

        # Khởi tạo cấu trúc dữ liệu
        gold_data = []
        current_section = "Chung"

        # Duyệt qua các hàng trong bảng
        rows = table.find_elements(By.TAG_NAME, "tr")

        for row in rows:
            # Bỏ qua hàng trống hoặc chỉ có colspan
            if not row.text.strip() and not row.get_attribute("data-code"):
                continue

            # Kiểm tra xem hàng này có phải là tiêu đề section không
            row_text = row.text.strip()
            row_class = row.get_attribute("class") or ""

            # Phát hiện section mới
            if "GIÁ VÀNG SJC" in row_text:
                current_section = "Vàng SJC Việt Nam"
                continue
            elif "CÁC THƯƠNG HIỆU VÀNG" in row_text:
                current_section = "Các thương hiệu vàng"
                continue
            elif "VÀNG THẾ GIỚI" in row_text:
                current_section = "Vàng thế giới"
                continue

            # Kiểm tra xem hàng có chứa dữ liệu giá không
            data_code = row.get_attribute("data-code")

            if data_code and data_code not in ["...", "", "none"]:
                # Hàng này có data-code, có thể chứa giá
                try:
                    # Tìm các ô trong hàng
                    cells = row.find_elements(By.TAG_NAME, "td")

                    if len(cells) >= 2:
                        # Cố gắng lấy thông tin từ các ô
                        # Trang này có thể hiển thị khác, cần thử nghiệm
                        item_name = ""
                        buy_price = ""
                        sell_price = ""

                        # Cách 1: Thử lấy từ các ô có class cụ thể
                        buy_cells = row.find_elements(By.CSS_SELECTOR, "td.buy, td[data-field='buy']")
                        sell_cells = row.find_elements(By.CSS_SELECTOR, "td.sell, td[data-field='sell']")

                        if buy_cells:
                            buy_price = buy_cells[0].text.strip()
                        if sell_cells:
                            sell_price = sell_cells[0].text.strip()

                        # Cách 2: Nếu không có class, thử lấy từ các ô thông thường
                        if not buy_price and len(cells) >= 2:
                            # Ô thứ 2 có thể là giá mua
                            buy_price = cells[1].text.strip() if len(cells) > 1 else ""

                        if not sell_price and len(cells) >= 3:
                            # Ô thứ 3 có thể là giá bán
                            sell_price = cells[2].text.strip() if len(cells) > 2 else ""

                        # Lấy tên từ ô đầu tiên hoặc từ thuộc tính data-title
                        if cells and cells[0].text.strip():
                            item_name = cells[0].text.strip()
                        else:
                            data_title = row.get_attribute("data-title")
                            if data_title:
                                item_name = data_title
                            else:
                                # Tạo tên từ mã
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

        # Nếu không có dữ liệu, thử phương pháp khác: tìm tất cả phần tử có data-code
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
            "source": "https://giavang.net/bang-gia-vang-trong-nuoc/",
            "last_updated": current_time.strftime("%Y-%m-%d %H:%M:%S"),
            "last_updated_vn": current_time.strftime("%H:%M %d/%m/%Y"),
            "total_items": len(gold_data),
            "sections": list(set([item["section"] for item in gold_data])),
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
                section = item["section"]
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
        return save_error_message("Timeout khi tải trang")
    except Exception as e:
        print(f"❌ Lỗi: {type(e).__name__}: {e}")
        return save_error_message(str(e))
    finally:
        if driver:
            driver.quit()
            print("\n🔄 Đã đóng trình duyệt.")


def format_price(price_str):
    """Định dạng giá tiền"""
    if not price_str:
        return ""

    # Loại bỏ ký tự không phải số
    import re
    digits = re.sub(r'[^\d]', '', price_str)

    if digits:
        try:
            # Thêm dấu phân cách hàng nghìn
            num = int(digits)
            return f"{num:,}"
        except:
            return price_str
    return price_str


def save_error_message(error_msg):
    """Lưu thông báo lỗi vào file JSON"""
    error_data = {
        "status": "error",
        "message": error_msg,
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "data": []
    }

    with open("giavang.json", "w", encoding="utf-8") as f:
        json.dump(error_data, f, ensure_ascii=False, indent=2)

    return error_data


# Hàm kiểm tra và cài đặt tự động
def setup_selenium():
    """Kiểm tra và cài đặt Selenium nếu cần"""
    try:
        from selenium import webdriver
        print("✅ Selenium đã sẵn sàng")
        return True
    except ImportError:
        print("❌ Selenium chưa được cài đặt.")
        print("📦 Cài đặt bằng lệnh: pip install selenium webdriver-manager")

        # Tự động cài đặt nếu được phép
        import sys
        response = input("Bạn có muốn tự động cài đặt? (y/n): ").lower()
        if response == 'y':
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "selenium", "webdriver-manager"])
            print("✅ Cài đặt thành công!")
            return True
        else:
            return False


# Điểm vào chính
if __name__ == "__main__":
    print("=" * 60)
    print("🪙 SCRAPER GIÁ VÀNG - GIAVANG.NET")
    print("=" * 60)

    # Kiểm tra và cài đặt
    if not setup_selenium():
        print("❌ Không thể tiếp tục. Vui lòng cài đặt thủ công.")
        exit(1)

    # Chạy scraper
    start_time = time.time()
    result = scrape_giavang_net()
    end_time = time.time()

    print(f"\n⏱️ Thời gian thực thi: {end_time - start_time:.2f} giây")

    if result and result["status"] == "success":
        print(f"\n✨ Hoàn thành! Kiểm tra file 'giavang.json' để xem dữ liệu.")
    else:
        print(f"\n⚠️ Có vấn đề xảy ra. Kiểm tra file 'giavang.json' để biết chi tiết.")
