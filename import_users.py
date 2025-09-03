import csv
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'techxchange.settings')
django.setup()

from catalog.models import Product, Category
from django.contrib.auth.models import User

csv_file = r"C:\Users\VKC\Downloads\db1.csv"

with open(csv_file, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f, delimiter=';')
    for row in reader:
        category = Category.objects.filter(id=row['category_id']).first()
        created_by = User.objects.filter(id=row['created_by']).first()
        updated_by = User.objects.filter(id=row['updated_by']).first() if row['updated_by'] != "0" else None

        Product.objects.update_or_create(
            id=int(row['id']),
            defaults={
                'name': row['name'],
                'slug': row['slug'],
                'brand': row['brand'],
                'specification': row['specification'],
                'description': row['description'],
                'is_active': bool(int(row['is_active'])),
                'created_at': row['created_at'],
                'updated_at': row['updated_at'],
                'category': category,
                'created_by': created_by,
                'updated_by': updated_by,
            }
        )
        print(f"Imported product: {row['name']}")
