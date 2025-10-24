from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import joblib
import re
import numpy as np
import pandas as pd
import requests
import os
import time
from unidecode import unidecode
from datetime import datetime, timedelta
from pyvi import ViTokenizer
from collections import Counter

# --- ASYNC & PLAYWRIGHT IMPORTS ---
import asyncio
from playwright.async_api import async_playwright
import nest_asyncio


# 1. Lấy thư mục chứa file app.py (thư mục 'server')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 2. Lấy thư mục gốc của dự án (thư mục 'FINAL_PRODUCT')
PARENT_DIR = os.path.dirname(BASE_DIR)

# 3. Định nghĩa đường dẫn tuyệt đối đến thư mục Frontend
FRONTEND_DIR = os.path.join(PARENT_DIR, 'website')

# Áp dụng nest_asyncio để cho phép chạy asyncio trong môi trường sync (Colab/Jupyter)
try:
  nest_asyncio.apply()
except Exception as e:
  # Bỏ qua nếu đã áp dụng
  pass

# --- CONFIG ---
app = Flask(__name__, template_folder=FRONTEND_DIR, static_folder=FRONTEND_DIR, static_url_path='/')
CORS(app)

VIETNAMESE_STOPWORDS = {
  'là', 'của', 'và', 'các', 'có', 'cho', 'không', 'với', 'như', 'đã', 'bị', 'mà', 'thì',
  'rất', 'quá', 'cũng', 'được', 'nhưng', 'tại', 'bởi', 'vì', 'sao', 'để', 'một', 'hai',
  'ba', 'bốn', 'năm', 'sáu', 'bảy', 'tám', 'chín', 'mười', 'nhiều', 'ít', 'khác', 'trong',
  'ngoài', 'trên', 'dưới', 'trước', 'sau', 'đây', 'kia', 'đó', 'này', 'ấy', 'về', 'việc',
  'thấy', 'nhìn', 'nói', 'làm', 'ra', 'vào', 'tuy', 'khi', 'thì', 'mà', 'còn', 'lại',
  'đến', 'nhận', 'hàng', 'shop', 'giao', 'nhanh', 'mua', 'sản', 'phẩm', 'chất', 'lượng',
  'ok', 'tốt', 'thời', 'gian', 'gói', 'hỗ', 'trợ', 'tư', 'vấn', 'shipper', 'admin', 'mình',
  'nên', 'lắm', 'khá', 'hơi', 'chưa', 'thật', 'sự', 'hợp', 'giá', 'tiền', 'ổn'
}

# --- 1. LOAD MODELS & DATA ---
try:
  TRUST_MODEL_PATH = os.path.join(BASE_DIR, 'trust_model.pkl')
  trust_model = joblib.load(TRUST_MODEL_PATH)
  SPAM_MODEL_PATH = os.path.join(BASE_DIR, 'spam_model.pkl')
  spam_model = joblib.load(SPAM_MODEL_PATH)
  print("AI models loaded successfully!")
except FileNotFoundError:
  print("WARNING: '.pkl' files not found. AI analysis will use average scores.")
  trust_model = None
  spam_model = None

try:
  PRICE_FILE_PATH = os.path.join(BASE_DIR, 'official_prices.csv')
  official_prices_df = pd.read_csv(PRICE_FILE_PATH)
  print(f"Price reference loaded ({len(official_prices_df)} products).")
except FileNotFoundError:
  print("WARNING: 'official_prices.csv' not found. Price analysis will use neutral scores.")
  official_prices_df = None

# --- 2. API CALL FUNCTIONS ---
HEADERS = {
  "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
  "Accept": "application/json, text/plain, */*"
}

def extract_ids_from_url(url):
  mpid, spid = None, None
  match_mpid = re.search(r'-p(\d+)\.html', url)
  if match_mpid: mpid = match_mpid.group(1)
  match_spid = re.search(r'spid=(\d+)', url)
  if match_spid: spid = match_spid.group(1)
  return mpid, spid

