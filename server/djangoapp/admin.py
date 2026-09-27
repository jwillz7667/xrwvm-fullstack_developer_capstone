from django.contrib import admin
from .models import CarMake, CarModel


@admin.register(CarMake)
class CarMakeAdmin(admin.ModelAdmin):
    list_display = ["name", "description"]
    search_fields = ["name"]


@admin.register(CarModel)
class CarModelAdmin(admin.ModelAdmin):
    list_display = ["name", "car_make", "body_type", "year"]
    list_filter = ["car_make", "body_type", "year"]
    search_fields = ["name", "car_make__name"]


admin.site.site_header = "OpenRoad Administration"
