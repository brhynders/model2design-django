from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils.html import format_html
from decimal import Decimal
import json

from .models import Cart, CartItem, GuestCartManager
from products.models import Product


class CartView(View):
    def get(self, request):
        cart_items = []
        subtotal = Decimal('0.00')
        products_data = []
        
        # Get products for JavaScript modal
        products_list = Product.objects.all()
        for product in products_list:
            products_data.append({
                'id': product.id,
                'name': product.name,
                'sizes': product.sizes or [],
                'prices': product.prices or {}
            })
        
        if request.user.is_authenticated:
            # Get user's cart
            try:
                cart = Cart.objects.get(user=request.user)
                cart_items_qs = cart.items.all()
                
                # Convert to template-friendly format
                for item in cart_items_qs:
                    try:
                        product = Product.objects.get(id=item.product_id)
                        cart_items.append({
                            'id': item.id,
                            'design_id': item.design_id,
                            'design_name': item.design_name,
                            'product_name': product.name,
                            'thumbnail': item.thumbnail,
                            'quantity': item.quantity,
                            'price': item.price,
                            'total_price': item.total_price,
                            'sizes_display': item.sizes_display,
                            'json_data': json.dumps({
                                'design_id': item.design_id,
                                'design_name': item.design_name,
                                'product_id': item.product_id,
                                'sizes': item.sizes
                            })
                        })
                        subtotal += item.total_price
                    except Product.DoesNotExist:
                        continue
                        
            except Cart.DoesNotExist:
                pass
        else:
            # Get guest cart from session
            session_cart = GuestCartManager.get_cart_from_session(request)
            
            for item in session_cart:
                try:
                    product = Product.objects.get(id=item.get('product_id'))
                    
                    # Calculate price based on quantity
                    quantity = item.get('quantity', 1)
                    price = self.get_product_price(product, quantity)
                    total_price = price * quantity
                    
                    # Build sizes display
                    sizes_display = ""
                    sizes = item.get('sizes', {})
                    if sizes:
                        size_strings = []
                        for size, qty in sizes.items():
                            if qty > 0:
                                size_strings.append(f"{qty}x {size}")
                        sizes_display = ", ".join(size_strings)
                    
                    cart_items.append({
                        'id': f"guest_{item.get('design_id')}",
                        'design_id': item.get('design_id'),
                        'design_name': item.get('design_name', ''),
                        'product_name': product.name,
                        'thumbnail': item.get('thumbnail', ''),
                        'quantity': quantity,
                        'price': price,
                        'total_price': total_price,
                        'sizes_display': sizes_display,
                        'json_data': json.dumps({
                            'design_id': item.get('design_id'),
                            'design_name': item.get('design_name', ''),
                            'product_id': item.get('product_id'),
                            'sizes': sizes
                        })
                    })
                    subtotal += total_price
                except Product.DoesNotExist:
                    continue
        
        shipping = Decimal('15.00')
        total = subtotal + shipping
        
        context = {
            'cart_items': cart_items,
            'subtotal': subtotal,
            'shipping': shipping,
            'total': total,
            'products_json': json.dumps(products_data)
        }
        
        return render(request, 'cart/cart.html', context)
    
    def post(self, request):
        action = request.POST.get('action')
        item_id = request.POST.get('item_id')
        
        if action == 'update_sizes':
            return self.update_sizes(request)
        elif action == 'remove':
            return self.remove_item(request, item_id)
        elif action == 'clear':
            return self.clear_cart(request)
        
        messages.error(request, 'Invalid action')
        return redirect('cart:view')
    
    def get_product_price(self, product, quantity):
        """Get appropriate price tier for quantity"""
        if not product.prices:
            return Decimal(str(product.get_base_price()))
        
        # Find the best price tier for this quantity
        available_qtys = [int(q) for q in product.prices.keys() if int(q) <= quantity]
        if available_qtys:
            best_qty = max(available_qtys)
            return Decimal(str(product.prices[str(best_qty)]))
        else:
            return Decimal(str(product.get_base_price()))
    
    def update_sizes(self, request):
        """Update sizes for a cart item"""
        item_id = request.POST.get('item_id')
        sizes_json = request.POST.get('sizes', '{}')
        
        try:
            sizes = json.loads(sizes_json)
            # Filter out zero quantities
            sizes = {size: qty for size, qty in sizes.items() if qty > 0}
            
            if request.user.is_authenticated:
                # Update database cart item
                if item_id.isdigit():
                    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
                    
                    if not sizes:
                        # Remove item if no sizes have quantity
                        cart_item.delete()
                    else:
                        # Update sizes and recalculate
                        cart_item.sizes = sizes
                        cart_item.quantity = sum(sizes.values())
                        cart_item.update_price()
                        cart_item.save()
            else:
                # Update session cart
                design_id = item_id.replace('guest_', '') if item_id.startswith('guest_') else item_id
                GuestCartManager.update_session_cart_item(request, design_id, sizes)
            
            messages.success(request, 'Cart updated successfully')
            
        except (json.JSONDecodeError, ValueError) as e:
            messages.error(request, 'Invalid size data')
        
        return redirect('cart:view')
    
    def remove_item(self, request, item_id):
        """Remove item from cart"""
        if request.user.is_authenticated:
            if item_id and item_id.isdigit():
                try:
                    cart_item = CartItem.objects.get(id=item_id, cart__user=request.user)
                    cart_item.delete()
                    messages.success(request, 'Item removed from cart')
                except CartItem.DoesNotExist:
                    messages.error(request, 'Item not found')
        else:
            # Remove from session cart
            design_id = item_id.replace('guest_', '') if item_id.startswith('guest_') else item_id
            GuestCartManager.remove_from_session_cart(request, design_id)
            messages.success(request, 'Item removed from cart')
        
        return redirect('cart:view')
    
    def clear_cart(self, request):
        """Clear all items from cart"""
        if request.user.is_authenticated:
            try:
                cart = Cart.objects.get(user=request.user)
                cart.clear()
                messages.success(request, 'Cart cleared')
            except Cart.DoesNotExist:
                pass
        else:
            GuestCartManager.clear_session_cart(request)
            messages.success(request, 'Cart cleared')
        
        return redirect('cart:view')