def fetch_all_tiki_data(product_id):
  product_details, reviews_data = {}, []
  try:
      detail_url = f"https://tiki.vn/api/v2/products/{product_id}"
      r_detail = requests.get(detail_url, headers=HEADERS, timeout=10)
      if r_detail.status_code == 200:
          data = r_detail.json()
          seller_id = data.get("current_seller", {}).get("id")
          product_details.update({
              "name": data.get("name", "N/A"), "price": data.get("price", 0),
              "original_price": data.get("original_price", 0), "image_url": data.get("thumbnail_url", ""),
              "seller_id": seller_id, "seller_name": data.get("current_seller", {}).get("name", "N/A"),
              "sold_count": data.get("quantity_sold", {}).get("value", 0),
              "rating_average": data.get("rating_average", 0), "review_count": data.get("review_count", 0)
          })
      else:
          print(f"Product API returned status {r_detail.status_code}")
          return None, []
  except Exception as e:
      print(f"Error calling Product API: {e}")
      return None, []

  try:
      reviews_url = "https://tiki.vn/api/v2/reviews"
      for page in range(1, 6):
          params = {"limit": 20, "include": "comments", "sort": "score|desc,id|desc,stars|all", "page": page,
                    "product_id": product_id}
          r_review = requests.get(reviews_url, headers=HEADERS, params=params, timeout=15)
          if r_review.status_code != 200: break
          items = r_review.json().get("data", [])
          if not items: break
          for item in items: reviews_data.append({"rating": item.get("rating"), "content": item.get("content", "")})
          time.sleep(0.1)
  except Exception as e:
      print(f"Error calling Reviews API: {e}")
  return product_details, reviews_data

def fetch_seller_metrics(mpid, spid, seller_id):
  seller_metrics = {}
  if not seller_id or seller_id == "N/A":
      print("Invalid seller_id for Seller Widget API.")
      return seller_metrics
  widget_api_url = f"https://api.tiki.vn/product-detail/v2/widgets/seller?seller_id={seller_id}&mpid={mpid}&spid={spid}&platform=desktop&version=3"
  try:
      response = requests.get(widget_api_url, headers=HEADERS, timeout=10)
      response.raise_for_status()
      data = response.json()
      seller_data = data.get('data', {}).get('seller')
      if seller_data and isinstance(seller_data, dict):
          days_joined = seller_data.get('days_since_joined')
          date_joined_str, years_active = "N/A", 0
          if days_joined is not None and isinstance(days_joined, int) and days_joined >= 0:
              date_joined = (datetime.now() - timedelta(days=days_joined))
              date_joined_str = date_joined.strftime('%Y-%m-%d')
              years_active = max(0, (datetime.now() - date_joined).days / 365.25)

          seller_rating = 0.0
          seller_rating_raw = seller_data.get('avg_rating_point')
          if seller_rating_raw is not None:
              try:
                  seller_rating = float(seller_rating_raw)
              except (ValueError, TypeError):
                  seller_rating = 0.0

          follower_count = 0
          follower_raw = seller_data.get('total_follower')
          if follower_raw is not None:
              try:
                  follower_count = int(follower_raw)
              except (ValueError, TypeError):
                  follower_count = 0

          review_count_widget = 0
          review_count_raw = seller_data.get('review_count')
          if review_count_raw is not None:
              try:
                  review_count_widget = int(review_count_raw)
              except (ValueError, TypeError):
                  review_count_widget = 0

          seller_metrics = {
              "seller_id": seller_data.get('id', 'N/A'), "seller_name_widget": seller_data.get('name', 'N/A'),
              "date_joined": date_joined_str, "years_active": round(years_active, 1),
              "follower_count": follower_count, "seller_rating": seller_rating,
              "review_count_widget": review_count_widget, "is_official_store": seller_data.get('is_official', False),
          }
      else:
          print("Invalid seller data from Widget API.")
  except requests.exceptions.RequestException as e:
      print(f"Error calling Seller Widget API: {e}")
  except Exception as e:
      print(f"Unknown error processing Seller Widget API: {e}")
  return seller_metrics

