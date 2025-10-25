# **README - WEBSITE HỖ TRỢ ĐÁNH GIÁ ĐỘ TIN CẬY CỦA SẢN PHẨM TRÊN TIKI**

## 1. GIỚI THIỆU DỰ ÁN

Đây là dự án xây dựng một ứng dụng web sử dụng Trí tuệ Nhân tạo (AI) để phân tích và đánh giá độ tin cậy của sản phẩm trên sàn thương mại điện tử Tiki. Mục tiêu nhằm hỗ trợ người dùng đưa ra quyết định mua sắm thông minh và giảm thiểu rủi ro mua phải hàng kém chất lượng.

### Nhóm Thực hiện (NQN)

| Họ và Tên | Mã số sinh viên |
| :--- | :--- |
| Nguyễn Thị Kim Ngân | 2351050113 |
| Hồ Phạm Như Quỳnh | 2351050149 |
| Nguyễn Lý Mị Nương | 2351050130 |

## 2. VẤN ĐỀ VÀ GIẢI PHÁP

### Vấn đề

Trong xu hướng mua sắm trực tuyến phát triển mạnh mẽ, người tiêu dùng ngày càng khó khăn trong việc phân biệt hàng thật/giả. Họ dễ bị thao túng bởi các thông tin nhiễu như hình ảnh quảng cáo chỉnh sửa, đánh giá "seeding" (review ảo), dẫn đến việc mua phải sản phẩm kém chất lượng và làm giảm trải nghiệm mua sắm.

### Tổng quan Giải pháp

Dự án cung cấp một công cụ tích hợp AI, cho phép người dùng dán liên kết (link) sản phẩm Tiki để nhận được **chỉ số phần trăm độ tin cậy** một cách khách quan. Hệ thống sẽ tự động:

1.  Thu thập dữ liệu sản phẩm, mô tả, và đánh giá.
2.  Sử dụng mô hình AI và Machine Learning để phân tích tính xác thực của các đánh giá.
3.  So sánh mức giá sản phẩm với "giá chuẩn" trên thị trường.
4.  Kết hợp các yếu tố trên bằng thuật toán để đưa ra điểm số cuối cùng.

Công cụ này giúp tiết kiệm thời gian và nâng cao độ chính xác trong quyết định mua sắm.

## 3. KIẾN TRÚC HỆ THỐNG

Dự án được xây dựng theo mô hình **Client-Server**.

### 3.1. Frontend (`website/`)

* Giao diện người dùng tối giản, dễ sử dụng.
* Công nghệ: **HTML, CSS, JavaScript**.
* Chức năng: Thu nhận link sản phẩm từ người dùng và hiển thị kết quả phân tích.

### 3.2. Backend (`server/`)

* Server trung tâm, xử lý các tác vụ nặng.
* Công nghệ: **Python Flask**.
* Chức năng chính:
    * Gọi API Tiki để thu thập dữ liệu sản phẩm (tối đa 100 reviews).
    * Tải và chạy các mô hình AI.
    * Đọc từ điển giá chuẩn (`official_prices.csv`).
    * Tính toán điểm số theo thuật toán và trả về kết quả.

### 3.3. Mô hình Trí tuệ nhân tạo (AI) & ML

Cả hai mô hình AI đều sử dụng thuật toán từ thư viện **Scikit-learn** với **TF-IDF** và **Logistic Regression**.

| Tên Mô hình | Tệp | Mục tiêu | Cơ chế |
| :--- | :--- | :--- | :--- |
| Mô hình Tin cậy | `trust_model.pkl` | Dự đoán review có "đáng tin" (chất lượng/cảm nhận thật) hay không. | Phản ánh chất lượng sản phẩm. Trả về 0 (Đáng tin) hoặc 1 (Không đáng tin). |
| Mô hình Spam | `spam_model.pkl` | Dự đoán review có phải là "review rác" (spam/seeding) hay không. | Đảm bảo tính xác thực của review. Trả về điểm từ 0 (Không spam) đến 3 (Độ spam cao). |

## 4. LOGIC CHẤM ĐIỂM HỆ THỐNG

**Điểm Tổng hợp (Final Score)** được tính bằng công thức trung bình có trọng số, thang điểm từ 0 đến 100.


final\_score =  int(review\_analysis\[“score”] \* 0.5 + seller\_analysis\[“score”] \* 0.3 + price\_analysis\[“score”] * 0.2 )

Trong đó:

50% trọng số đến từ Điểm phân tích dựa trên Review ( review\_analysis\[“score”])

30% trọng số đến từ Điểm phân tích dựa trên Hành vi người bán (seller\_analysis\[“score”])

20% trọng số đến từ Điểm phân tích Giá sản phẩm (price\_analysis\[“score”])

### 4.1. Điểm phân tích dựa trên Review (Trọng số lớn nhất)

**Mục tiêu:** Trả lời cho câu hỏi: *"Các review này có thật không và có đáng tin cậy không?"*

* **Đầu vào:** Tối đa 100 reviews (đã làm sạch dữ liệu).
* **Chạy mô hình AI:**
    * **Trust Model:** Xác định độ hài lòng/không hài lòng (chiếm 20% tổng điểm review).
    * **Spam Model:** Lọc đánh giá giả mạo/spam (chiếm 80% tổng điểm review).
* **Công thức:** 
**Tính điểm thành phần:**

trust\_score\_part: 20%

spam\_score\_part: 80%

**Tổng hợp điểm Review:**

Điểm Review = trust\_score\_part + spam\_score\_part

### 4.2. Điểm phân tích dựa trên Hành vi Người bán (Trọng số 30%)

**Mục tiêu:** Trả lời cho câu hỏi: *"Shop này có thực sự uy tín hay không?"*

