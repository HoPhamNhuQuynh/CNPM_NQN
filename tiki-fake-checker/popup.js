const btn = document.getElementById("checkBtn");
const card = document.getElementById("card");
const raw = document.getElementById("raw");
const noteEl = document.getElementById("p_note");

function showCard() { card.classList.remove("hidden"); raw.classList.add("hidden"); }
function showRaw(text) { raw.textContent = text; raw.classList.remove("hidden"); card.classList.add("hidden"); }
function resetBtn() { btn.disabled = false; btn.textContent = "Phân tích sản phẩm"; }

btn.addEventListener("click", () => {
    btn.disabled = true;
    btn.textContent = "Đang phân tích...";
    noteEl.textContent = "Đang lấy dữ liệu từ trang...";

    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        const tab = tabs[0];
        if (!tab) { noteEl.textContent = "Không tìm thấy tab."; resetBtn(); return; }

        chrome.tabs.sendMessage(tab.id, { action: "extract" }, (basicInfo) => {
            if (!basicInfo) { noteEl.textContent = "Không nhận được phản hồi từ content script."; resetBtn(); return; }

            // hiển thị ngay thông tin cơ bản
            document.getElementById("p_name").textContent = basicInfo.title || "—";
            document.getElementById("p_price").textContent = basicInfo.price || "—";
            document.getElementById("p_seller").textContent = basicInfo.seller || "—";
            showCard();

            const productId = basicInfo.productId;
            if (!productId) { noteEl.textContent = "Không tìm thấy productId."; resetBtn(); return; }

            // gọi background fetch
            chrome.runtime.sendMessage({ action: "fetchProductAPI", productId }, (response) => {
                resetBtn();

                if (!response) { noteEl.textContent = "Không nhận được dữ liệu từ background."; return; }
                if (response.error) { noteEl.textContent = "Lỗi fetch: " + response.error; showRaw(JSON.stringify(response, null, 2)); return; }

                const product = response.product || {};
                const reviews = response.reviews || {};

                // fill các thông tin sản phẩm
                document.getElementById("p_name").textContent = product.name || basicInfo.title || "—";
                const priceDisplay = (product.price && product.price>0) ? (product.price.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".")+"₫") : (basicInfo.price||"—");
                document.getElementById("p_price").textContent = priceDisplay;

                // seller
                let sellerName = "—";
                if(product && product.seller && product.seller.name) sellerName = product.seller.name;
                else if(basicInfo.seller) sellerName = basicInfo.seller;
                document.getElementById("p_seller").textContent = sellerName;

                // official
                let auth = "Không rõ";
                if(product && typeof product.is_authorized !== "undefined") auth = product.is_authorized ? "Có" : "Không";
                else if(product && product.seller && product.seller.is_official) auth = product.seller.is_official ? "Có" : "Không";
                document.getElementById("p_official").textContent = auth;

                // brand
                document.getElementById("p_brand").textContent = (product.brand && product.brand.name) ? product.brand.name : "—";

                // rating & review count
                const rating = product.rating_average || product.customer_review_average || "—";
                const reviewCount = product.review_count || product.rating_count || ((reviews.meta && reviews.meta.total)?reviews.meta.total:"—");
                document.getElementById("p_rating").textContent = rating;
                document.getElementById("p_review_count").textContent = reviewCount;

                // count review images
                let reviewImageCount = 0;
                const arr = (reviews.data || reviews.results || reviews.items) || [];
                for (const r of arr){
                    if(r && (r.images || r.rating_images || r.media)){
                        const imgs = r.images || r.rating_images || r.media;
                        reviewImageCount += Array.isArray(imgs)? imgs.length : 1;
                    }
                }
                document.getElementById("p_review_images").textContent = reviewImageCount;

                // product url
                chrome.tabs.query({active:true,currentWindow:true}, tabs2=>{
                    document.getElementById("p_url").textContent = tabs2[0]?tabs2[0].url:"—";
                });

                // Hiển thị review trong popup
const reviewsDiv = document.getElementById("p_reviews");
reviewsDiv.innerHTML = ""; // reset
if(response.reviews && response.reviews.data && response.reviews.data.length > 0){
    response.reviews.data.forEach(r => {
        const div = document.createElement("div");
        div.style.borderBottom = "1px solid #eee";
        div.style.marginBottom = "5px";
        div.style.paddingBottom = "3px";
        div.innerHTML = `
            <div><strong>⭐ ${r.rating || "—"}</strong> - ${r.created_at || ""}</div>
            <div>${r.content || ""}</div>
        `;
        reviewsDiv.appendChild(div);
    });

    // Lưu file txt
    const blob = new Blob([response.reviews.data.map(r => `⭐${r.rating} - ${r.created_at}\n${r.content}`).join("\n\n")], {type: "text/plain"});
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `reviews_${response.productId}.txt`;
    a.click();
    URL.revokeObjectURL(url);
} else {
    reviewsDiv.textContent = "Không tìm thấy review nào.";
}

                noteEl.textContent = "Đã lấy dữ liệu và lưu review vào file.";
            });
        });
    });
});
