from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import joblib
import re
import numpy as np
import pandas as pd
import requests
import os
import time

# --- CẤU HÌNH ĐƯỜNG DẪN ---
app = Flask(__name__, template_folder='../website', static_folder='../website', static_url_path='')
CORS(app)

# --- 1. TẢI CÁC "BỘ NÃO" VÀ DỮ LIỆU ---
try:
    trust_model = joblib.load("trust_model.pkl")
    spam_model = joblib.load("spam_model.pkl")
    print("✅ Đã tải 2 mô hình AI thành công!")
except FileNotFoundError:
    print("⚠️ CẢNH BÁO: Không tìm thấy file '.pkl'. Phần phân tích AI sẽ dùng điểm trung bình.")
    trust_model = None
    spam_model = None

try:
    # Tải "Sổ tay giá" từ file bạn cung cấp
    official_prices_df = pd.read_csv("official_prices.csv")
    print(f"✅ Đã tải Sổ tay giá ({len(official_prices_df)} sản phẩm) thành công!")
except FileNotFoundError:
    print("⚠️ CẢNH BÁO: Không tìm thấy file 'official_prices.csv'. Phần phân tích giá sẽ dùng điểm trung lập.")
    official_prices_df = None

# --- 2. CÁC HÀM GỌI API TIKI ---
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*"
}


def fetch_all_tiki_data(product_id):
    product_details = {}
    reviews_data = []  # List of dictionaries

    # 1. Gọi API Lấy Chi tiết Sản phẩm
    try:
        detail_url = f"https://tiki.vn/api/v2/products/{product_id}"
        r_detail = requests.get(detail_url, headers=HEADERS, timeout=5)
        if r_detail.status_code == 200:
            data = r_detail.json()
            product_details.update({
                "name": data.get("name", "N/A"),
                "price": data.get("price", 0),
                "original_price": data.get("original_price", 0),
                "image_url": data.get("thumbnail_url", ""),
                "seller_name": data.get("current_seller", {}).get("name", "N/A"),
                "sold_count": data.get("quantity_sold", {}).get("value", 0),
                "rating_average": data.get("rating_average", 0),
                "review_count": data.get("review_count", 0)
            })
    except Exception as e:
        print(f"❌ Lỗi gọi API Product: {e}")

    # 2. Gọi API Lấy Review (lấy tối đa 100)
    try:
        reviews_url = "https://tiki.vn/api/v2/reviews"
        for page in range(1, 6):
            params = {"limit": 20, "include": "comments", "sort": "score|desc,id|desc,stars|all", "page": page,
                      "product_id": product_id}
            r_review = requests.get(reviews_url, headers=HEADERS, params=params, timeout=5)
            if r_review.status_code != 200: break
            items = r_review.json().get("data", [])
            if not items: break
            for item in items:
                reviews_data.append({
                    "rating": item.get("rating"),
                    "content": item.get("content", "")
                })
            time.sleep(0.1)
    except Exception as e:
        print(f"❌ Lỗi gọi API Reviews: {e}")

    return product_details, reviews_data


# --- 3. CÁC HÀM PHÂN TÍCH (REVIEW & GIÁ) ---
def clean_text(text):
    if not isinstance(text, str): return ""
    text = text.lower()
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def analyze_reviews(reviews_data):
    analysis = {
        "score": 50,  # Điểm trung bình
        "positive_reviews": [],
        "negative_reviews": [],
        "summary": "Không đủ dữ liệu hoặc mô hình AI chưa sẵn sàng."
    }

    if not reviews_data or (not trust_model or not spam_model):
        return analysis

    reviews_clean = [clean_text(r['content']) for r in reviews_data if r.get('content')]
    if not reviews_clean:
        return analysis

    # Chạy 2 mô hình AI
    trust_preds = trust_model.predict(reviews_clean)
    spam_preds = spam_model.predict(reviews_clean)

    # Tính điểm
    trust_score_part = (1 - np.mean(trust_preds)) * 20  # 20%
    spam_score_part = (1 - (np.mean(spam_preds) / 3.0)) * 80  # 80%
    analysis["score"] = int(trust_score_part + spam_score_part)

    # Tìm review Tốt/Xấu nhất
    sorted_reviews = sorted(reviews_data, key=lambda r: r.get('rating', 0), reverse=True)
    analysis["positive_reviews"] = [r['content'] for r in sorted_reviews if r.get('rating', 0) >= 4][:3]
    analysis["negative_reviews"] = [r['content'] for r in reversed(sorted_reviews) if r.get('rating', 0) <= 2][:3]

    # Tạo nhận xét
    if np.mean(spam_preds) > 1.5:
        analysis["summary"] = "Cảnh báo: Nhiều review có dấu hiệu seeding/spam, làm giảm độ khách quan."
    elif len(analysis["negative_reviews"]) > 1:
        analysis["summary"] = "Lưu ý: Có một số review phàn nàn về chất lượng, cần xem xét kỹ."
    else:
        analysis["summary"] = "Đa số review là tích cực, chất lượng review khá tốt."

    return analysis


