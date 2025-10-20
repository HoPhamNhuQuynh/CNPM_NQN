// content-script.js

function safeQuery(selectors) {
    for (let sel of selectors) {
        try {
            const el = document.querySelector(sel);
            if (el && el.innerText) return el.innerText.trim();
        } catch (e) { }
    }
    return "";
}

function getProductIdFromUrl() {
    // Tiki thường có định dạng ...-p{productId}.html
    const m = window.location.pathname.match(/-p(\d+)\.html/);
    if (m) return m[1];
    // fallback: có khi trang SPA không dùng .html - thử tìm trong DOM data attribute
    const meta = document.querySelector('meta[property="og:url"]');
    if (meta && meta.content) {
        const mm = meta.content.match(/-p(\d+)\.html/);
        if (mm) return mm[1];
    }
    return null;
}

function extractProductInfo() {
    const productId = getProductIdFromUrl();

    const title = safeQuery([
        'h1[data-view-id="pdp_product_title"]',
        'h1',
        '.title',
        '.product-title'
    ]);

    const price = safeQuery([
        '.product-price__current-price',
        '.styles__Price-sc-1o67jhy-2',
        '.price-discount__price'
    ]);

    const seller = safeQuery([
        '.seller-name',
        '.seller-info__name',
        '[data-view-id="pdp_seller_name"]'
    ]);

    return { productId, title, price, seller };
}

// Listener: trả về basic info cho popup
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
    if (msg && msg.action === "extract") {
        // delay nhỏ để SPA có thể render
        setTimeout(() => {
            sendResponse(extractProductInfo());
        }, 300);
        return true; // giữ callback async
    }
});
