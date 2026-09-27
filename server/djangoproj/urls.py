from django.contrib import admin
from django.urls import include, path, re_path
from django.views.generic import TemplateView
from djangoapp import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("djangoapp/", include("djangoapp.urls")),
    path("healthz", views.health),
    path("about", TemplateView.as_view(template_name="About.html")),
    path("contact", TemplateView.as_view(template_name="Contact.html")),
    re_path(r"^(?:|dealers|login|register|dealer/[0-9]+|postreview/[0-9]+)$", views.page),
]
