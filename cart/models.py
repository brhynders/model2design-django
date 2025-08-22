from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
import json

User = get_user_model()


class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=40, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        if self.user:
            return f"Cart for {self.user.email}"
        return f"Guest Cart ({self.session_key})"
    
    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())
    
    @property
    def subtotal(self):
        return sum(item.total_price for item in self.items.all())
    
    @property
    def shipping_cost(self):
        # Fixed $15 shipping as per PHP code
        return Decimal('15.00')
    
    @property
    def total(self):
        return self.subtotal + self.shipping_cost
    
    def clear(self):
        """Clear all items from cart"""
        self.items.all().delete()
    
    def merge_with_session_cart(self, session_cart_data):
        """Merge session cart data into this cart"""
        for item_data in session_cart_data:
            design_id = item_data.get('design_id')
            sizes = item_data.get('sizes', {})
            
            # Try to find existing cart item for this design
            existing_item = self.items.filter(design_id=design_id).first()
            
            if existing_item:
                # Merge sizes
                existing_sizes = existing_item.sizes or {}
                for size, qty in sizes.items():
                    existing_sizes[size] = existing_sizes.get(size, 0) + qty
                existing_item.sizes = existing_sizes
                existing_item.quantity = sum(existing_sizes.values())
                existing_item.update_price()
                existing_item.save()
            else:
                # Create new item
                CartItem.objects.create(
                    cart=self,
                    design_id=design_id,
                    sizes=sizes,
                    quantity=sum(sizes.values()),
                    design_name=item_data.get('design_name', ''),
                    thumbnail=item_data.get('thumbnail', ''),
                    product_id=item_data.get('product_id')
                )


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    
    # Design information - can reference database design or guest design
    design_id = models.CharField(max_length=100)  # Can be integer ID or guest string ID
    design_name = models.CharField(max_length=200, blank=True)
    thumbnail = models.CharField(max_length=500, blank=True)
    product_id = models.IntegerField()
    
    # Size and quantity information
    sizes = models.JSONField(default=dict)  # {"S": 2, "M": 1, "L": 3}
    quantity = models.PositiveIntegerField(default=1)  # Total quantity across all sizes
    price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['cart', 'design_id']
    
    def __str__(self):
        return f"{self.design_name or 'Design'} x{self.quantity}"
    
    @property
    def total_price(self):
        return self.price * self.quantity
    
    @property
    def is_guest_design(self):
        """Check if this is a guest design (non-numeric ID)"""
        try:
            int(self.design_id)
            return False
        except (ValueError, TypeError):
            return True
    
    @property
    def sizes_display(self):
        """Get human-readable sizes display"""
        if not self.sizes:
            return ""
        
        size_strings = []
        for size, qty in self.sizes.items():
            if qty > 0:
                size_strings.append(f"{qty}x {size}")
        return ", ".join(size_strings)
    
    def update_price(self):
        """Update price based on current quantity and product pricing"""
        from products.models import Product
        
        try:
            product = Product.objects.get(id=self.product_id)
            
            # Get appropriate price tier based on total quantity
            if product.prices:
                # Find the best price tier for this quantity
                available_qtys = [int(q) for q in product.prices.keys() if int(q) <= self.quantity]
                if available_qtys:
                    best_qty = max(available_qtys)
                    self.price = Decimal(str(product.prices[str(best_qty)]))
                else:
                    # Fallback to base price
                    self.price = Decimal(str(product.get_base_price()))
            else:
                self.price = Decimal(str(product.get_base_price()))
                
        except Product.DoesNotExist:
            # Fallback price if product not found
            self.price = Decimal('19.99')
    
    def add_size_quantity(self, size, quantity):
        """Add quantity for a specific size"""
        if not self.sizes:
            self.sizes = {}
        
        self.sizes[size] = self.sizes.get(size, 0) + quantity
        self.quantity = sum(self.sizes.values())
        self.update_price()
    
    def update_size_quantity(self, size, quantity):
        """Update quantity for a specific size"""
        if not self.sizes:
            self.sizes = {}
        
        if quantity <= 0:
            self.sizes.pop(size, None)
        else:
            self.sizes[size] = quantity
        
        self.quantity = sum(self.sizes.values())
        self.update_price()
    
    def save(self, *args, **kwargs):
        if not self.price or self.price == 0:
            self.update_price()
        super().save(*args, **kwargs)


class GuestCartManager:
    """Manager for handling guest cart operations using session"""
    
    @staticmethod
    def get_cart_from_session(request):
        """Get cart items from session"""
        return request.session.get('cart', [])
    
    @staticmethod
    def save_cart_to_session(request, cart_items):
        """Save cart items to session"""
        request.session['cart'] = cart_items
        request.session['cart_count'] = sum(item.get('quantity', 0) for item in cart_items)
    
    @staticmethod
    def add_to_session_cart(request, design_id, size, quantity, design_name='', 
                           thumbnail='', product_id=None):
        """Add item to session-based cart"""
        cart_items = GuestCartManager.get_cart_from_session(request)
        
        # Find existing item
        existing_item = None
        for item in cart_items:
            if item.get('design_id') == str(design_id):
                existing_item = item
                break
        
        if existing_item:
            # Update existing item
            sizes = existing_item.get('sizes', {})
            sizes[size] = sizes.get(size, 0) + quantity
            existing_item['sizes'] = sizes
            existing_item['quantity'] = sum(sizes.values())
        else:
            # Create new item
            cart_items.append({
                'design_id': str(design_id),
                'design_name': design_name,
                'thumbnail': thumbnail,
                'product_id': product_id,
                'sizes': {size: quantity},
                'quantity': quantity,
                'created_at': timezone.now().isoformat()
            })
        
        GuestCartManager.save_cart_to_session(request, cart_items)
    
    @staticmethod
    def update_session_cart_item(request, design_id, sizes):
        """Update sizes for a specific item in session cart"""
        cart_items = GuestCartManager.get_cart_from_session(request)
        
        for item in cart_items:
            if item.get('design_id') == str(design_id):
                item['sizes'] = sizes
                item['quantity'] = sum(sizes.values()) if sizes else 0
                break
        
        # Remove items with zero quantity
        cart_items = [item for item in cart_items if item.get('quantity', 0) > 0]
        
        GuestCartManager.save_cart_to_session(request, cart_items)
    
    @staticmethod
    def remove_from_session_cart(request, design_id):
        """Remove item from session cart"""
        cart_items = GuestCartManager.get_cart_from_session(request)
        cart_items = [item for item in cart_items if item.get('design_id') != str(design_id)]
        GuestCartManager.save_cart_to_session(request, cart_items)
    
    @staticmethod
    def clear_session_cart(request):
        """Clear all items from session cart"""
        request.session['cart'] = []
        request.session['cart_count'] = 0
    
    @staticmethod
    def migrate_to_user_cart(request, user):
        """Migrate session cart to user's database cart"""
        session_cart = GuestCartManager.get_cart_from_session(request)
        if not session_cart:
            return
        
        # Get or create user's cart
        cart, created = Cart.objects.get_or_create(user=user)
        
        # Merge session cart data
        cart.merge_with_session_cart(session_cart)
        
        # Clear session cart
        GuestCartManager.clear_session_cart(request)