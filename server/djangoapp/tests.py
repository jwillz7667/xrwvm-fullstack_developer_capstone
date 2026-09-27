import json
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from .models import CarMake, CarModel


class PortalSecurityTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            "reviewer", password="Nontrivial-Testing-739!"
        )
        make = CarMake.objects.create(name="Example Motors")
        self.car = CarModel.objects.create(
            car_make=make, name="Touring", body_type="Sedan", year=2023
        )

    def post(self, path, data, client=None):
        return (client or self.client).post(
            "/djangoapp/" + path, json.dumps(data), content_type="application/json"
        )

    def test_csrf_is_required_for_login_and_logout(self):
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(
            self.post(
                "login", {"userName": "reviewer", "password": "Nontrivial-Testing-739!"}, client
            ).status_code,
            403,
        )
        self.assertEqual(self.post("logout", {}, client).status_code, 403)

    def test_session_login_logout_and_invalid_credentials(self):
        self.assertEqual(
            self.post("login", {"userName": "reviewer", "password": "wrong"}).status_code, 401
        )
        self.assertEqual(
            self.post(
                "login", {"userName": "reviewer", "password": "Nontrivial-Testing-739!"}
            ).status_code,
            200,
        )
        self.assertEqual(self.client.get("/djangoapp/session").json()["userName"], "reviewer")
        self.assertEqual(self.client.get("/djangoapp/logout").status_code, 405)
        self.assertEqual(self.post("logout", {}).status_code, 200)
        self.assertIsNone(self.client.get("/djangoapp/session").json()["userName"])

    def test_review_requires_session(self):
        self.assertEqual(
            self.post("add_review", {"dealership": 1, "review": "Helpful staff"}).status_code, 401
        )

    @patch("djangoapp.views.analyze_review_sentiments", return_value="positive")
    @patch("djangoapp.views.request_json")
    def test_review_uses_authenticated_identity_not_forged_body(self, request_json, _sentiment):
        self.client.force_login(self.user)
        request_json.side_effect = [[{"id": 1}], {"id": "new-review"}]
        response = self.post(
            "add_review",
            {
                "dealership": 1,
                "review": "Helpful staff",
                "purchase": False,
                "user_id": 999,
                "name": "Another user",
            },
        )
        self.assertEqual(response.status_code, 201)
        submitted = request_json.call_args.args[2]
        self.assertEqual(submitted["user_id"], self.user.pk)
        self.assertEqual(submitted["name"], "reviewer")
        self.assertEqual(submitted["sentiment"], "positive")

    def test_invalid_purchase_and_bad_json_rejected(self):
        self.client.force_login(self.user)
        self.assertEqual(
            self.post(
                "add_review",
                {
                    "dealership": 1,
                    "review": "Good",
                    "purchase": True,
                    "car_id": self.car.pk,
                    "purchase_date": "2999-01-01",
                },
            ).status_code,
            400,
        )
        self.assertEqual(
            self.client.post("/djangoapp/login", "{", content_type="application/json").status_code,
            400,
        )
        self.assertEqual(
            self.post("add_review", {"dealership": True, "review": "Good"}).status_code, 400
        )

    def test_registration_rejects_weak_password_and_creates_valid_account(self):
        data = {
            "userName": "newdriver",
            "firstName": "New",
            "lastName": "Driver",
            "email": "driver@example.com",
            "password": "12345678",
        }
        self.assertEqual(self.post("register", data).status_code, 400)
        data["password"] = "Long-Unique-Testing-1982!"
        self.assertEqual(self.post("register", data).status_code, 201)
        self.assertTrue(
            get_user_model().objects.get(username="newdriver").check_password(data["password"])
        )
        self.assertEqual(self.post("register", data).status_code, 400)

    def test_login_throttles_repeated_attempts(self):
        for _ in range(20):
            self.post("login", {"userName": "reviewer", "password": "wrong"})
        self.assertEqual(
            self.post("login", {"userName": "reviewer", "password": "wrong"}).status_code, 429
        )

    def test_catalog_and_admin_access(self):
        self.assertEqual(
            self.client.get("/djangoapp/get_cars").json()["models"][0]["make"], "Example Motors"
        )
        self.assertEqual(self.client.get("/admin/").status_code, 302)
        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save()
        self.client.force_login(self.user)
        self.assertEqual(self.client.get("/admin/").status_code, 200)
