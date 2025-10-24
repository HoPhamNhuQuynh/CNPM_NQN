// main.js (Phiên bản Tạm thời Tắt Modal)








const urlInput = document.getElementById("url-input");
const analyzeButton = document.getElementById("analyze-button");
const loadingEl = document.getElementById("loading");
const errorEl = document.getElementById("error");
const resultContainer = document.getElementById("result-tabs-container");






// Biến lưu trữ biểu đồ
let starChartInstance = null;
let aiChartInstance = null;








// --- HÀM TIỆN ÍCH ---
function showError(message) {
 loadingEl.classList.add("hidden");
 resultContainer.classList.add("hidden");
 errorEl.innerText = message;
 errorEl.classList.remove("hidden");
 analyzeButton.disabled = false;
 analyzeButton.innerText = "Phân tích";
}








function formatPrice(price) {
 return price > 0 ? price.toLocaleString('vi-VN') + ' ₫' : "N/A";
}








function formatBigNumber(num) {
 if (num === null || num === undefined || num === "N/A") return "N/A";
 const number = parseInt(num);
  if (isNaN(number)) return "N/A";
 if (number >= 1000000) return (number / 1000000).toFixed(1) + ' Tr';
 if (number >= 1000) return (number / 1000).toFixed(0) + ' K';
 return number.toString();
}








function setScoreCircle(elementId, score) {
 const circle = document.getElementById(elementId);
 const valueEl = document.getElementById(elementId.replace('circle', 'value'));
 if (!circle || !valueEl) return;
 const numericScore = parseInt(score);
 if (isNaN(numericScore)) {
     valueEl.innerText = '--';
     circle.className = 'score-circle medium'; return;
 }
 valueEl.innerText = `${numericScore}%`;
 circle.className = 'score-circle';
 if (numericScore >= 70) circle.classList.add("high");
 else if (numericScore >= 40) circle.classList.add("medium");
 else circle.classList.add("low");
}




// --- HÀM RENDER ẢNH FEEDBACK (Đã bỏ sự kiện click modal) ---
function renderFeedbackImages(urls) {
  const grid = document.getElementById('feedback-images-grid');
  if (!grid) { console.warn("Không tìm thấy div 'feedback-images-grid'"); return; }




  grid.innerHTML = ''; // Clear contents




  // --- BƯỚC LỌC ẢNH KHÔNG PHÙ HỢP ---
  // Vì không có AI, thực hiện một heuristic đơn giản:
  // 1. Tạm thời BỎ qua 5 ảnh đầu tiên (thường là ảnh rác/người)
  // 2. Giữ lại tối đa 10 ảnh sau khi lọc




  const allUrls = urls || [];
  // Lấy tất cả ảnh từ vị trí thứ 5 (index 5) trở đi.
  let filteredUrls = allUrls.slice(5);




  // Nếu không đủ ảnh sau khi lọc 5 cái đầu, ta lấy lại ảnh cuối cùng (phòng trường hợp chỉ có ít ảnh)
  if (filteredUrls.length === 0 && allUrls.length > 0) {
      // Giữ lại 2 ảnh cuối cùng nếu chỉ có ít ảnh
      filteredUrls = allUrls.slice(Math.max(0, allUrls.length - 2));
  }




  if (filteredUrls.length === 0) {
      grid.innerHTML = '<p id="no-images-message" style="color: #6c757d; font-style: italic;">Không tìm thấy ảnh feedback nào.</p>';
      return;
  }




  // Chỉ hiển thị tối đa 10 ảnh sau khi lọc
  const imagesToDisplay = filteredUrls.slice(0, 10);




  imagesToDisplay.forEach(url => {
      const img = document.createElement('img');
      img.src = url;
      img.className = 'feedback-image-item';
      img.alt = 'Ảnh feedback sản phẩm';
      // Tạm thời bỏ sự kiện click để phóng to (theo yêu cầu)
      // img.addEventListener('click', () => openModal(url));
      grid.appendChild(img);
  });
}
// ---------------------------------------------