# --- 3. HELPER FUNCTIONS ---
def clean_text(text):
  if not isinstance(text, str): return ""
  text = text.lower();
  text = re.sub(r'<[^>]+>', '', text);
  text = re.sub(r'\s+', ' ', text).strip()
  return text

def normalize_volume(text):
  if not isinstance(text, str) or text == '—': return ""
  return text.lower().replace(" ", "")

def format_price_py(price):
  if price is not None and price > 0: return f"{price:,.0f} ₫".replace(",", ".")
  return "N/A"

def remove_accents(text):
  if not isinstance(text, str): return ""
  return unidecode(text).lower()

def format_big_number_py(num):
  """Format large numbers for display (Python version)."""
  if num is None or num == "N/A": return "N/A"
  try:
      number = int(num)
      if number >= 1_000_000: return f"{number / 1_000_000:.1f} Tr"
      if number >= 1_000: return f"{number / 1_000:.0f} K"
      return str(number)
  except (ValueError, TypeError):
      return "N/A"

# --- 4. ANALYSIS FUNCTIONS ---

def analyze_reviews(reviews_data):
  analysis = {
      "score": 50, "positive_reviews": [], "negative_reviews": [],
      "summary": "No data or AI models unavailable.",
      "star_distribution": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
      "ai_analysis": {"real": 0, "spam": 0}, "word_cloud": []
  }
  if not reviews_data or (not trust_model or not spam_model): return analysis

  reviews_with_content = [r for r in reviews_data if r.get('content')]
  if not reviews_with_content:
      analysis["summary"] = "Reviews lack content.";
      return analysis
  reviews_clean = [clean_text(r['content']) for r in reviews_with_content]

  try:
      trust_preds = trust_model.predict(reviews_clean)
      spam_preds = spam_model.predict(reviews_clean)
  except Exception as e:
      print(f" Error during AI prediction: {e}");
      analysis["summary"] = "Error analyzing reviews with AI.";
      return analysis

  trust_score_part = (1 - np.mean(trust_preds)) * 20
  spam_score_part = (1 - (np.mean(spam_preds) / 3.0)) * 80
  analysis["score"] = max(0, min(100, int(trust_score_part + spam_score_part)))

  real_reviews_text, positive_list, negative_list = [], [], []
  star_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
  spam_count = 0;
  total_reviews_with_content = len(reviews_clean)

  for i, review in enumerate(reviews_with_content):
      content, rating = review['content'], review.get('rating', 0)
      is_spam, is_trustworthy = spam_preds[i] != 0, trust_preds[i] == 0
      if is_spam:
          spam_count += 1
      else:
          if rating <= 3: real_reviews_text.append(content)
          if rating >= 4 and is_trustworthy:
              positive_list.append(content)
          elif rating <= 2:
              negative_list.append(content)

  for review in reviews_data:
      rating = review.get('rating', 0)
      if rating in star_counts: star_counts[rating] += 1

  analysis["star_distribution"] = star_counts
  analysis["ai_analysis"] = {"real": total_reviews_with_content - spam_count, "spam": spam_count}
  np.random.shuffle(positive_list);
  np.random.shuffle(negative_list)
  analysis["positive_reviews"] = positive_list[:3]
  analysis["negative_reviews"] = negative_list[:3]

  if total_reviews_with_content > 0:
      spam_ratio_display = int((spam_count / total_reviews_with_content) * 100)
      if spam_ratio_display > 30:
          analysis[
              "summary"] = f"Warning: ~{spam_ratio_display}% reviews ({spam_count}/{total_reviews_with_content}) flagged as potential spam/seeding."
      elif len(analysis["negative_reviews"]) > 0:
          analysis["summary"] = ""
      else:
          analysis[
              "summary"] = f"Mostly positive and trustworthy reviews ({analysis['ai_analysis']['real']}/{total_reviews_with_content})."

  try:
      full_text = " ".join(real_reviews_text).lower()
      tokenized_string = ViTokenizer.tokenize(full_text)
      tokens = tokenized_string.split()
      word_counts = Counter(tokens)
      filtered_words = [[word, count] for word, count in word_counts.items() if
                        word not in VIETNAMESE_STOPWORDS and len(word) > 2 and count > 1]
      filtered_words.sort(key=lambda x: x[1], reverse=True)
      analysis["word_cloud"] = filtered_words[:40]
  except Exception as e:
      print(f"Error creating Word Cloud: {e}"); analysis["word_cloud"] = []
  return analysis

