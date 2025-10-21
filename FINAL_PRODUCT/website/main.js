// main.js (Phiên bản "Nâng cấp Toàn diện")

const urlInput = document.getElementById("url-input");
const analyzeButton = document.getElementById("analyze-button");
const loadingEl = document.getElementById("loading");
const errorEl = document.getElementById("error");
const resultContainer = document.getElementById("result-tabs-container");

// --- CÁC HÀM TIỆN ÍCH ---
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

function setScoreCircle(elementId, score) {
    const circle = document.getElementById(elementId);
    const valueEl = document.getElementById(elementId.replace('circle', 'value'));
    if (!circle || !valueEl) return;

    valueEl.innerText = `${score}%`;
    circle.className = 'score-circle'; // Reset
    if (score >= 75) circle.classList.add("high");
    else if (score >= 40) circle.classList.add("medium");
    else circle.classList.add("low");
}

// --- CÁC HÀM "VẼ" GIAO DIỆN ---
function renderOverviewTab(data) {
    const info = data.product_info;
    document.getElementById("product-image").src = info.image_url || "https://placehold.co/180x180/e1e1e1/777?text=Image";
    document.getElementById("product-name").innerText = info.name || "N/A";

    // Xử lý giá
    const priceEl = document.getElementById("product-price");
    const originalPriceEl = document.getElementById("product-original-price");
    const discountBadgeEl = document.getElementById("product-discount-badge");

    priceEl.innerText = formatPrice(info.price);
    if (info.original_price > info.price) {
        originalPriceEl.innerText = formatPrice(info.original_price);
        const discount = Math.round(((info.original_price - info.price) / info.original_price) * 100);
        discountBadgeEl.innerText = `-${discount}%`;
        discountBadgeEl.classList.remove("hidden");
    } else {
        originalPriceEl.innerText = "";
        discountBadgeEl.classList.add("hidden");
    }

    document.getElementById("product-seller").innerText = info.seller_name || "N/A";
    document.getElementById("product-sold").innerText = info.sold_count > 0 ? info.sold_count.toLocaleString('vi-VN') : "N/A";
    document.getElementById("product-reviews").innerText = info.review_count > 0 ? `${info.review_count.toLocaleString('vi-VN')} (${info.rating_average.toFixed(1)}⭐)` : "N/A";
    document.getElementById("final-summary").innerText = data.final_summary || "";
    setScoreCircle("final-score-circle", data.final_score);
}

function renderReviewTab(data) {
    const analysis = data.review_analysis;
    setScoreCircle("review-score-circle", analysis.score);
    document.getElementById("review-summary").innerText = analysis.summary || "";

    const posList = document.getElementById("positive-reviews-list");
    posList.innerHTML = "";
    if (analysis.positive_reviews && analysis.positive_reviews.length > 0) {
        analysis.positive_reviews.forEach(text => {
            const li = document.createElement("li");
            li.textContent = text.substring(0, 100) + "...";
            posList.appendChild(li);
        });
    } else {
        posList.innerHTML = "<li>Không có review tích cực nổi bật.</li>";
    }

    const negList = document.getElementById("negative-reviews-list");
    negList.innerHTML = "";
    if (analysis.negative_reviews && analysis.negative_reviews.length > 0) {
        analysis.negative_reviews.forEach(text => {
            const li = document.createElement("li");
            li.textContent = text.substring(0, 100) + "...";
            negList.appendChild(li);
        });
    } else {
        negList.innerHTML = "<li>Không tìm thấy review tiêu cực.</li>";
    }
}

function renderPriceTab(data) {
    const analysis = data.price_analysis;
    const info = data.product_info;
    setScoreCircle("price-score-circle", analysis.score);
    document.getElementById("price-summary").innerText = analysis.summary || "";

    document.getElementById("current-price-value").innerText = formatPrice(info.price);
    document.getElementById("official-price-value").innerText = analysis.official_price ? formatPrice(analysis.official_price) : "N/A";

    const diffEl = document.getElementById("price-difference-value");
    if (analysis.difference !== null) {
        const diffPercent = (analysis.difference * 100).toFixed(0);
        diffEl.innerText = `${diffPercent > 0 ? '+' : ''}${diffPercent}%`;
        diffEl.className = 'value'; // Reset
        if (analysis.difference < -0.2) diffEl.classList.add('low-text');
        else if (analysis.difference > 0.1) diffEl.classList.add('medium-text');
        else diffEl.classList.add('high-text');
    } else {
        diffEl.innerText = "N/A";
    }
}

// --- HÀM CHÍNH ---
analyzeButton.addEventListener("click", async () => {
    const url = urlInput.value;
    if (!url || !url.includes("tiki.vn")) {
        showError("Vui lòng dán link sản phẩm Tiki hợp lệ.");
        return;
    }

    // 1. Chuẩn bị UI
    analyzeButton.disabled = true;
    analyzeButton.innerText = "Đang phân tích...";
    loadingEl.classList.remove("hidden");
    errorEl.classList.add("hidden");
    resultContainer.classList.add("hidden");

    try {
        // 2. GỌI "BỘ NÃO" app.py
        const response = await fetch("http://127.0.0.1:5000/analyze_url", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ url: url }),
        });
        const data = await response.json();
        if (!response.ok) {
            showError(data.error || "Lỗi không xác định từ server.");
            return;
        }

        // 3. "VẼ" GIAO DIỆN VỚI DATA NHẬN VỀ
        renderOverviewTab(data);
        renderReviewTab(data);
        renderPriceTab(data);

        // 4. HIỂN THỊ KẾT QUẢ
        loadingEl.classList.add("hidden");
        resultContainer.classList.remove("hidden");

    } catch (err) {
        showError("Lỗi kết nối: Server 'app.py' chưa chạy?");
        console.error(err);
    } finally {
        analyzeButton.disabled = false;
        analyzeButton.innerText = "Phân tích";
    }
});

// --- LOGIC CHUYỂN TAB ---
document.querySelectorAll('.tab-button').forEach(button => {
    button.addEventListener('click', () => {
        const tabName = button.dataset.tab;
        document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
        button.classList.add('active');
        document.getElementById(tabName).classList.add('active');
    });
});