| Tiêu chí | Điểm tối đa | Ý nghĩa |
| :--- | :--- | :--- |
| **Trạng thái Shop** | 45 | Official Store hoặc Tiki Trading. |
| **Đánh giá Shop** | 35 | $\ge 4.7$ sao và $\ge 1000$ reviews. |
| **Thâm niên** | 15 | Shop hoạt động càng lâu càng được điểm cao. |
| **Lượt theo dõi** | 5 | Điểm bonus cho lượt theo dõi cao. |
| **TỔNG CỘNG** | **100** | Phản ánh uy tín được chứng thực và cam kết lâu dài của Shop. |

### 4.3. Điểm phân tích dựa trên Giá sản phẩm (Trọng số 20%)

**Mục tiêu:** Trả lời cho câu hỏi: *"Giá có hợp lý hay không so với giá chuẩn từ nhãn hàng?"*

* **Đầu vào:** Tên & Giá sản phẩm, so sánh với từ điển "Giá Chuẩn".
* **Công thức chênh lệch:** $\text{diff} = (\text{Giá hiện tại} - \text{Giá chuẩn}) / \text{Giá chuẩn}$

| Khoảng $\text{diff}$ | Mức độ | Điểm thưởng/phạt | Ý nghĩa |
| :--- | :--- | :--- | :--- |
| $\text{diff} < -0.4$ (Rẻ $>40\%$) | **Rủi ro Cực kỳ cao** | 10 điểm (Phạt nặng) | Dấu hiệu hàng giả/hàng lỗi. |
| $0.1 < \text{diff}$ (Đắt $>10\%$) | **Mua "hớ"** | 70 điểm (Phạt nhẹ) | Giá cao hơn giá chuẩn. |
| $-0.4 \le \text{diff} \le 0.1$ | **Khoảng Bình ổn/Giảm giá tốt** | 95 điểm (Thưởng cao) | Giá hợp lý hoặc đang giảm giá có kiểm soát. |
| Không tìm thấy giá chuẩn | Trung lập | 50 điểm | |

**Ý nghĩa:** Giá rẻ bất thường là dấu hiệu rủi ro lớn nhất và bị phạt nặng nhất.

## 5. HƯỚNG DẪN CÀI ĐẶT VÀ SỬ DỤNG (LOCAL)

### 5.1. Cài đặt

**Bước 1: Clone Repository**

```bash
git clone <repo-url> FINAL_PRODUCT
cd FINAL_PRODUCT
```
**Bước 2: Tạo virtual environment và kích hoạt**
```bash
python -m venv .venv
```

# Windows
```bash
.venv\Scripts\activate
```
# macOS / Linux
```bash
source .venv/bin/activate
```
**Bước 3: Cài dependencies**
```bash

pip install -r server/requirements.txt
```

**Bước 4: Đặt các file mô hình và dữ liệu:**
```bash
server/models/trust\_model.pkl

server/models/spam\_model.pkl

server/official\_prices.csv (định dạng CSV: product\_name,brand,price,source)
```

**Bước 5: Tạo file cấu hình môi trường từ mẫu (nếu có):**
```bash
cp server/config.example.json server/config.json

\# hoặc dùng .env

cp server/.env.example server/.env

Chỉnh config.json/.env để thêm API key Tiki (nếu sử dụng), đường dẫn file, cài đặt logging, v.v.
```

**Sử dụng công cụ rất đơn giản, bạn chỉ cần thực hiện 3 bước sau:**

&nbsp; Tìm kiếm Sản phẩm: Mở trang Tiki và tìm đến sản phẩm bạn muốn kiểm tra.

&nbsp; Sao chép Liên kết (Link): Sao chép toàn bộ đường dẫn URL của sản phẩm đó.

&nbsp; Dán và Phân tích:

&nbsp; Dán liên kết (Link) sản phẩm vào ô nhập liệu trên trang web của chúng tôi.

&nbsp; Nhấn nút "Phân tích" (hoặc tương đương).

Hệ thống sẽ ngay lập tức tự động thu thập thông tin, chạy các mô hình AI và hiển thị kết quả đánh giá cho bạn.



**Cấu trúc thư mục:**
```bash

FINAL\_PRODUCT/

 	.venv/					# Môi trường ảo Python

 	server/					# Thư mục Backend

 		app.py				# File server Flask

         trust\_model.pkl		# Mô hình huấn luyện AI 1

 		spam\_model.pkl		# Mô hình huấn luyện AI 2

 		official\_prices.csv		# File thư viện giá chuẩn

 		requirements.txt 		# Danh sách các thư viện cần cài đặt

 	website/				# Thư mục Frontend

 		index.html			# Giao diện trang web

 		main.js				# Xử lý giao diện
```


**Lưu ý khi huấn luyện/ thay thế mô hình:**

Mô hình hiện dùng TF-IDF + Logistic Regression (Scikit-learn). Khi huấn luyện lại, lưu kèm tfidf\_vectorizer và model (joblib hoặc pickle) vào server/models/.

Đảm bảo preprocessing trên training và inference là thống nhất.


**Thông tin liên hệ**

| Họ và Tên | Mã số sinh viên | Email (Trường) | Email (Thay thế) |
| :--- | :--- | :--- | :--- |
| Nguyễn Thị Kim Ngân | 2351050113 | 2351050113ngan@ou.edu.vn | ntkn26062005@gmail.com |
| Hồ Phạm Như Quỳnh | 2351050149 | 2351050149quynh@ou.edu.vn | quynhho2611@gmail.com |
| Nguyễn Lý Mị Nương | 2351050130 | 2351050130nuong@nuong.edu.vn | nguyenlyminuong1234567890@gmail.com |





