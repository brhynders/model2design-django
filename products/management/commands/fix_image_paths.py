from django.core.management.base import BaseCommand
from products.models import Product


class Command(BaseCommand):
    help = 'Fix product image paths from static/ to static/'

    def handle(self, *args, **options):
        products = Product.objects.all()
        
        for product in products:
            if product.thumbnail and product.thumbnail.startswith('static/'):
                old_path = product.thumbnail
                new_path = product.thumbnail.replace('static/', '', 1)
                product.thumbnail = new_path
                product.save()
                self.stdout.write(f'Updated {product.name}: {old_path} -> {new_path}')
        
        self.stdout.write(
            self.style.SUCCESS('Successfully updated all product image paths')
        )