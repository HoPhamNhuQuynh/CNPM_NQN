from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import re

app = Flask(__name__)
CORS(app)  # cho phép extension gọi local API

# Load model .pkl
model1 = joblib.load('model1.pkl')
model2 = joblib.load('model2.pkl')

def clean_text(text):
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'http\S+', '', text)
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def aggregate_reviews(reviews):
    reviews = [clean_text(r) for r in reviews if r]
    return " ".join(reviews[:20])

@app.route('/predict', methods=['POST'])
def predict():
    data = request.json
    reviews = data.get('reviews', [])
    price_raw = data.get('price', "")
    try:
        price = float(re.sub(r'[^\d.]', '', str(price_raw)))
    except:
        price = 0.0

    text_input = aggregate_reviews(reviews)

    try:
        pred1 = model1.predict([text_input])
    except Exception as e:
        pred1 = ["error: "+str(e)]

    try:
        pred2 = model2.predict([text_input])
    except Exception as e:
        pred2 = ["error: "+str(e)]

    return jsonify({
        'model1': pred1[0] if hasattr(pred1, '__len__') else pred1,
        'model2': pred2[0] if hasattr(pred2, '__len__') else pred2,
        'price': price
    })

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5000, debug=True)
