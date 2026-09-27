"""Relational vehicle catalog and shared authentication throttle."""

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class CarMake(models.Model):
    name = models.CharField(max_length=60, unique=True)
    description = models.TextField(blank=True, max_length=1000)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class CarModel(models.Model):
    car_make = models.ForeignKey(CarMake, on_delete=models.PROTECT, related_name="models")
    name = models.CharField(max_length=80)
    body_type = models.CharField(max_length=30)
    year = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1900), MaxValueValidator(2100)]
    )

    class Meta:
        ordering = ["car_make__name", "name", "year"]
        constraints = [
            models.UniqueConstraint(
                fields=["car_make", "name", "year"], name="unique_vehicle_variant"
            )
        ]

    def __str__(self):
        return f"{self.car_make.name} {self.name} ({self.year})"


class AuthAttempt(models.Model):
    key = models.CharField(max_length=64, db_index=True)
    created = models.DateTimeField(auto_now_add=True, db_index=True)
