"""Session-authenticated, CSRF-protected API for the React client."""

import hashlib
import json
from datetime import date, timedelta
from functools import wraps
from urllib.parse import quote
from django.conf import settings
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import IntegrityError
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST
from .models import CarMake, CarModel, AuthAttempt
from .restapis import get_request, post_review, analyze_review_sentiments, UpstreamError

User = get_user_model()


def api_errors(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        try:
            return view(request, *args, **kwargs)
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError, TypeError, KeyError) as error:
            return JsonResponse({"error": str(error) or "Invalid request."}, status=400)
        except ValidationError as error:
            return JsonResponse({"error": " ".join(error.messages)}, status=400)
        except UpstreamError as error:
            return JsonResponse({"error": str(error)}, status=503)

    return wrapped


def body(request):
    if request.content_type != "application/json":
        raise ValueError("Use application/json.")
    value = json.loads(request.body)
    if not isinstance(value, dict):
        raise ValueError("Expected a JSON object.")
    return value


def text(data, key, maximum, optional=False):
    value = data.get(key, "")
    if not isinstance(value, str):
        raise ValueError(f"Invalid {key}.")
    value = value.strip()
    if (not value and not optional) or len(value) > maximum:
        raise ValueError(f"{key} must contain 1–{maximum} characters.")
    return value


def throttle(request, username):
    cutoff = timezone.now() - timedelta(minutes=10)
    # Do not persist raw IP addresses or usernames in the throttle table.
    keys = [
        hashlib.sha256((settings.SECRET_KEY + value).encode()).hexdigest()
        for value in [request.META.get("REMOTE_ADDR", "unknown"), username.casefold()]
    ]
    AuthAttempt.objects.filter(created__lt=cutoff).delete()
    if any(AuthAttempt.objects.filter(key=key, created__gte=cutoff).count() >= 20 for key in keys):
        return JsonResponse(
            {"error": "Too many attempts. Please try again in ten minutes."}, status=429
        )
    AuthAttempt.objects.bulk_create([AuthAttempt(key=key) for key in keys])
    return None


@ensure_csrf_cookie
@require_GET
def page(request):
    return render(request, "index.html")


@ensure_csrf_cookie
@require_GET
def session(request):
    return JsonResponse(
        {"userName": request.user.username if request.user.is_authenticated else None}
    )


@require_POST
@api_errors
def login_user(request):
    data = body(request)
    username = text(data, "userName", 150)
    limited = throttle(request, username)
    if limited:
        return limited
    password = data.get("password", "")
    if not isinstance(password, str) or len(password) > 256:
        raise ValueError("Invalid credentials.")
    user = authenticate(request, username=username, password=password)
    if user is None:
        return JsonResponse({"error": "Incorrect username or password."}, status=401)
    login(request, user)
    return JsonResponse({"userName": user.username, "status": "Authenticated"})


@require_POST
def logout_request(request):
    logout(request)
    return JsonResponse({"status": "Logged out"})


@require_POST
@api_errors
def registration(request):
    data = body(request)
    username = text(data, "userName", 150)
    limited = throttle(request, username)
    if limited:
        return limited
    user = User(
        username=username,
        first_name=text(data, "firstName", 150),
        last_name=text(data, "lastName", 150),
        email=text(data, "email", 254),
    )
    validate_email(user.email)
    user.full_clean(exclude=["password"])
    password = data.get("password", "")
    if not isinstance(password, str) or len(password) > 256:
        raise ValueError("Password must be no longer than 256 characters.")
    validate_password(password, user)
    user.set_password(password)
    try:
        user.save()
    except IntegrityError:
        return JsonResponse({"error": "This username is unavailable."}, status=409)
    login(request, user)
    return JsonResponse({"userName": user.username, "status": "Registered"}, status=201)


@require_GET
@api_errors
def get_dealerships(request, state=""):
    if len(state) > 50:
        raise ValueError("Invalid state.")
    endpoint = "/fetchDealers" + ("/" + quote(state, safe="") if state and state != "All" else "")
    return JsonResponse({"status": 200, "dealers": get_request(endpoint)})


@require_GET
@api_errors
def get_dealer_details(request, dealer_id):
    dealers = get_request(f"/fetchDealer/{dealer_id}")
    return JsonResponse(
        {"status": 200 if dealers else 404, "dealer": dealers}, status=200 if dealers else 404
    )


@require_GET
@api_errors
def get_dealer_reviews(request, dealer_id):
    return JsonResponse(
        {"status": 200, "reviews": get_request(f"/fetchReviews/dealer/{dealer_id}")}
    )


@require_GET
def get_cars(request):
    makes = list(CarMake.objects.values("id", "name", "description"))
    models = [
        {
            "id": car.pk,
            "make": car.car_make.name,
            "model": car.name,
            "year": car.year,
            "body_type": car.body_type,
        }
        for car in CarModel.objects.select_related("car_make")
    ]
    return JsonResponse({"status": 200, "makes": makes, "models": models})


@require_POST
@api_errors
def add_review(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Please log in to write a review."}, status=401)
    data = body(request)
    dealer_id = data.get("dealership")
    if type(dealer_id) is not int or dealer_id <= 0:
        raise ValueError("Choose a valid dealership.")
    review = text(data, "review", 3000)
    purchase = data.get("purchase", False)
    if not isinstance(purchase, bool):
        raise ValueError("Invalid purchase value.")
    record = {
        "user_id": request.user.pk,
        "name": request.user.get_full_name() or request.user.username,
        "dealership": dealer_id,
        "review": review,
        "purchase": purchase,
        "time": timezone.now().isoformat(),
        "car_make": "",
        "car_model": "",
        "car_year": None,
        "purchase_date": "",
    }
    if purchase:
        try:
            car = CarModel.objects.select_related("car_make").get(pk=data.get("car_id"))
        except (CarModel.DoesNotExist, TypeError, ValueError):
            raise ValueError("Choose a valid vehicle.") from None
        purchased = date.fromisoformat(text(data, "purchase_date", 10))
        if purchased > date.today() or purchased.year < 1900:
            raise ValueError("Choose a purchase date in the past.")
        record.update(
            car_make=car.car_make.name,
            car_model=car.name,
            car_year=car.year,
            purchase_date=purchased.isoformat(),
        )
    if not get_request(f"/fetchDealer/{dealer_id}"):
        return JsonResponse({"error": "Dealership not found."}, status=404)
    record["sentiment"] = analyze_review_sentiments(review)
    saved = post_review(record)
    return JsonResponse({"status": 201, "review": saved}, status=201)


@require_GET
def health(request):
    return JsonResponse({"status": "ok"})
