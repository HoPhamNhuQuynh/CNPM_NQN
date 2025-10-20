function getPrice() {
  const el = document.querySelector('.product-price__current, .price'); 
  return el ? el.innerText.trim() : "";
}

function getReviews() {
  const nodes = document.querySelectorAll('.review-item__content, .pdp-review__review'); 
  return Array.from(nodes).map(n => n.innerText.trim()).slice(0, 50);
}

(async function sendToBackground(){
  const reviews = getReviews();
  const price = getPrice();
  chrome.runtime.sendMessage({type: 'PREDICT', reviews, price});
})();

chrome.runtime.onMessage.addListener((msg) => {
  if (msg.type === 'PREDICTION_RESULT') {
    let container = document.getElementById('ai-prediction-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'ai-prediction-container';
      container.style.position = 'fixed';
      container.style.right = '12px';
      container.style.bottom = '80px';
      container.style.zIndex = 999999;
      container.style.background = 'white';
      container.style.border = '1px solid #ccc';
      container.style.padding = '12px';
      container.style.boxShadow = '0 2px 8px rgba(0,0,0,0.15)';
      document.body.appendChild(container);
    }
    container.innerHTML = `
      <strong>AI Predictions</strong><br>
      Model1: ${msg.result.model1}<br>
      Model2: ${msg.result.model2}<br>
      Price(parsed): ${msg.result.price}
    `;
  }
});
