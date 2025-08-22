from django.core.management.base import BaseCommand
from brands.models import Brand
from products.models import Product, BrandProduct


class Command(BaseCommand):
    help = 'Setup test brands and brand-product relationships'

    def handle(self, *args, **options):
        self.stdout.write('Setting up test brands...')

        # Create default brand
        default_brand, created = Brand.objects.get_or_create(
            is_default=True,
            defaults={
                'name': 'Model2Design',
                'slug': 'model2design',
                'description': 'Default brand with all products',
                'primary_color': '#0d6efd',
                'secondary_color': '#6c757d',
            }
        )
        if created:
            self.stdout.write(f'Created default brand: {default_brand.name}')

        # Create test brand 1 - SportsPro (only sports-related products)
        sportspro_brand, created = Brand.objects.get_or_create(
            subdomain='sportspro',
            defaults={
                'name': 'SportsPro',
                'slug': 'sportspro',
                'description': 'Professional sports apparel brand',
                'primary_color': '#28a745',
                'secondary_color': '#17a2b8',
                'is_active': True,
            }
        )
        if created:
            self.stdout.write(f'Created brand: {sportspro_brand.name}')

        # Create test brand 2 - HomeStyle (only home products)
        homestyle_brand, created = Brand.objects.get_or_create(
            subdomain='homestyle',
            defaults={
                'name': 'HomeStyle',
                'slug': 'homestyle',
                'description': 'Custom home decor and accessories',
                'primary_color': '#dc3545',
                'secondary_color': '#ffc107',
                'is_active': True,
            }
        )
        if created:
            self.stdout.write(f'Created brand: {homestyle_brand.name}')

        # Get products by category
        jerseys_products = Product.objects.filter(categories__name='Jerseys')
        hoodies_products = Product.objects.filter(categories__name='Hoodies')
        home_products = Product.objects.filter(categories__name='Home')
        tees_products = Product.objects.filter(categories__name='Tees')

        # Setup SportsPro brand products (Jerseys, Hoodies, Tees - sports related)
        sports_products = list(jerseys_products) + list(hoodies_products) + list(tees_products)
        for product in sports_products:
            brand_product, created = BrandProduct.objects.get_or_create(
                brand=sportspro_brand,
                product=product,
                defaults={
                    'is_available': True,
                    'custom_prices': {
                        '1': str(float(product.get_base_price()) * 1.1),  # 10% markup
                        '5': str(float(product.get_base_price()) * 1.0),  # Base price
                        '10': str(float(product.get_base_price()) * 0.9), # 10% discount
                    }
                }
            )
            if created:
                self.stdout.write(f'Added {product.name} to {sportspro_brand.name}')

        # Setup HomeStyle brand products (Home products only)
        for product in home_products:
            brand_product, created = BrandProduct.objects.get_or_create(
                brand=homestyle_brand,
                product=product,
                defaults={
                    'is_available': True,
                    'custom_prices': {
                        '1': str(float(product.get_base_price()) * 1.2),  # 20% markup for custom
                        '3': str(float(product.get_base_price()) * 1.1),  # 10% markup
                        '5': str(float(product.get_base_price()) * 1.0),  # Base price
                    }
                }
            )
            if created:
                self.stdout.write(f'Added {product.name} to {homestyle_brand.name}')

        self.stdout.write(
            self.style.SUCCESS('Successfully set up test brands and product relationships!')
        )
        
        self.stdout.write('\nBrand Summary:')
        self.stdout.write(f'- Default Brand (no subdomain): {Product.objects.count()} products')
        self.stdout.write(f'- SportsPro (sportspro.domain.com): {BrandProduct.objects.filter(brand=sportspro_brand).count()} products')
        self.stdout.write(f'- HomeStyle (homestyle.domain.com): {BrandProduct.objects.filter(brand=homestyle_brand).count()} products')