def analyze_price(product_details, df_prices):
    analysis = {
        "score": 50,  # Điểm trung bình
        "official_price": None,
        "difference": None,
        "summary": "Không có dữ liệu giá chuẩn để so sánh."
    }

    name = product_details.get("name", "").lower()
    price = product_details.get("price", 0)

    if df_prices is None or not name or price == 0:
        return analysis

    # Tìm giá trong "Sổ tay"
    for index, row in df_prices.iterrows():
        # Kiểm tra cả brand và tên sản phẩm để tăng độ chính xác
        brand_match = str(row.get('brand', '')).lower() in name
        name_match = str(row.get('product_name_official', '')).lower() in name
        if brand_match and name_match:
            official_price = row['official_price']
            analysis["official_price"] = official_price

            diff = (price - official_price) / official_price
            analysis["difference"] = diff

            if diff < -0.4:  # Rẻ hơn 40%
                analysis["score"] = 10
                analysis["summary"] = "Cảnh báo: Giá rẻ hơn đáng kể so với giá chuẩn, nguy cơ hàng giả cao."
            elif diff > 0.1:  # Đắt hơn 10%
                analysis["score"] = 70
                analysis["summary"] = "Lưu ý: Giá đang cao hơn so với giá niêm yết."
            else:  # Giá tốt
                analysis["score"] = 95
                analysis["summary"] = "Giá bán hợp lý, sát với giá niêm yết của hãng."
            return analysis

    return analysis


# --- 4. API CHÍNH (WEB GỌI VỀ ĐÂY) ---
@app.route("/analyze_url", methods=["POST"])
def analyze_url():
    url = request.json.get("url", "")

    product_id = None
    match = re.search(r'-p(\d+)\.html', url)
    if match: product_id = match.group(1)
    if not product_id:
        return jsonify({"error": "Link Tiki không hợp lệ."}), 400

    # Lấy dữ liệu
    product_details, reviews_data = fetch_all_tiki_data(product_id)
    if not product_details:
        return jsonify({"error": "Không thể lấy thông tin sản phẩm từ API Tiki."}), 500

    # Phân tích
    review_analysis = analyze_reviews(reviews_data)
    price_analysis = analyze_price(product_details, official_prices_df)

    # Tính điểm tổng (70% Review, 30% Giá)
    final_score = int(review_analysis["score"] * 0.7 + price_analysis["score"] * 0.3)

    # Tạo lý giải
    final_summary = f"Điểm tổng hợp dựa trên {len(reviews_data)} reviews và phân tích giá. "
    if final_score < 50:
        final_summary += "Sản phẩm có nhiều rủi ro, cần cân nhắc kỹ trước khi mua."
    elif final_score < 75:
        final_summary += "Sản phẩm ở mức chấp nhận được, nhưng vẫn có một vài điểm cần lưu ý."
    else:
        final_summary += "Sản phẩm có độ tin cậy tốt, đáng để tham khảo."

    # Trả về JSON "siêu chi tiết"
    return jsonify({
        "product_info": product_details,
        "review_analysis": review_analysis,
        "price_analysis": price_analysis,
        "final_score": final_score,
        "final_summary": final_summary
    })


# --- 5. API ĐỂ HIỂN THỊ TRANG WEB ---
@app.route("/")
def home():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)

