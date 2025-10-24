# **DỰ ÁN: WEBSITE HỖ TRỢ ĐÁNH GIÁ ĐỘ TIN CẬY CỦA SẢN PHẨM TRÊN TIKI**



##### **Nhóm thực hiện:**

\- Tên nhóm: NQN

1. Nguyễn Thị Kim Ngân - 2351050113
2. Hồ Phạm Như Quỳnh - 2351050149
3. Nguyễn Lý Mị Nương - 2351050130



1. **Giới thiệu chung:**
   Đây là một dự án xây dựng một ứng dụng web có sử dụng trí tuệ nhân tạo để phân tích và đánh giá sản phẩm trên sàn thương mại điện tử, cụ thể là Tiki, nhằm hỗ trợ người dùng đưa ra quyết định mua sắm thông minh và mua được hàng có chất lượng hơn.
   Vấn đề:
   	Hiện nay, mua sắm trực tuyến đang dần trở thành một xu hướng chung của mọi người trong đời sống hiện đại, nhất là khi nhu cầu “nhanh, tiện lợi” được đặt lên trên hàng đầu.
   Tuy nhiên, cùng với sự phát triển mạnh mẽ của các sàn thương mại điện tử thì người tiêu dùng lại phải đối mặt với một vấn đề vô cùng nan giải: rất khó để phân biệt giữa hàng thật và hàng giả.
   Phần lớn họ thường phải dựa vào các thông tin nhiễu như hình ảnh quảng cáo đã được chỉnh sửa, các đánh giá “seeding” và review ảo nhằm thao túng niềm tin của khách hàng, dẫn đến tình trạng mua phải sản phẩm kém chất lượng và gây trực tiếp đến trải nghiệm mua sắm của người dùng.
   
2. **Tổng quan giải pháp:**

* Ngày nay, việc lựa chọn sản phẩm trên các sàn thương mại điện tử vẫn còn là thách thức đối với nhiều người dùng. Không ít trường hợp mua phải hàng kém chất lượng do bị ảnh hưởng bởi các đánh giá thiếu trung thực hoặc nội dung quảng cáo được “tô hồng” quá mức. Điều này khiến người tiêu dùng khó đưa ra quyết định chính xác.

Để giải quyết vấn đề đó, dự án này cung cấp một công cụ tích hợp AI giúp phân tích nội dung mô tả và đánh giá sản phẩm, từ đó đưa ra chỉ số phần trăm độ tin cậy một cách khách quan. Hệ thống tự động thu thập dữ liệu thông qua liên kết sản phẩm do người dùng cung cấp, xử lý và đánh giá dựa trên nhiều tiêu chí như mô tả sản phẩm, mức giá, cũng như nội dung đánh giá từ khách hàng.

Bằng cách áp dụng mô hình AI đã được huấn luyện trên bộ dữ liệu chuyên biệt và tinh chỉnh qua nhiều giai đoạn, công cụ giúp tiết kiệm thời gian đánh giá thủ công, đồng thời nâng cao độ chính xác khi đưa ra quyết định mua sắm.



* Như vậy, dự án cung cấp công cụ hệ thống website hỗ trợ:

&nbsp;	- Lấy dữ liệu sản phẩm từ link sản phẩm người dùng cung cấp qua giao diện trên website

&nbsp;	- Phân tích sản phẩm từ các dữ liệu lấy được, tập trung vào phân tích đánh giá của người mua - thông qua mô hình huấn luyện AI và Machine Learning, độ chênh lệch giá - dựa vào việc so sánh mức giá hiện có với mức giá chuẩn trên thị trường của cùng dòng sản phẩm đến từ các nhãn hàng uy tín. Từ đó, kết hợp với thuật toán đánh giá, đưa về kết quả là mức độ tin cậy của sản phẩm.

Kiến trúc hệ thống: Dự án được xây dựng theo kiến trúc Client - Server

5.1. Frontend: Một trang web với giao diện tối giản, dễ nhìn, dễ sử dụng được xây dựng bằng HTML, CSS và JavaScript ( đặt trong thư mục website/)

5.2. Backend: Một server được phát triển bằng Python Flask ( đặt trong thư mục server). Đây là nơi trung tâm thực hiện tất cả các tác vụ nặng của hệ thống:

5.2.1. Gọi API Tiki để lấy dữ liệu