def analyze_price(product_details, df_prices):
  # Khởi tạo analysis, thêm 'suggestion': None ngay từ đầu
  analysis = {"score": 50, "official_price": None, "difference": None,
              "summary": "Không có dữ liệu giá chuẩn.", "suggestion": None} # <-- KHỞI TẠO suggestion


  tiki_name, tiki_price = product_details.get("name", ""), product_details.get("price", 0)


  # Kiểm tra đầu vào kỹ hơn
  if df_prices is None or not isinstance(df_prices, pd.DataFrame):
       analysis["summary"] = "Lỗi dữ liệu giá chuẩn (không phải DataFrame)."
       return analysis
  if not tiki_name or not isinstance(tiki_price, (int, float)) or tiki_price <= 0:
       analysis["summary"] = "Tên hoặc giá sản phẩm Tiki không hợp lệ."
       return analysis # Thoát sớm nếu giá Tiki không hợp lệ


  tiki_name_no_accent, tiki_name_normalized = remove_accents(tiki_name), normalize_volume(tiki_name)


  found_match = False # Biến cờ để biết có tìm thấy khớp không
  for index, row in df_prices.iterrows():
      try: # Thêm try-except để xử lý lỗi từng dòng CSV
           brand_csv, type_csv, volume_csv = remove_accents(row.get('brand_name', '')), remove_accents(
               row.get('product_type', '')), normalize_volume(row.get('volume_weight', ''))
           official_link = row.get('url', None) # <-- LẤY LINK TỪ CSV


           # Logic khớp (giữ nguyên)
           if not brand_csv or brand_csv == '—' or brand_csv not in tiki_name_no_accent: continue
           if type_csv and type_csv != '—' and type_csv not in tiki_name_no_accent: continue
           if volume_csv and volume_csv not in tiki_name_normalized: continue


           # --- Match Found ---
           found_match = True
           official_price_str = str(row.get('old_price', '0'))
           official_price = int(re.sub(r'[^\d]', '', official_price_str))
           if 0 < official_price < 10000: official_price *= 1000


           if official_price <= 0: # Bỏ qua nếu giá chuẩn không hợp lệ
               print(f"Giá chuẩn không hợp lệ ({official_price}) cho dòng {index}")
               found_match = False # Coi như không khớp nếu giá sai
               continue # Duyệt dòng tiếp theo


           analysis["official_price"] = official_price
           diff = (tiki_price - official_price) / official_price
           analysis["difference"] = diff


           # --- THÊM LOGIC ĐỀ XUẤT LINK ---
           if diff > 0.05 and official_link and pd.notna(official_link) and str(official_link).strip().startswith('http'): # Kiểm tra link hợp lệ hơn
               analysis["suggestion"] = {
                   "text": "Giá hiện tại cao hơn giá chuẩn. Tham khảo link chính hãng:",
                   "link": str(official_link)
               }
           else:
               analysis["suggestion"] = None # Đảm bảo reset nếu không đủ điều kiện
           # --- KẾT THÚC LOGIC ĐỀ XUẤT ---


           formatted_official = format_price_py(official_price);
           diff_percent = abs(diff * 100)


           # Logic tính điểm và summary (giữ nguyên)
           if diff < -0.7:
               score, summary = 10, f"Cảnh báo: Rẻ bất thường ({diff_percent:.0f}%) so với giá gốc ({formatted_official}). Rủi ro cao."
           elif diff < -0.4:
               score, summary = 95, f"Giá siêu tốt! Rẻ hơn {diff_percent:.0f}% so với giá gốc ({formatted_official}). Thường là giá Sale/Clearance."
           elif diff > 0.1: # Chỉ cần diff > 0.1 là đủ (không cần > 0.05 nữa vì suggestion đã xử lý)
               score, summary = 70, f"Lưu ý: Cao hơn {diff_percent:.0f}% so với giá niêm yết ({formatted_official})."
           else: # Giá tốt hoặc chỉ cao hơn < 10%
               score, summary = 90, f"Giá hợp lý, sát hoặc tốt hơn giá niêm yết ({formatted_official})."


           analysis["score"], analysis["summary"] = score, summary
           break # Thoát vòng lặp ngay khi tìm thấy và xử lý xong


      except Exception as e:
           print(f"Lỗi khi xử lý dòng CSV {index} cho giá: {e}")
           continue # Bỏ qua dòng lỗi, duyệt tiếp

  # Xử lý trường hợp không tìm thấy khớp nào sau khi duyệt hết vòng lặp
  if not found_match:
       analysis["summary"] = "Không tìm thấy giá chuẩn khớp với sản phẩm này."
       analysis["official_price"] = None
       analysis["difference"] = None
       analysis["suggestion"] = None
       analysis["score"] = 50 # Đặt điểm trung bình


  return analysis

