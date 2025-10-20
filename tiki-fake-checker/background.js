// background.js

// helper fetch with simple error handling
async function safeFetchJson(url) {
    try {
        const res = await fetch(url, { credentials: 'omit' });
        if (!res.ok) return { error: `HTTP ${res.status} - ${url}` };
        return await res.json();
    } catch (e) {
        return { error: e.toString(), url };
    }
}

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
    if (msg && msg.action === "fetchProductAPI") {
        const id = msg.productId;
        if (!id) {
            sendResponse({ error: "missing productId" });
            return;
        }

        (async () => {
            // endpoint product
            const productUrl = `https://tiki.vn/api/v2/products/${id}`;
            const productJson = await safeFetchJson(productUrl);

            // endpoint reviews (try a couple of forms)
            // This endpoint format may vary; this is a commonly used one.
            const reviewsUrl = `https://tiki.vn/api/v2/reviews?product_id=${id}&limit=5&sort=default`;

            const reviewsJson = await safeFetchJson(reviewsUrl);

            // try another reviews endpoint if the first returns error/empty
            let reviewsData = reviewsJson;
            if (reviewsJson && reviewsJson.error) {
                const altReviewsUrl = `https://tiki.vn/pdp/reviews?product_id=${id}&limit=50`;
                reviewsData = await safeFetchJson(altReviewsUrl);
            }

            // Compose useful summary for popup (so popup doesn't need to parse raw)
            const summary = {
                productId: id,
                product: productJson || null,
                reviews: reviewsData || null
            };

            sendResponse(summary);
        })();

        return true; // keep callback
    }
});
