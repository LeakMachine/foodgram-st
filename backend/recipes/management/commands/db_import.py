import os
import csv
import json
from django.core.management.base import BaseCommand
from recipes.models import Ingredient
from django.conf import settings


class Command(BaseCommand):
    help = 'Импортирует ингредиенты из ingredients.csv или ingredients.json'

    def handle(self, *args, **kwargs):
        if Ingredient.objects.exists():
            self.stdout.write(
                self.style.WARNING('Ингредиенты уже загружены. Пропуск.')
            )
            return

        static_dir = os.path.join(settings.BASE_DIR, 'static')
        csv_path = os.path.join(static_dir, 'ingredients.csv')
        json_path = os.path.join(static_dir, 'ingredients.json')

        if os.path.exists(json_path):
            self.load_from_json(json_path)
        elif os.path.exists(csv_path):
            self.load_from_csv(csv_path)
        else:
            self.stdout.write(self.style.ERROR(
                'Файл ингредиентов не найден (csv или json)')
            )

    def load_from_csv(self, path):
        with open(path, encoding='utf-8') as file:
            reader = csv.reader(file)
            count = 0
            for row in reader:
                if len(row) < 2:
                    continue
                title, unit = row[0].strip(), row[1].strip()
                Ingredient.objects.create(name=title, measurement_unit=unit)
                count += 1
        self.stdout.write(self.style.SUCCESS(
            f'Загружено из CSV: {count} ингредиентов')
        )

    def load_from_json(self, path):
        with open(path, encoding='utf-8') as file:
            data = json.load(file)
            count = 0
            for item in data:
                title = item.get('name')
                unit = item.get('measurement_unit')
                if title and unit:
                    Ingredient.objects.create(
                        name=title.strip(), measurement_unit=unit.strip()
                    )
                    count += 1
        self.stdout.write(self.style.SUCCESS(
            f'Загружено из JSON: {count} ингредиентов')
        )
