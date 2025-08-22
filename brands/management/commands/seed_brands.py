from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from brands.models import Brand, BrandOwner, BrandTemplate, BrandImage, BrandImageCategory, BrandEarnings
from products.models import BrandProduct, Product
from django.utils import timezone
from datetime import timedelta
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Seed the database with brands test data'

    def handle(self, *args, **options):
        self.stdout.write("🌱 Seeding brands database...")
        
        # Clear existing data
        self.stdout.write("Clearing existing data...")
        BrandOwner.objects.all().delete()
        BrandEarnings.objects.all().delete()
        BrandImage.objects.all().delete()
        BrandImageCategory.objects.all().delete()
        BrandTemplate.objects.all().delete()
        BrandProduct.objects.all().delete()
        Brand.objects.all().delete()
        User.objects.filter(email__in=['brandowner@example.com', 'admin@example.com']).delete()

        # Create admin user
        admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='admin123',
            first_name='Admin',
            last_name='User',
            is_staff=True,
            is_superuser=True
        )
        self.stdout.write(f"✓ Created admin: admin@example.com / admin123")

        # Create brand owner user
        brand_user = User.objects.create_user(
            username='brandowner',
            email='brandowner@example.com',
            password='brand123',
            first_name='Brand',
            last_name='Owner',
            is_brand_owner=True
        )
        self.stdout.write(f"✓ Created brand owner: brandowner@example.com / brand123")

        # Create test brands
        brands_data = [
            {
                'name': 'Acme Sports',
                'slug': 'acme-sports',
                'subdomain': 'acme',
                'description': 'Premium sports apparel and accessories',
                'contact_email': 'contact@acmesports.com',
                'website_url': 'https://acmesports.com',
                'primary_color': '#ff6b35',
                'secondary_color': '#004e98',
                'is_active': True,
            },
            {
                'name': 'Tech Gear Pro',
                'slug': 'tech-gear-pro',
                'subdomain': 'techgear',
                'description': 'Professional technology merchandise and branding',
                'contact_email': 'hello@techgearpro.com',
                'website_url': 'https://techgearpro.com',
                'primary_color': '#2563eb',
                'secondary_color': '#64748b',
                'is_active': True,
            },
            {
                'name': 'Default Brand',
                'slug': 'default-brand',
                'subdomain': '',
                'description': 'Default brand for main domain',
                'is_default': True,
                'is_active': True,
                'primary_color': '#0d6efd',
                'secondary_color': '#6c757d',
            }
        ]

        created_brands = []
        for brand_data in brands_data:
            brand = Brand.objects.create(**brand_data)
            created_brands.append(brand)
            self.stdout.write(f"✓ Created brand: {brand.name}")

        # Assign brand ownership
        for brand in created_brands[:2]:  # Not the default brand
            BrandOwner.objects.create(
                brand=brand,
                user=brand_user,
                is_primary=True
            )
            self.stdout.write(f"✓ Assigned {brand_user.email} as owner of {brand.name}")

        # Create image categories
        categories_data = [
            {'name': 'Backgrounds', 'slug': 'backgrounds', 'description': 'Background images and textures'},
            {'name': 'Logos', 'slug': 'logos', 'description': 'Brand logos and marks'},
            {'name': 'Textures', 'slug': 'textures', 'description': 'Texture maps and patterns'},
            {'name': 'Icons', 'slug': 'icons', 'description': 'Icon sets and graphics'},
        ]

        for brand in created_brands:
            for cat_data in categories_data:
                BrandImageCategory.objects.create(
                    brand=brand,
                    name=cat_data['name'],
                    slug=cat_data['slug'],
                    description=cat_data['description']
                )

        # Create sample brand images
        sample_images = [
            {'name': 'Logo Primary', 'category_slug': 'logos'},
            {'name': 'Background Pattern', 'category_slug': 'backgrounds'},
            {'name': 'Texture 1', 'category_slug': 'textures'},
            {'name': 'Icon Set', 'category_slug': 'icons'},
        ]

        for brand in created_brands[:2]:  # Only for non-default brands
            for img_data in sample_images:
                category = BrandImageCategory.objects.get(brand=brand, slug=img_data['category_slug'])
                BrandImage.objects.create(
                    brand=brand,
                    category=category,
                    name=f"{brand.name} - {img_data['name']}",
                    image_url=f'https://via.placeholder.com/400x200/{brand.primary_color[1:]}/white?text={img_data["name"].replace(" ", "+")}',
                    thumbnail_url=f'https://via.placeholder.com/200x100/{brand.primary_color[1:]}/white?text={img_data["name"].replace(" ", "+")}',
                    alt_text=f"{img_data['name']} for {brand.name}",
                    is_public=random.choice([True, False]),
                    width=400,
                    height=200,
                    file_size=random.randint(10000, 100000),
                )

        # Create sample brand templates
        template_data = [
            {'name': 'Summer Collection', 'description': 'Bright summer designs with tropical themes'},
            {'name': 'Corporate Identity', 'description': 'Professional business template set'},
            {'name': 'Vintage Sports', 'description': 'Retro-inspired sports merchandise designs'},
            {'name': 'Modern Tech', 'description': 'Clean, minimalist tech-focused templates'},
        ]

        for brand in created_brands[:2]:
            for i, tmpl_data in enumerate(template_data):
                BrandTemplate.objects.create(
                    brand=brand,
                    name=f"{brand.name} - {tmpl_data['name']}",
                    description=tmpl_data['description'],
                    template_data={'layers': [], 'meshes': [], 'version': '1.0'},
                    thumbnail_url=f'https://via.placeholder.com/300x200/{brand.primary_color[1:]}/white?text=Template',
                    is_public=i < 2,  # First 2 are public
                    is_featured=i == 0,  # First one is featured
                    usage_count=random.randint(0, 50),
                    created_by=brand_user,
                )

        # Create sample earnings data
        if created_brands:
            brand = created_brands[0]  # Use first brand
            base_date = timezone.now() - timedelta(days=90)
            
            for i in range(20):
                order_date = base_date + timedelta(days=random.randint(0, 90))
                order_amount = random.uniform(25.0, 150.0)
                commission_rate = random.uniform(8.0, 15.0)
                
                BrandEarnings.objects.create(
                    brand=brand,
                    order_id=1000 + i,
                    amount=round(order_amount, 2),
                    commission_rate=round(commission_rate, 2),
                    commission_amount=round((order_amount * commission_rate) / 100, 2),
                    payment_status=random.choice(['pending', 'paid', 'pending', 'paid']),
                    transaction_date=order_date,
                    payment_date=order_date + timedelta(days=random.randint(7, 30)) if random.choice([True, False]) else None,
                    notes=f'Order #{1000 + i} commission payment',
                )

        # Assign products to brands if they exist
        if Product.objects.exists():
            products = Product.objects.all()[:5]
            
            for brand in created_brands:
                for i, product in enumerate(products):
                    BrandProduct.objects.create(
                        brand=brand,
                        product=product,
                        is_available=True,
                        custom_prices={} if i % 2 == 0 else {'1': str(random.uniform(20.0, 50.0))}
                    )

        self.stdout.write(self.style.SUCCESS("\n🎉 Database seeded successfully!"))
        self.stdout.write("\nLogin credentials:")
        self.stdout.write("👤 Brand Owner: brandowner@example.com / brand123")
        self.stdout.write("🔧 Admin: admin@example.com / admin123")
        self.stdout.write("\nURLs to test:")
        self.stdout.write("📊 Brand Dashboard: http://localhost:8001/brand/dashboard/")
        self.stdout.write("⚙️  Django Admin: http://localhost:8001/admin/")
        self.stdout.write("🔑 Login Page: http://localhost:8001/accounts/login/")