@require_http_methods(["POST"])
def add_to_cart(request):
    """Add item to cart - handles both AJAX and form submissions"""
    try:
        design_id = request.POST.get('design_id')
        size = request.POST.get('size')
        quantity = int(request.POST.get('quantity', 1))
        
        if not design_id or not size:
            if request.headers.get('Content-Type') == 'application/json' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': 'Missing required fields'})
            else:
                messages.error(request, 'Missing required fields')
                return redirect('products:list')
        
        # Get design data (placeholder - will need actual design model integration)
        design_data = {
            'id': design_id,
            'name': f'Design {design_id}',
            'product_id': 1,  # Default product for now
            'thumbnail': ''
        }
        
        # Get product info
        try:
            product = Product.objects.get(id=design_data['product_id'])
        except Product.DoesNotExist:
            if request.headers.get('Content-Type') == 'application/json' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': 'Product not found'})
            else:
                messages.error(request, 'Product not found')
                return redirect('products:list')
        
        # Validate size
        if size not in product.sizes:
            if request.headers.get('Content-Type') == 'application/json' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': 'Invalid size selected'})
            else:
                messages.error(request, 'Invalid size selected')
                return redirect('products:list')
        
        if request.user.is_authenticated:
            # Add to database cart
            cart, created = Cart.objects.get_or_create(user=request.user)
            
            # Check if design already in cart
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                design_id=design_id,
                defaults={
                    'design_name': design_data['name'],
                    'thumbnail': design_data['thumbnail'],
                    'product_id': product.id,
                    'sizes': {size: quantity},
                    'quantity': quantity
                }
            )
            
            if not created:
                # Update existing item
                cart_item.add_size_quantity(size, quantity)
                cart_item.save()
        else:
            # Add to session cart
            GuestCartManager.add_to_session_cart(
                request,
                design_id=design_id,
                size=size,
                quantity=quantity,
                design_name=design_data['name'],
                thumbnail=design_data['thumbnail'],
                product_id=product.id
            )
        
        if request.headers.get('Content-Type') == 'application/json' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'Added to cart successfully'})
        else:
            messages.success(request, 'Added to cart successfully')
            return redirect('cart:view')
            
    except (ValueError, KeyError) as e:
        if request.headers.get('Content-Type') == 'application/json' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})
        else:
            messages.error(request, f'Error: {str(e)}')
            return redirect('products:list')


def cart_sidebar(request):
    """API endpoint for cart sidebar content"""
    cart_items = []
    cart_total = Decimal('0.00')
    
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            cart_items_qs = cart.items.all()[:5]  # Limit to 5 items for sidebar
            
            for item in cart_items_qs:
                try:
                    product = Product.objects.get(id=item.product_id)
                    cart_items.append({
                        'design_name': item.design_name,
                        'product_name': product.name,
                        'thumbnail': item.thumbnail,
                        'quantity': item.quantity,
                        'price': float(item.price),
                        'total': float(item.total_price),
                        'sizes_display': item.sizes_display
                    })
                    cart_total += item.total_price
                except Product.DoesNotExist:
                    continue
                    
        except Cart.DoesNotExist:
            pass
    else:
        # Get from session
        session_cart = GuestCartManager.get_cart_from_session(request)[:5]
        
        for item in session_cart:
            try:
                product = Product.objects.get(id=item.get('product_id'))
                quantity = item.get('quantity', 1)
                
                # Calculate price
                if product.prices:
                    available_qtys = [int(q) for q in product.prices.keys() if int(q) <= quantity]
                    if available_qtys:
                        best_qty = max(available_qtys)
                        price = Decimal(str(product.prices[str(best_qty)]))
                    else:
                        price = Decimal(str(product.get_base_price()))
                else:
                    price = Decimal(str(product.get_base_price()))
                
                total_price = price * quantity
                
                # Build sizes display
                sizes_display = ""
                sizes = item.get('sizes', {})
                if sizes:
                    size_strings = []
                    for size, qty in sizes.items():
                        if qty > 0:
                            size_strings.append(f"{qty}x {size}")
                    sizes_display = ", ".join(size_strings)
                
                cart_items.append({
                    'design_name': item.get('design_name', ''),
                    'product_name': product.name,
                    'thumbnail': item.get('thumbnail', ''),
                    'quantity': quantity,
                    'price': float(price),
                    'total': float(total_price),
                    'sizes_display': sizes_display
                })
                cart_total += total_price
                
            except Product.DoesNotExist:
                continue
    
    shipping = Decimal('15.00')
    grand_total = cart_total + shipping
    
    context = {
        'cart_items': cart_items,
        'cart_total': float(cart_total),
        'shipping': float(shipping),
        'grand_total': float(grand_total),
        'cart_count': len(cart_items)
    }
    
    return render(request, 'cart/cart_sidebar.html', context)