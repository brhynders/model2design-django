from django.core.management.base import BaseCommand
from django.utils.text import slugify
from products.models import ProductCategory


class Command(BaseCommand):
    help = 'Populate slug fields for existing categories'

    def handle(self, *args, **options):
        categories = ProductCategory.objects.all()
        
        for category in categories:
            if not category.slug:
                category.slug = slugify(category.name)
                category.save()
                self.stdout.write(f'Updated slug for: {category.name} -> {category.slug}')
        
        self.stdout.write(
            self.style.SUCCESS('Successfully populated all category slugs')
        )