// --- HÀM RENDER ---
function renderOverviewTab(data) {
 try {
     const info = data.product_info;
     if (!info) throw new Error("product_info không tồn tại");
     document.getElementById("product-image").src = info.image_url || "https://placehold.co/180x180/e1e1e1/777?text=Image";
     document.getElementById("product-name").innerText = info.name || "N/A";
     const priceEl = document.getElementById("product-price"), originalPriceEl = document.getElementById("product-original-price"), discountBadgeEl = document.getElementById("product-discount-badge");
     priceEl.innerText = formatPrice(info.price);
     if (info.original_price > info.price) {
         originalPriceEl.innerText = formatPrice(info.original_price);
         const discount = Math.round(((info.original_price - info.price) / info.original_price) * 100);
         discountBadgeEl.innerText = `-${discount}%`; discountBadgeEl.classList.remove("hidden");
     } else { originalPriceEl.innerText = ""; discountBadgeEl.classList.add("hidden"); }
     document.getElementById("product-seller").innerText = info.seller_name_widget || info.seller_name || "N/A";
     const officialBadge = document.getElementById("official-badge");
     if (info.is_official_store) { officialBadge.classList.remove("hidden"); } else { officialBadge.classList.add("hidden"); }
     document.getElementById("seller-rating").innerText = info.seller_rating > 0 ? `${info.seller_rating.toFixed(1)}/5★` : "N/A";
     document.getElementById("seller-joined").innerText = info.date_joined || "N/A";
     document.getElementById("seller-followers").innerText = formatBigNumber(info.follower_count);
     document.getElementById("product-sold").innerText = info.sold_count > 0 ? formatBigNumber(info.sold_count) : "N/A";
     document.getElementById("product-reviews").innerText = info.review_count > 0 ? `${formatBigNumber(info.review_count)} (${info.rating_average ? info.rating_average.toFixed(1) : 'N/A'}⭐)` : "N/A";
     document.getElementById("final-summary").innerText = data.final_summary || "";
     setScoreCircle("final-score-circle", data.final_score);
 } catch (e) { console.error("Lỗi renderOverviewTab:", e); throw new Error("Lỗi renderOverviewTab"); }
}








function renderReviewTab(data) {
 try {
     const analysis = data.review_analysis;
     if (!analysis) throw new Error("review_analysis không tồn tại");
     setScoreCircle("review-score-circle", analysis.score);
     document.getElementById("review-summary").innerText = analysis.summary || "";








     // Lists
     const posList = document.getElementById("positive-reviews-list"), negList = document.getElementById("negative-reviews-list");
     posList.innerHTML = negList.innerHTML = ""; // Clear lists
     const renderList = (listEl, reviews, defaultText) => {
         const validReviews = reviews ? reviews.filter(t => t && t.trim().length > 0).slice(0, 3) : []; // Lấy 3 review
         if (validReviews.length > 0) {
             validReviews.forEach(text => {
                 const li = document.createElement("li");
                 li.textContent = text.substring(0, 150) + "..."; // Giới hạn ký tự
                 listEl.appendChild(li);
             });
         } else { listEl.innerHTML = `<li>${defaultText}</li>`; }
     };
     renderList(posList, analysis.positive_reviews, "Không có review tích cực nổi bật.");
     renderList(negList, analysis.negative_reviews, "Không tìm thấy review tiêu cực.");




     // === BỔ SUNG: RENDER ẢNH FEEDBACK ===
     renderFeedbackImages(data.product_info.review_image_urls);








     // Star Chart
     if (starChartInstance) starChartInstance.destroy();
     const starCtx = document.getElementById('star-chart');
     if (typeof Chart !== 'undefined' && analysis.star_distribution && starCtx) {
         starChartInstance = new Chart(starCtx.getContext('2d'), {
             type: 'bar', data: { labels: ['5★', '4★', '3★', '2★', '1★'], datasets: [{ label: 'Số lượng', data: [analysis.star_distribution['5']||0, analysis.star_distribution['4']||0, analysis.star_distribution['3']||0, analysis.star_distribution['2']||0, analysis.star_distribution['1']||0], backgroundColor: ['#4CAF50', '#8BC34A', '#FFEB3B', '#FF9800', '#F44336'] }] },
             options: { indexAxis: 'y', scales: { x: { beginAtZero: true, ticks: { precision: 0 } } }, plugins: { legend: { display: false } } }
         });
     } else { console.warn("Star chart canvas/data missing or Chart.js not loaded."); }








     // AI Chart
     if (aiChartInstance) aiChartInstance.destroy();
     const aiCtx = document.getElementById('ai-chart');
     if (typeof Chart !== 'undefined' && analysis.ai_analysis && (analysis.ai_analysis.real >= 0 && analysis.ai_analysis.spam >= 0) && aiCtx) {
         aiChartInstance = new Chart(aiCtx.getContext('2d'), {
             type: 'doughnut', data: { labels: ['Review Thật', 'Review Spam/Seeding'], datasets: [{ data: [analysis.ai_analysis.real, analysis.ai_analysis.spam], backgroundColor: ['#007bff', '#DC3545'] }] },
             options: { responsive: true, plugins: { legend: { position: 'top' } } }
         });
     } else { console.warn("AI chart canvas/data missing or Chart.js not loaded."); }








     // Word Cloud


 } catch (e) { console.error("Lỗi renderReviewTab:", e); throw new Error(`Lỗi renderReviewTab: ${e.message}`); }
}