def analyze_seller(seller_metrics):
  """ Tính điểm Seller Score và tạo summary sâu sắc hơn """
  analysis = {"score": 30, "summary": "Chưa đủ thông tin đánh giá người bán.", "status_text": "N/A",
              "rating_text": "N/A", "seniority_text": "N/A", "followers_text": "N/A"}
  if not seller_metrics: return analysis

  score = 0
  status_score, rating_score, seniority_score, followers_score = 0, 0, 0, 0
  status_class, rating_class, seniority_class, followers_class = "warn", "warn", "warn", "warn"

  is_official = seller_metrics.get("is_official_store", False)
  is_tiki_trading = "tiki trading" in seller_metrics.get("seller_name_widget", "").lower()
  if is_official or is_tiki_trading:
      status_score = 45
      analysis["status_text"] = "Official Store" if is_official else "Tiki Trading"
      status_class = "good"
  else:
      status_score = 0
      analysis["status_text"] = "ℹ️ Shop thường"
      status_class = "info"

  rating = seller_metrics.get("seller_rating", 0.0)
  review_count = seller_metrics.get("review_count_widget", 0)
  analysis[
      "rating_text"] = f"{rating:.1f} ({format_big_number_py(review_count)})" if review_count > 0 else "Chưa có đánh giá"
  if rating >= 4.7 and review_count >= 1000:
      rating_score = 35
      rating_class = "good"
  elif rating >= 4.5 and review_count >= 500:
      rating_score = 25
      rating_class = "good"
  elif rating >= 4.0 and review_count >= 100:
      rating_score = 15
      rating_class = "warn"
  elif rating > 0:
      rating_score = 5
      rating_class = "bad"
      analysis["rating_text"] += " (Thấp/Ít)"
  else:
      rating_score = 0
      rating_class = "info"

  years = seller_metrics.get("years_active", 0)
  joined_date = seller_metrics.get("date_joined", "N/A")
  analysis["seniority_text"] = f"{years:.1f} năm (từ {joined_date})" if years > 0 else "Mới tham gia"
  if years >= 5:
      seniority_score = 15
      seniority_class = "good"
  elif years >= 3:
      seniority_score = 10
      seniority_class = "good"
  elif years >= 1:
      seniority_score = 5
      seniority_class = "warn"
  else:
      seniority_score = 0
      seniority_class = "bad"

  followers = seller_metrics.get("follower_count", 0)
  analysis["followers_text"] = format_big_number_py(followers)
  if followers > 100000:
      followers_score = 5
      followers_class = "good"
  elif followers > 10000:
      followers_score = 2
      followers_class = "info"
  else:
      followers_score = 0
      followers_class = "info"

  score = status_score + rating_score + seniority_score + followers_score
  analysis["score"] = max(0, min(100, int(score)))

  if analysis["score"] >= 80:
      summary = "Người bán có độ uy tín rất cao."
  elif analysis["score"] >= 60:
      summary = "Người bán đáng tin cậy."
  elif analysis["score"] >= 40:
      summary = "Người bán ở mức chấp nhận được, cần xem xét thêm."
  else:
      summary = "Người bán có nhiều yếu tố rủi ro (shop mới, đánh giá thấp...)."

  analysis["status_class"] = status_class
  analysis["rating_class"] = rating_class
  analysis["seniority_class"] = seniority_class
  analysis["followers_class"] = followers_class
  analysis["summary"] = summary

  return analysis

