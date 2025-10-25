from playwright.sync_api import sync_playwright
import csv
import time
import random
import re
from typing import Tuple, Dict, List, Any

# --- THÔNG SỐ CẤU HÌNH ĐÃ CẬP NHẬT ---
OUTPUT_FILE = "dataset_goc_guardian.csv"
CATEGORY_URL = "https://www.guardian.com.vn/cham-soc-da-mat.html"
BASE_URL = "https://www.guardian.com.vn"
TARGET_COUNT = 300
PRODUCTS_PER_PAGE = 20

# --- HÀM CHUẨN HÓA VÀ XỬ LÝ DỮ LIỆU ---

def clean_and_normalize_price(old_p_str: str, curr_p_str: str) -> Tuple[str, str]:
    """
    Chuẩn hóa giá:
    - Nếu không cào được Giá Gốc, đặt Giá Gốc = Giá Hiện Tại.
    - KHÔNG hoán đổi giá trị nếu Giá Gốc < Giá Hiện Tại.
    """

    def clean_price(p_str: str) -> int:
        # Loại bỏ ký tự không phải số và chuyển thành số nguyên (hoặc 0 nếu là '—')
        return int(re.sub(r'[^\d]', '', p_str)) if p_str.strip() and p_str.strip() != '—' else 0

    def format_price(p_int: int) -> str:
        # Định dạng lại giá trị về chuỗi có dấu phân cách hàng nghìn
        return f"{p_int:,}" if p_int > 0 else "—"

    # 1. Làm sạch và chuyển đổi thành số
    p1 = clean_price(old_p_str)
    p2 = clean_price(curr_p_str)

    if p2 == 0:
        return "—", "—"

    if p1 == 0:
        # TRƯỜNG HỢP KHÔNG GIẢM GIÁ (Giá Gốc = Giá Hiện Tại)
        return format_price(p2), format_price(p2)
    else:
        # TRƯỜNG HỢP CÓ GIẢM GIÁ (Giữ nguyên giá trị cào được)
        return format_price(p1), format_price(p2)


def extract_volume_weight_and_type(title: str) -> Tuple[str, str]:
    """Trích xuất định lượng và loại sản phẩm."""
    volume_weight = "—"
    product_type = "Khác"
    volume_match = re.search(r'(\d+[\.\,]?\d*\s*(?:ml|mg|g|kg))', title, re.IGNORECASE)
    if volume_match:
        volume_weight = volume_match.group(1).strip()

    keywords = {
        "Sữa rửa mặt": ["sữa rửa mặt", "gel rửa mặt", "foam", "cleansing gel"],
        "Kem chống nắng": ["kem chống nắng", "sữa chống nắng", "xịt chống nắng", "sunscreen", "spf"],
        "Tẩy trang": ["nước tẩy trang", "tẩy trang", "dầu tẩy trang", "micellar"],
        "Mặt nạ": ["mặt nạ", "mask"],
        "Tẩy tế bào chết": ["tẩy tế bào chết", "gel tẩy da chết", "tbc", "exfoliator", "scrub"],
        "Nước hoa hồng/Toner": ["toner", "nước hoa hồng", "lotion"],
        "Kem dưỡng": ["kem dưỡng", "dưỡng ẩm"],
        "Serum/Tinh chất": ["tinh chất", "serum"]
    }
    normalized_title = title.lower()
    for category, terms in keywords.items():
        if any(term in normalized_title for term in terms):
            product_type = category
            break

    return volume_weight, product_type

# --- HÀM CÀO DỮ LIỆU CHÍNH ---