function renderSellerTab(data) {
 try {
     const analysis = data.seller_analysis;
     const info = data.product_info;
     if (!analysis || !info) throw new Error("seller_analysis hoặc product_info không tồn tại");








     setScoreCircle("seller-score-circle", analysis.score);
     document.getElementById("seller-overall-summary").innerText = analysis.summary || "Chưa có đánh giá tổng quan.";








     const setMetric = (id, text, cssClass) => {
         const el = document.getElementById(id);
         if(el) {
             el.innerText = text || "--";
             el.className = 'value';
             if (cssClass && cssClass !== 'info') {
                 el.classList.add(cssClass);
             }
         } else {
              console.warn(`Element with ID ${id} not found.`);
         }
     };








     setMetric("seller-status", analysis.status_text, analysis.status_class);
     setMetric("seller-rating-detail", analysis.rating_text, analysis.rating_class);
     setMetric("seller-seniority", analysis.seniority_text, analysis.seniority_class);
     setMetric("seller-followers-detail", analysis.followers_text, analysis.followers_class);








 } catch (e) { console.error("Lỗi renderSellerTab:", e); throw new Error(`Lỗi renderSellerTab: ${e.message}`); }
}




function renderPriceTab(data) {
   try {
       const analysis = data.price_analysis; // Lấy kết quả phân tích giá
       const info = data.product_info; // Lấy thông tin sản phẩm (chứa giá Tiki)
       if (!analysis || !info) throw new Error("price_analysis hoặc product_info không tồn tại");


       // 1. Hiển thị điểm giá và tóm tắt
       setScoreCircle("price-score-circle", analysis.score);
       document.getElementById("price-summary").innerText = analysis.summary || "Chưa có nhận xét giá.";


       // 2. Hiển thị link đề xuất (nếu có)
       const suggestionEl = document.getElementById("price-suggestion");
       const suggestionTextEl = document.getElementById("suggestion-text");
       const suggestionLinkEl = document.getElementById("suggestion-link");


       // Kiểm tra xem suggestion có tồn tại và có link không
       if (analysis.suggestion && analysis.suggestion.link && suggestionEl && suggestionTextEl && suggestionLinkEl) {
           suggestionTextEl.innerText = analysis.suggestion.text || "Giá Tiki cao hơn, tham khảo link sau: ";
           suggestionLinkEl.href = analysis.suggestion.link;
           suggestionEl.classList.remove("hidden"); // Hiện ô đề xuất
       } else if (suggestionEl) {
           suggestionEl.classList.add("hidden"); // Ẩn ô đề xuất nếu không có
       }


       // 3. Hiển thị giá hiện tại, giá chuẩn, chênh lệch
       const currentPrice = info.price;
       const officialPrice = analysis.official_price;


       document.getElementById("current-price-value").innerText = formatPrice(currentPrice);
       document.getElementById("official-price-value").innerText = officialPrice ? formatPrice(officialPrice) : "N/A";


       const diffEl = document.getElementById("price-difference-value");


       // 4. Hiển thị thanh so sánh giá (Price Bar)
       const priceBar = document.getElementById("price-bar-current");
       const priceBarLabel = document.getElementById("price-bar-label");
       const priceBarContainer = priceBar ? priceBar.parentElement : null;


       if(priceBarContainer) priceBarContainer.classList.add('hidden'); // Ẩn thanh bar mặc định


       // Chỉ tính toán và hiển thị nếu có đủ thông tin giá
       if (analysis.difference !== null && isFinite(analysis.difference) && officialPrice > 0 && currentPrice > 0) {
           const diffPercent = (analysis.difference * 100);
           diffEl.innerText = `${diffPercent > 0 ? '+' : ''}${diffPercent.toFixed(0)}%`; // Hiển thị % chênh lệch
           diffEl.className = 'value'; // Reset class màu


           const ratio = Math.min(200, Math.max(0, (currentPrice / officialPrice) * 100)); // Tính tỉ lệ giá, giới hạn 0-200%
           if(priceBar) priceBar.style.width = `${ratio.toFixed(1)}%`; // Cập nhật độ dài thanh bar


           // Xác định màu sắc và nhãn cho thanh bar dựa trên điểm giá
           let barColor = 'var(--primary-color)'; // Màu mặc định (Hợp lý)
           let barLabelText = `Giá hiện tại = ${ratio.toFixed(0)}% giá chuẩn - Hợp lý.`;
           diffEl.classList.remove('low-text', 'high-text', 'medium-text'); // Xóa class màu cũ của % chênh lệch


           if (analysis.score <= 10) { // Rẻ bất thường
               diffEl.classList.add('low-text');
               barColor = 'var(--danger-color)';
               barLabelText = `Giá hiện tại chỉ bằng ${ratio.toFixed(0)}% giá chuẩn - Rất rẻ!`;
           } else if (analysis.score >= 95) { // Giá tốt (Sale)
               diffEl.classList.add('high-text');
               barColor = 'var(--success-color)';
                barLabelText = `Giá hiện tại bằng ${ratio.toFixed(0)}% giá chuẩn - Giá tốt!`;
           } else if (analysis.score === 70) { // Giá cao
               diffEl.classList.add('medium-text');
               barColor = 'var(--warning-color)';
                barLabelText = `Giá hiện tại bằng ${ratio.toFixed(0)}% giá chuẩn - Cao hơn!`;
            } // Trường hợp score = 90 (Hợp lý) giữ nguyên màu xanh primary


            if(priceBar) priceBar.style.backgroundColor = barColor; // Cập nhật màu thanh bar
            if(priceBarLabel) priceBarLabel.innerText = barLabelText; // Cập nhật nhãn thanh bar
            if(priceBarContainer) priceBarContainer.classList.remove('hidden'); // Hiện thanh bar


       } else { // Trường hợp không đủ thông tin để so sánh
           diffEl.innerText = "N/A";
           diffEl.className = 'value';
           if(priceBar) priceBar.style.width = '0%'; // Reset thanh bar
           if(priceBarLabel) priceBarLabel.innerText = "Không thể so sánh giá.";
           // Container đã bị ẩn ở đầu rồi
       }
   } catch (e) { // Xử lý lỗi nếu có
       console.error("Lỗi khi render Tab Giá:", e);
       // Ẩn các phần tử có thể gây lỗi giao diện
       const priceBarContainer = document.querySelector('.price-bar-container');
       if (priceBarContainer) priceBarContainer.classList.add('hidden');
        const suggestionEl = document.getElementById("price-suggestion");
        if (suggestionEl) suggestionEl.classList.add('hidden');
       throw new Error("Lỗi renderPriceTab"); // Ném lỗi để hàm gọi biết
   }
}


