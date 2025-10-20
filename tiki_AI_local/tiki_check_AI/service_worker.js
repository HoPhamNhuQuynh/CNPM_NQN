chrome.runtime.onMessage.addListener((msg, sender) => {
  if (msg.type === 'PREDICT') {
    fetch('http://127.0.0.1:5000/predict', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({reviews: msg.reviews, price: msg.price})
    })
    .then(r => r.json())
    .then(result => {
      chrome.tabs.query({active: true, currentWindow: true}, (tabs) => {
        if (tabs[0]) {
          chrome.tabs.sendMessage(tabs[0].id, {type: 'PREDICTION_RESULT', result});
        }
      });
    })
    .catch(err => console.error('Predict error', err));
  }
});
