from django.core.management.base import BaseCommand
from products.models import Product, ProductCategory


class Command(BaseCommand):
    help = 'Import products from PHP data structure'

    def handle(self, *args, **options):
        # Product data from PHP file
        products_data = [
            {
                'id': 0,
                'name': 'Pro Series Hoodie (Fleece Lined) FULL ZIP',
                'modelLink': '/models/pro-series-hoodie-full-zip.glb',
                'thumbnail': 'static/thumbnails/pro-series-hoodie-full-zip.png',
                'categories': ['Hoodies'],
                'description': 'Premium fleece-lined hoodie with full zip and customizable pockets. Perfect for staying warm while showcasing your custom designs.',
                'initialLayer': 'Front',
                'canOrder': True,
                'sizes': [
                    'Youth Small', 'Youth Medium', 'Youth Large', 'Youth X-Large',
                    'X-Small', 'Small', 'Medium', 'Large', 'X-Large', '2X-Large', '3X-Large', '4X-Large'
                ],
                'prices': {1: 100, 3: 90, 5: 80, 10: 70, 20: 60},
                'initialBumpmap': 'Polyester',
                'supportedBumpmaps': ['Micromesh', 'Polyester'],
                'productDetails': [
                    '100% premium cotton blend',
                    'Pre-shrunk for perfect fit',
                    'Reinforced seams for durability',
                    'Machine washable',
                    'Long-lasting vibrant colors',
                    'Fade-resistant full sublimation'
                ],
            },
            {
                'id': 1,
                'name': 'Pro Series Hoodie (Fleece Lined)',
                'modelLink': '/models/pro-series-hoodie.glb',
                'thumbnail': 'static/thumbnails/pro-series-hoodie.png',
                'categories': ['Hoodies'],
                'description': 'Cozy fleece-lined pullover hoodie designed for all-day comfort. Features a kangaroo pocket and soft drawstring hood for the perfect custom fit.',
                'initialLayer': 'Front',
                'canOrder': True,
                'sizes': [
                    'Youth Small', 'Youth Medium', 'Youth Large', 'Youth X-Large',
                    'X-Small', 'Small', 'Medium', 'Large', 'X-Large', '2X-Large', '3X-Large', '4X-Large'
                ],
                'prices': {1: 90, 3: 80, 5: 70, 10: 65, 20: 55},
                'initialBumpmap': 'Polyester',
                'supportedBumpmaps': ['Micromesh', 'Polyester'],
                'productDetails': [
                    '100% premium fleece material',
                    'Pre-shrunk for perfect fit',
                    'Reinforced seams for durability',
                    'Machine washable',
                    'Long-lasting vibrant colors',
                    'Fade-resistant full sublimation'
                ],
            },
            {
                'id': 7,
                'name': 'Elite Series LS Hood (SPF 40)',
                'modelLink': '/models/elite-series-ls-hood.glb',
                'thumbnail': 'static/thumbnails/elite-series-ls-hood.png',
                'categories': ['Hoodies'],
                'description': 'Lightweight SPF 40 hooded long sleeve perfect for outdoor activities. Provides sun protection while maintaining breathability and comfort.',
                'initialLayer': 'Front',
                'canOrder': True,
                'sizes': [
                    'Youth Small', 'Youth Medium', 'Youth Large', 'Youth X-Large',
                    'X-Small', 'Small', 'Medium', 'Large', 'X-Large', '2X-Large', '3X-Large', '4X-Large'
                ],
                'prices': {1: 80, 3: 70, 5: 60, 10: 55, 20: 45},
                'initialBumpmap': 'Polyester',
                'supportedBumpmaps': ['Micromesh', 'Polyester'],
                'productDetails': [
                    'Lightweight SPF 40 polyester blend',
                    'Pre-shrunk for perfect fit',
                    'Reinforced seams for durability',
                    'Machine washable',
                    'Long-lasting vibrant colors',
                    'Fade-resistant full sublimation'
                ],
            },
            {
                'id': 2,
                'name': 'Elite Series Long Sleeve',
                'modelLink': '/models/elite-series-long-sleeve.glb',
                'thumbnail': 'static/thumbnails/elite-series-long-sleeve.png',
                'categories': ['Jerseys'],
                'description': 'Elite performance long sleeve jersey with moisture-wicking technology. Perfect for teams and athletes who demand superior comfort during intense activities.',
                'initialLayer': 'Front',
                'initialBumpmap': 'Polyester',
                'canOrder': True,
                'sizes': [
                    'Youth Small', 'Youth Medium', 'Youth Large', 'Youth X-Large',
                    'X-Small', 'Small', 'Medium', 'Large', 'X-Large', '2X-Large', '3X-Large', '4X-Large'
                ],
                'prices': {1: 75, 3: 65, 5: 60, 10: 55, 20: 45},
                'supportedBumpmaps': ['Micromesh', 'Polyester'],
                'productDetails': [
                    'Premium moisture-wicking polyester',
                    'Pre-shrunk for perfect fit',
                    'Reinforced seams for durability',
                    'Machine washable',
                    'Long-lasting vibrant colors',
                    'Fade-resistant full sublimation'
                ],
            },
            {
                'id': 3,
                'name': 'Crew Neck Long Sleeve',
                'modelLink': '/models/crew-neck-long-sleeve.glb',
                'thumbnail': 'static/thumbnails/crew-neck-long-sleeve.png',
                'categories': ['Jerseys'],
                'description': 'Classic crew neck long sleeve jersey offering timeless style and athletic functionality. Ideal for layering and custom team designs.',
                'initialLayer': 'Front',
                'initialBumpmap': 'Polyester',
                'canOrder': True,
                'sizes': [
                    'Youth Small', 'Youth Medium', 'Youth Large', 'Youth X-Large',
                    'X-Small', 'Small', 'Medium', 'Large', 'X-Large', '2X-Large', '3X-Large', '4X-Large'
                ],
                'prices': {1: 70, 3: 60, 5: 55, 10: 50, 20: 40},
                'supportedBumpmaps': ['Micromesh', 'Polyester'],
                'productDetails': [
                    'Classic crew neck polyester blend',
                    'Pre-shrunk for perfect fit',
                    'Reinforced seams for durability',
                    'Machine washable',
                    'Long-lasting vibrant colors',
                    'Fade-resistant full sublimation'
                ],
            },
            {
                'id': 9,
                'name': 'Crew Neck Short Sleeve',
                'categories': ['Jerseys', 'Tees'],
                'description': 'Lightweight crew neck short sleeve jersey perfect for warm weather sports and activities. Features breathable fabric for optimal performance.',
                'modelLink': '/models/crew-neck-short-sleeve.glb',
                'thumbnail': 'static/thumbnails/crew-neck-short-sleeve.png',
                'initialLayer': 'Front',
                'initialBumpmap': 'Polyester',
                'canOrder': True,
                'sizes': [
                    'Youth Small', 'Youth Medium', 'Youth Large', 'Youth X-Large',
                    'X-Small', 'Small', 'Medium', 'Large', 'X-Large', '2X-Large', '3X-Large', '4X-Large'
                ],
                'prices': {1: 65, 3: 60, 5: 50, 10: 45, 20: 35},
                'supportedBumpmaps': ['Micromesh', 'Polyester'],
                'productDetails': [
                    'Lightweight crew neck polyester',
                    'Pre-shrunk for perfect fit',
                    'Reinforced seams for durability',
                    'Machine washable',
                    'Long-lasting vibrant colors',
                    'Fade-resistant full sublimation'
                ],
            },
            {
                'id': 10,
                'name': 'Pro Series Short Sleeve',
                'modelLink': '/models/pro-series-short-sleeve.glb',
                'thumbnail': 'static/thumbnails/pro-series-short-sleeve.png',
                'categories': ['Jerseys', 'Tees'],
                'description': 'Premium short sleeve tee that combines classic comfort with custom style. Perfect for everyday wear and showcasing your personal expression.',
                'initialLayer': 'Front',
                'initialBumpmap': 'Polyester',
                'canOrder': True,
                'sizes': [
                    'Youth Small', 'Youth Medium', 'Youth Large', 'Youth X-Large',
                    'X-Small', 'Small', 'Medium', 'Large', 'X-Large', '2X-Large', '3X-Large', '4X-Large'
                ],
                'prices': {1: 65, 3: 60, 5: 55, 10: 50, 20: 40},
                'supportedBumpmaps': ['Micromesh', 'Polyester'],
                'productDetails': [
                    'Premium cotton-polyester blend',
                    'Pre-shrunk for perfect fit',
                    'Reinforced seams for durability',
                    'Machine washable',
                    'Long-lasting vibrant colors',
                    'Fade-resistant full sublimation'
                ],
            },
            {
                'id': 5,
                'name': 'Big Golf Towel',
                'modelLink': '/models/big-golf-towel.glb',
                'thumbnail': 'static/thumbnails/big-golf-towel.png',
                'categories': ['Towels'],
                'description': 'Premium large golf towel designed for superior performance on the course. Highly absorbent with quick-dry technology and convenient clip attachment.',
                'initialLayer': 'Front',
                'initialBumpmap': 'Cloth',
                'canOrder': True,
                'supportedBumpmaps': [],
                'productDetails': [
                    'Premium terry cloth material',
                    'Highly absorbent',
                    'Quick-drying technology',
                    'Machine washable',
                    'Long-lasting vibrant colors',
                    'Fade-resistant full sublimation'
                ],
            },
            {
                'id': 6,
                'name': 'Small Golf Towel',
                'modelLink': '/models/small-golf-towel.glb',
                'thumbnail': 'static/thumbnails/small-golf-towel.png',
                'categories': ['Towels'],
                'description': 'Compact golf towel perfect for on-the-go use and easy bag storage. Features premium terry cloth material with excellent absorption and quick-drying properties.',
                'initialLayer': 'Front',
                'initialBumpmap': 'Cloth',
                'canOrder': True,
                'supportedBumpmaps': [],
                'productDetails': [
                    'Premium terry cloth material',
                    'Highly absorbent',
                    'Quick-drying technology',
                    'Machine washable',
                    'Long-lasting vibrant colors',
                    'Fade-resistant full sublimation'
                ],
            },
            {
                'id': 4,
                'name': 'Cornhole Board',
                'modelLink': '/models/cornhole-board.glb',
                'thumbnail': 'static/thumbnails/cornhole-board.png',
                'categories': ['Home'],
                'description': 'Professional-grade cornhole board built for years of backyard fun and tournament play. Features premium plywood construction with weather-resistant finish.',
                'initialLayer': 'Face',
                'initialBumpmap': 'Marble',
                'canOrder': True,
                'supportedBumpmaps': [],
                'productDetails': [
                    'Premium plywood construction',
                    'Weather-resistant finish',
                    'Durable construction',
                    'Easy to clean',
                    'Long-lasting vibrant colors',
                    'Fade-resistant printing'
                ],
            },
            {
                'id': 8,
                'name': 'Mug',
                'modelLink': '/models/mug.glb',
                'thumbnail': 'static/thumbnails/mug.png',
                'categories': ['Home'],
                'description': 'Durable ceramic mug perfect for your morning coffee and custom designs. Microwave and dishwasher safe with fade-resistant printing.',
                'initialLayer': 'Surface',
                'initialBumpmap': 'Marble',
                'canOrder': True,
                'supportedBumpmaps': [],
                'productDetails': [
                    'High-quality ceramic material',
                    'Microwave and dishwasher safe',
                    'Durable construction',
                    'Easy to clean',
                    'Long-lasting vibrant colors',
                    'Fade-resistant printing'
                ],
            },
            {
                'id': 11,
                'name': 'Tumbler',
                'modelLink': '/models/tumbler.glb',
                'thumbnail': 'static/thumbnails/tumbler.png',
                'categories': ['Home'],
                'description': 'Keep beverages at the perfect temperature with this insulated stainless steel tumbler. Features double-wall construction and comes with a convenient straw.',
                'initialLayer': 'Surface',
                'initialBumpmap': 'Marble',
                'canOrder': True,
                'supportedBumpmaps': [],
                'productDetails': [
                    'Stainless steel construction',
                    'Double-wall insulation',
                    'Durable construction',
                    'Easy to clean',
                    'Long-lasting vibrant colors',
                    'Fade-resistant printing'
                ],
            },
        ]

        self.stdout.write('Starting product import...')

        # Clear existing data
        Product.objects.all().delete()
        ProductCategory.objects.all().delete()

        category_objects = {}
        
        for product_data in products_data:
            # Create categories if they don't exist
            categories = []
            for category_name in product_data.get('categories', []):
                if category_name not in category_objects:
                    category, created = ProductCategory.objects.get_or_create(name=category_name)
                    category_objects[category_name] = category
                    if created:
                        self.stdout.write(f'Created category: {category_name}')
                categories.append(category_objects[category_name])

            # Create product
            product = Product.objects.create(
                name=product_data['name'],
                description=product_data.get('description', ''),
                model_link=product_data.get('modelLink', ''),
                thumbnail=product_data.get('thumbnail', ''),
                initial_layer=product_data.get('initialLayer', 'Front'),
                initial_bumpmap=product_data.get('initialBumpmap', 'Polyester'),
                can_order=product_data.get('canOrder', True),
                sizes=product_data.get('sizes', []),
                prices=product_data.get('prices', {}),
                supported_bumpmaps=product_data.get('supportedBumpmaps', []),
                product_details=product_data.get('productDetails', []),
            )

            # Add categories
            product.categories.set(categories)
            
            self.stdout.write(f'Created product: {product.name}')

        self.stdout.write(
            self.style.SUCCESS(f'Successfully imported {len(products_data)} products')
        )