# --- HÀM MÔ PHỎNG LỌC ẢNH SỬ DỤNG AI/LOGIC ---
def filter_product_images_mock(image_urls: list[str]) -> list[str]:

  # Lọc các URL không chứa các từ khóa liên quan đến ảnh đại diện người dùng
  filtered_urls = [
      url for url in image_urls
      if "avatar" not in url.lower() and "profile" not in url.lower() and "w750" in url.lower()
  ]

  # Giữ lại tối đa 20 ảnh (để frontend hiển thị nhanh hơn)
  return filtered_urls[:20]

# --- HÀM CÀO ẢNH BẰNG PLAYWRIGHT (ASYNC) ---
MAX_REVIEW_IMAGES_LIMIT = 100

async def crawl_review_images_playwright(url: str) -> list[str]:
  """Cào URL ảnh review bằng Playwright (async)."""
  images_list: list[str] = []

  try:
      async with async_playwright() as p:
          # Sử dụng 'headless=True' cho môi trường production
          browser = await p.chromium.launch()
          page = await browser.new_page()

          print(f"[Scraping] Đang tải trang: {url}")
          await page.goto(url, timeout=60000)

          # 1. Cuộn trang để tải phần Review (rất quan trọng)
          await page.evaluate("window.scrollTo(0, 3000);")
          await page.wait_for_timeout(3000)

          # 2. Bấm vào nút "Có hình ảnh" để hiển thị TẤT CẢ reviews có ảnh
          try:
              photo_filter_button = page.locator('button:has-text("Có hình ảnh")')
              if await photo_filter_button.is_visible():
                  await photo_filter_button.click()
                  print("   -> [Scraping] Đã bấm nút 'Có hình ảnh' để lọc")
                  await page.wait_for_timeout(1000)
          except Exception:
              pass

              # 3. Trích xuất URL từ tất cả các phần tử ảnh
          image_selectors = [".thumbnail-list__item", ".review-images__img"]
          image_elements = []
          for selector in image_selectors:
              image_elements.extend(await page.locator(selector).all())

          print(f"   -> [Scraping] Tìm thấy tổng cộng {len(image_elements)} phần tử ảnh...")

          for element in image_elements:
              if len(images_list) >= MAX_REVIEW_IMAGES_LIMIT: break

              style = await element.get_attribute("style")
              if style:
                  # Dùng regex để trích xuất URL bên trong url(...)
                  match = re.search(r'url\("?(.+?)"?\)', style)
                  if match:
                      img_url_thumb = match.group(1).strip()
                      # Thay đổi w280/w200 thành w750 để lấy ảnh chất lượng cao
                      img_url_full = img_url_thumb.replace("/w280/", "/w750/").replace("/w200/", "/w750/")
                      if img_url_full not in images_list:
                          images_list.append(img_url_full)
          await browser.close()
  except Exception as e:
      print(f"[Scraping] Lỗi Playwright: {e}")

  return images_list


