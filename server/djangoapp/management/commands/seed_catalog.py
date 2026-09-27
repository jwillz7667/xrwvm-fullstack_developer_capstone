"""Load the supplied course vehicle fixtures without deleting existing data."""

import json
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings
from djangoapp.models import CarMake, CarModel


class Command(BaseCommand):
    help = "Idempotently import the supplied vehicle catalog"

    def handle(self, *args, **options):
        data = json.loads((Path(settings.BASE_DIR) / "database/data/car_records.json").read_text())
        for record in data["cars"]:
            make, _ = CarMake.objects.get_or_create(
                name=record["make"],
                defaults={
                    "description": f"{record['make']} vehicles in the supplied dealership catalog."
                },
            )
            CarModel.objects.get_or_create(
                car_make=make,
                name=record["model"],
                year=record["year"],
                defaults={"body_type": record["bodyType"]},
            )
        self.stdout.write(
            self.style.SUCCESS(
                f"Catalog: {CarMake.objects.count()} makes; {CarModel.objects.count()} models"
            )
        )
