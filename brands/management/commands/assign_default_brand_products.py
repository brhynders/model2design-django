from django.core.management.base import BaseCommand
from brands.models import Brand
from products.models import Product, BrandProduct


class Command(BaseCommand):
    help = 'Assign specific products to the default brand'

    def handle(self, *args, **options):
        self.stdout.write('Assigning products to default brand...')

        # Get default brand
        try:
            default_brand = Brand.objects.get(is_default=True)
        except Brand.DoesNotExist:
            self.stdout.write(self.style.ERROR('No default brand found. Run setup_test_brands first.'))
            return

        # Get products that are not assigned to any other brand
        # These would be the "remaining" products for the default brand
        assigned_product_ids = BrandProduct.objects.exclude(
            brand=default_brand
        ).values_list('product_id', flat=True)
        
        unassigned_products = Product.objects.exclude(
            id__in=assigned_product_ids
        ).filter(can_order=True)

        # Assign unassigned products to default brand
        for product in unassigned_products:
            brand_product, created = BrandProduct.objects.get_or_create(
                brand=default_brand,
                product=product,
                defaults={
                    'is_available': True,
                    # Default brand uses standard product pricing (no custom prices)
                }
            )
            if created:
                self.stdout.write(f'Assigned {product.name} to {default_brand.name}')

        # Get final counts
        default_count = BrandProduct.objects.filter(brand=default_brand).count()
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully assigned products to default brand!')
        )
        
        self.stdout.write(f'\nFinal count for {default_brand.name}: {default_count} products')
        
        # Show what products each brand has
        all_brands = Brand.objects.filter(is_active=True)
        for brand in all_brands:
            count = BrandProduct.objects.filter(brand=brand).count()
            products = [bp.product.name for bp in BrandProduct.objects.filter(brand=brand)[:3]]
            products_str = ', '.join(products)
            if count > 3:
                products_str += f'... (+{count-3} more)'
            
            subdomain_info = f" ({brand.subdomain}.domain.com)" if brand.subdomain else " (main domain)"
            self.stdout.write(f'- {brand.name}{subdomain_info}: {count} products - {products_str}')