@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(FRONTEND_DIR, path)

# --- 5. MAIN API ROUTE (ĐÃ BỔ SUNG PLAYWRIGHT) ---
@app.route("/analyze_url", methods=["POST"])
def analyze_url():
  url = request.json.get("url", "")
  mpid, spid = extract_ids_from_url(url)
  if not mpid or not spid:
      print(f"Insufficient IDs extracted: mpid={mpid}, spid={spid}")
      return jsonify({"error": "Invalid Tiki URL or missing spid parameter."}), 400

  product_details, reviews_data = fetch_all_tiki_data(mpid)
  if not product_details:
      return jsonify({"error": "Could not fetch product details from Tiki API."}), 500

  seller_id = product_details.get("seller_id")
  seller_metrics = fetch_seller_metrics(mpid, spid, seller_id)
  product_details.update(seller_metrics)

  # --- TÍCH HỢP PLAYWRIGHT BẰNG ASYNCIO.RUN() ---
  print(f"\n--- BẮT ĐẦU CÀO ẢNH ĐỘNG BẰNG PLAYWRIGHT CHO URL: {url} ---")
  raw_image_urls = asyncio.run(crawl_review_images_playwright(url))

  # BƯỚC MỚI: LỌC ẢNH SỬ DỤNG HÀM MÔ PHỎNG
  filtered_image_urls = filter_product_images_mock(raw_image_urls)

  # Thêm URL ảnh review ĐÃ LỌC vào product_info
  product_details['review_image_urls'] = filtered_image_urls

  # DÒNG IN KẾT QUẢ CÀO ẢNH RA CONSOLE/TERMINAL
  print("\n=======================================================")
  print(f"Đã cào được {len(raw_image_urls)} URL ảnh review, sau khi lọc còn {len(filtered_image_urls)} ảnh.")
  # Dòng in ra toàn bộ danh sách URL ảnh đã lọc
  print(f"Danh sách URL ảnh đã lọc của feedback: {filtered_image_urls}")
  print("=======================================================\n")
  # --- KẾT THÚC PLAYWRIGHT ---

  review_analysis = analyze_reviews(reviews_data)
  price_analysis = analyze_price(product_details, official_prices_df)
  seller_analysis = analyze_seller(seller_metrics)

  # Weighted score: Review 50%, Seller 30%, Price 20%
  final_score = int(review_analysis["score"] * 0.5 + seller_analysis["score"] * 0.3 + price_analysis["score"] * 0.2)
  final_score = max(0, min(100, final_score))

  num_reviews = len(reviews_data)
  final_summary = f"Được đánh giá dựa trên {num_reviews} reviews, hành vi của người bán, và độ chênh lệch giá. "
  if final_score < 40:
      final_summary += "High risk, consider carefully."
  elif final_score < 70:
      final_summary += "⚠Acceptable, but check details."
  else:
      final_summary += "Good reliability, worth considering."
  if price_analysis["score"] <= 10: final_summary += "Price warning: unusually cheap!"

  return jsonify({
      "product_info": product_details, "review_analysis": review_analysis,
      "price_analysis": price_analysis, "seller_analysis": seller_analysis,
      "final_score": final_score, "final_summary": final_summary,
      "scraped_images_count": len(raw_image_urls)
  })

# --- 6. ROOT ROUTE ---
@app.route('/')
def serve_index():
    return send_from_directory(FRONTEND_DIR, 'index.html')

if __name__ == "__main__":
  app.run(host="0.0.0.0", port=5000, debug=False)