def scrape_guardian_category(limit: int = TARGET_COUNT):
    """Cào dữ liệu sản phẩm từ trang danh mục Guardian."""

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True,
                                    args=["--no-sandbox", "--disable-blink-features=AutomationControlled"])
        page = browser.new_page(
            user_agent="Mozilla/50 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

        print(f" Đang mở trang danh mục Guardian: {CATEGORY_URL}")

        # Mở trang và chờ tải
        page.goto(CATEGORY_URL, wait_until="domcontentloaded", timeout=90000)
        time.sleep(random.uniform(5.0, 7.0))

        # --- THU THẬP LIÊN KẾT SẢN PHẨM BẰNG CƠ CHẾ PHÂN TRANG (PAGINATION) ---
        product_links = set()
        max_pages_to_scrape = (limit + PRODUCTS_PER_PAGE - 1) // PRODUCTS_PER_PAGE
        current_page_num = 1

        print(f"Bắt đầu thu thập link sản phẩm (Tối đa {max_pages_to_scrape} trang cần duyệt)...")

        while len(product_links) < limit and current_page_num <= max_pages_to_scrape:
            # 1. Cào link trên trang hiện tại
            links = page.query_selector_all("a.product-item-link")
            for el in links:
                href = el.get_attribute("href")
                if href and href.startswith("/"):
                    product_links.add(BASE_URL + href)
                elif href and href.startswith(BASE_URL):
                    product_links.add(href)

            print(f"   Trang {current_page_num}: Đã cào {len(product_links)} link.")

            if len(product_links) >= limit:
                break

            # 2. Chuyển trang (Sử dụng nút "Next")
            next_button_selector = "a.action.next"
            try:
                # Đảm bảo nút "Next" tồn tại và có thể nhấp
                page.wait_for_selector(next_button_selector, timeout=5000)

                # Kiểm tra thuộc tính disable (nếu có)
                is_disabled = page.is_disabled(next_button_selector)
                if is_disabled:
                    print("⚠️ Đã đạt đến trang cuối cùng của danh mục.")
                    break

                # Nhấp nút và chờ tải trang mới
                page.click(next_button_selector)
                page.wait_for_load_state("domcontentloaded")

                # Tăng thời gian chờ sau click để đảm bảo AJAX/DOM hoàn thành tải sản phẩm
                time.sleep(random.uniform(5.0, 7.0))

                current_page_num += 1
            except Exception:
                # Không tìm thấy nút Next (đã hết trang)
                print("⚠️ Không tìm thấy nút phân trang tiếp theo. Đã đạt đến cuối danh mục.")
                break

        product_links = list(product_links)[:limit]
        print(f"\n Tổng số link cuối cùng được cào chi tiết: {len(product_links)}")

        # --- Cào Chi tiết từng Sản phẩm & Áp dụng Chuẩn hóa Giá ---
        rows: List[Dict[str, Any]] = []
        for idx, url in enumerate(product_links, 1):
            print(f"[{idx}/{len(product_links)}] Cào chi tiết: {url}")
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                time.sleep(random.uniform(1.0, 2.0))

                # Cào thông tin cơ bản
                title = page.query_selector("h1.product-name, h1.page-title span")
                title = title.inner_text().strip() if title else "—"

                brand = page.query_selector(".product-brand-name, .brand-name")
                brand = brand.inner_text().strip() if brand else "—"

                desc_el = page.query_selector(".product-info-main, .product.attribute.description")
                desc = desc_el.inner_text().strip() if desc_el else "—"
                short_desc = (desc[:250].replace('\n', ' ') + "...") if len(desc) > 250 else desc.replace('\n', ' ')

                # 1. CÀO GIÁ THÔ VỚI BỘ CHỌN CHẶT CHẼ

                old_price_el = page.query_selector(".product-info-main .old-price .price")
                old_price_raw = "—"
                current_price_raw = "—"

                if old_price_el:
                    # TRƯỜNG HỢP CÓ GIẢM GIÁ
                    old_price_raw = old_price_el.inner_text().strip()

                    # Giá hiện tại: special-price
                    curr_price_el = page.query_selector(".product-info-main .special-price .price-container .price")
                    if curr_price_el:
                        current_price_raw = curr_price_el.inner_text().strip()

                else:
                    # TRƯỜNG HỢP KHÔNG GIẢM GIÁ

                    # Giá hiện tại: final price
                    curr_price_el = page.query_selector(
                        ".product-info-main .price-final_price .price-container .price"
                    )
                    if curr_price_el:
                        current_price_raw = curr_price_el.inner_text().strip()

                # 2. Chuẩn hóa giá: Áp dụng quy tắc Giá Gốc = Giá Hiện Tại nếu cần
                old_price, current_price = clean_and_normalize_price(old_price_raw, current_price_raw)

                # Trích xuất Định lượng và Loại Sản phẩm
                volume_weight, product_type = extract_volume_weight_and_type(title)

                rows.append({
                    "url": url,
                    "title": title,
                    "brand_name": brand,
                    "product_type": product_type,
                    "volume_weight": volume_weight,
                    "short_description": short_desc,
                    "old_price": old_price,
                    "current_price": current_price
                })

            except Exception as e:
                print(f" Lỗi khi cào {url}: {e}")

            time.sleep(random.uniform(1.0, 2.0))

        # --- Xuất ra file CSV ---
        with open(OUTPUT_FILE, "w", newline="", encoding="utf-8-sig") as f:
            fieldnames = [
                "url", "title", "brand_name", "product_type", "volume_weight",
                "short_description", "old_price", "current_price"
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        print(f"\n Đã lưu {len(rows)} sản phẩm vào {OUTPUT_FILE}")
        browser.close()


if __name__ == "__main__":
    scrape_guardian_category(TARGET_COUNT)