// --- HÀM CHÍNH ---
analyzeButton.addEventListener("click", async () => {
 const url = urlInput.value;
 if (!url || !url.includes("tiki.vn")) { showError("Vui lòng dán link sản phẩm Tiki hợp lệ."); return; }
 analyzeButton.disabled = true; analyzeButton.innerText = "Đang phân tích...";
 loadingEl.classList.remove("hidden"); errorEl.classList.add("hidden"); resultContainer.classList.add("hidden");
 try {
     const response = await fetch("http://127.0.0.1:5000/analyze_url", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ url: url }), });
     if (!response.ok) {
         const errorText = await response.text(); console.error("Server trả về lỗi:", response.status, errorText);
         try { const errorData = JSON.parse(errorText); showError(errorData.error || `Lỗi server ${response.status}`); } catch (e) { showError(`Lỗi server ${response.status}. Chi tiết lỗi không phải JSON.`); } return;
     }
     const data = await response.json();
     try {
         renderOverviewTab(data);
         renderReviewTab(data);
         renderSellerTab(data);
         renderPriceTab(data);
     } catch (renderError) { console.error("LỖI RENDER GIAO DIỆN:", renderError); showError(`Lỗi JavaScript khi hiển thị: ${renderError.message}. Kiểm tra Console F12.`); return; }
     loadingEl.classList.add("hidden"); resultContainer.classList.remove("hidden");
 } catch (err) { showError("Lỗi kết nối: Server 'app.py' chưa chạy?"); console.error("Lỗi fetch() hoặc lỗi JSON:", err);
 } finally { analyzeButton.disabled = false; analyzeButton.innerText = "Phân tích"; }
});








// --- LOGIC CHUYỂN TAB ---
document.querySelectorAll('.tab-button').forEach(button => {
 button.addEventListener('click', () => {
     const tabName = button.dataset.tab;
     document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
     document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
     button.classList.add('active');
     const tabElement = document.getElementById(tabName);
     if (tabElement) { tabElement.classList.add('active'); } else { console.error(`Không tìm thấy tab content ID: ${tabName}`); }
 });
});
