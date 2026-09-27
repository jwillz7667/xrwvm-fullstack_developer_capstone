"""Bounded, server-to-server HTTP calls; never accept a client-provided URL."""

from urllib.parse import quote
import requests
from django.conf import settings


class UpstreamError(Exception):
    pass


def request_json(method, path, payload=None):
    try:
        response = requests.request(
            method,
            settings.BACKEND_URL + path,
            json=payload,
            headers={"X-Service-Key": settings.SERVICE_KEY},
            timeout=(3, 10),
        )
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, ValueError) as error:
        raise UpstreamError("The dealership service is temporarily unavailable.") from error


def analyze_review_sentiments(text):
    try:
        response = requests.get(
            settings.SENTIMENT_URL + "/analyze/" + quote(text, safe=""), timeout=(3, 8)
        )
        response.raise_for_status()
        sentiment = response.json()["sentiment"]
        if sentiment not in {"positive", "neutral", "negative"}:
            raise ValueError("Invalid sentiment")
        return sentiment
    except (requests.RequestException, ValueError, KeyError) as error:
        raise UpstreamError(
            "The sentiment service is temporarily unavailable. Please try again."
        ) from error