5.2.2. Tải và chạy 2 model AI đã được train ( theo mô hinh gì….)

5.2.3. Đọc từ điển “giá chuẩn”

5.2.4. Tính toán điểm số theo thuật toán và trả về kết quả cuối cùng

5.3. Mô hình Trí tuệ nhân tạo (AI)

5.3.1. Mô hình trust\_model.pkl: Đây là mô hình AI được huấn luyện để dự đoán một review có dấu hiệu của sản phẩm “Có đáng tin cậy hay không?”

5.3.2. Mô hình spam\_model.pkl: Đây là mô hình AI được huấn luyện để dự đoán một review “Có phải là review rác hay không?”

5.3.3 Thuật toán: Cả hai mô hình AI trên đều sử dụng thuật toán từ thư viện Scikit-learn

\- TF-IDF

\- Logistic Regression

Logic chấm điểm của hệ thống:

Final Score - Điểm tổng hợp: Đây là điểm số quan trọng nhất, được tính bằng công thức trung bình có trọng số:

final\_score =  int(review\_analysis\[“score”] \* 0.7 + price\_analysis\[“score”])

Trong đó:

70% trọng số đến từ Điểm phân tích dựa trên Review ( review\_analysis\[“score”])

30% trọng số đến từ Điểm phân tích Giá sản phẩm (price\_analysis\[“score”])



6.1. Điểm phân tích dựa trên review( Chiếm 50%)

Mục tiêu: Trả lời cho câu hỏi “Các review này có thật không và có đáng tin cậy không?”

Đầu vào: Hệ thống lấy tối đa 100 reviews làm mẫu thử và làm sạch, xử lý dữ liệu ( xoá HTML, chuẩn hóa văn bản)

Chạy 2 mô hình AI:

 	trust\_model.predict():

Mục tiêu: xác định mức độ hài lòng hay không hài lòng của khách hàng đối với sản phẩm, chiếm tổng điểm lớn nhất là 60% vì nó phản ánh trực tiếp đến chất lượng và cảm nhận của khách hàng.

Cơ chế: Mô hình này dự đoán xem review có “đáng tin” không. Trả về kết quả: hoặc 1 ( không đáng tin) hoặc 0 ( đáng tin)



spam\_model.predict():

Mục tiêu: Đảm bảo tính xác thực và độ tin cậy của nội dung review nhằm lọc các đánh giá giả mạo, spam, hoặc quảng cáo, qua đó giúp nâng cao chất lượng của review và uy tín của hệ thống.

Cơ chế: Mô hình này dự đoán mức độ spam/seeding của review. Kết quả trả về một điểm trong khoảng từ 0  3 ( với 0 = không spam, 3 = độ spam cao)



Tính điểm thành phần:

 		trust\_score\_part: 20%

spam\_score\_part: 80%

Tổng hợp điểm Review:

Điểm Review = trust\_score\_part + spam\_score\_part

6.2. Điểm phân tích dựa trên hành vi người bán( Chiếm 30%)

Mục tiêu: Trả lời cho câu hỏi “Shop này có thực sự uy tín hay không?”. Đánh giá mức độ đáng tin cậy và chất lượng của shop.

Đầu vào: Hệ thống lấy thông tin của người bán gồm rating, follower, is\_official và ngày tạo tài khoản của shop.

Cách tính điểm:

Trạng thái shop: Nếu là Official Store hoặc Tiki Trading(45)

Đánh giá shop: Yêu cầu >= 4.7 sao và >= 1000 reviews để đạt điểm tối đa(35)

Thâm niên: Điểm càng tăng đối với các shop có thâm niên càng cao(15)

Lượt theo dõi: Điểm bonus cho các shop có lượt theo dõi cao(5)

 	Tổng điểm tối đa: 45 + 35 + 15 + 5 = 100 điểm.

Ý nghĩa: Phần điểm này chiếm trọng số lớn (30%), phản ánh uy tín được chứng thực và cam kết lâu dài của Shop. Điểm cao cho thấy Shop đã vượt qua các tiêu chuẩn về tính xác thực và được cộng đồng người dùng đánh giá cao, giảm thiểu rủi ro mua hàng cho khách hàng.

6.3. Điểm phân tích dựa trên Giá sản phẩm( Chiếm 20%)

