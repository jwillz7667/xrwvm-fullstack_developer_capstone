"""VADER sentiment microservice with a vendored course lexicon."""

from pathlib import Path
from flask import Flask, jsonify
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer

nltk.data.path.insert(0, str(Path(__file__).resolve().parent))
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16384
analyzer = SentimentIntensityAnalyzer()


@app.get("/healthz")
def health():
    return jsonify(status="ok")


@app.get("/analyze/<path:input_txt>")
def analyze(input_txt):
    if not input_txt.strip() or len(input_txt) > 3000:
        return jsonify(error="Provide 1–3000 characters."), 400
    score = analyzer.polarity_scores(input_txt)["compound"]
    sentiment = "positive" if score >= 0.05 else "negative" if score <= -0.05 else "neutral"
    return jsonify(sentiment=sentiment, compound=score)


@app.after_request
def headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Cache-Control"] = "no-store"
    return response