Mục tiêu: Trả lời cho câu hỏi “Giá bạn này có hợp lý hay không? Có chênh lệch quá  nhiều hay không so với giá chuẩn từ nhãn hàng?”.  Đánh giá mức độ tin cậy dựa vào khoảng cách dao động giá và sẽ đưa ra đề xuất giúp khách hàng nhận được mức ưu đãi tốt hơn và đáng tin cậy hơn, tập trung vào trường hợp giá sản phẩm cao hơn giá dữ liệu gốc.

 Đầu vào: Hệ thống lấy tên và giá sản phẩm trên Tiki, sau đó tìm trong từ điển “giá chuẩn” để xem giá niêm yết.

Trường hợp 1: Không tìm thấy giá chuẩn: trả về điểm trung lập 50

Trường hợp 2: Tìm thấy giá chuẩn: hệ thống tiến hành tính toán chênh lệch phần trăm:

diff = ( Giá hiện tại - Giá chuẩn)/ Giá chuẩn

Với diff < -0.4 ( Rẻ hơn 40% so với giá chuẩn)

Đây là dấu hiệu cực kỳ đáng nhờ ( nguy cơ hàng giả, hàng lỗi cao)

Điểm bị phạt nặng: chỉ được 10 điểm

 		Với diff > 0.1 ( Đắt hơn 10% so với giá chuẩn)

Người dùng đang bị mua “hớ”

Điểm bị phạt nhẹ: được 70 điểm

Với -0.4 <= diff <= 0.1 ( Khoảng bình ổn)

Đây là giá hợp ký hoặc đang được giảm giá tốt

Điểm thưởng cao: 95 điểm



Ý nghĩa: Điểm Giá không phải “càng rẻ càng tốt”, mà là “càng hợp lý càng tốt”. Giá rẻ một cách bất thường bị coi là một dấu hiệu rủi ro lớn nhất và bị phạt nặng nhất về điểm số.



Hướng dẫn chạy và cài đặt:

Cài đặt nhanh (Local)

Bước 1: Clone repo:

git clone <repo-url> FINAL\_PRODUCT

cd FINAL\_PRODUCT

Bước 2: Tạo virtual environment và kích hoạt:

python -m venv .venv

\# Windows

.venv\\Scripts\\activate

\# macOS / Linux

source .venv/bin/activate

Bước 3: Cài dependencies:

pip install -r server/requirements.txt

Bước 4: Đặt các file mô hình và dữ liệu:

server/models/trust\_model.pkl

server/models/spam\_model.pkl

server/official\_prices.csv (định dạng CSV: product\_name,brand,price,source)





Bước 5: Tạo file cấu hình môi trường từ mẫu (nếu có):

cp server/config.example.json server/config.json

\# hoặc dùng .env

cp server/.env.example server/.env

Chỉnh config.json/.env để thêm API key Tiki (nếu sử dụng), đường dẫn file, cài đặt logging, v.v.



Sử dụng công cụ rất đơn giản, bạn chỉ cần thực hiện 3 bước sau:

Tìm kiếm Sản phẩm: Mở trang Tiki và tìm đến sản phẩm bạn muốn kiểm tra.

Sao chép Liên kết (Link): Sao chép toàn bộ đường dẫn URL của sản phẩm đó.

Dán và Phân tích:

Dán liên kết (Link) sản phẩm vào ô nhập liệu trên trang web của chúng tôi.

Nhấn nút "Phân tích" (hoặc tương đương).

Hệ thống sẽ ngay lập tức tự động thu thập thông tin, chạy các mô hình AI và hiển thị kết quả đánh giá cho bạn.

Cấu trúc thư mục:

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



Lưu ý khi huấn luyện/ thay thế mô hình:

Mô hình hiện dùng TF-IDF + Logistic Regression (Scikit-learn). Khi huấn luyện lại, lưu kèm tfidf\_vectorizer và model (joblib hoặc pickle) vào server/models/.

Đảm bảo preprocessing trên training và inference là thống nhất.

Thông tin liên hệ:

Họ và tên

Email

Email thay thế

Nguyễn Thị Kim Ngân

2351050113ngan@ou.edu.vn

ntkn26062005@gmail.com

Hồ Phạm Như Quỳnh

2351050149quynh@ou.edu.vn

quynhho2611@gmail.com

Nguyễn Lý Mị Nương

2351050130nuong@nuong.edu.vn

nguyenlyminuong1234567890@gmail.com

