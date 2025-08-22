from .models import Cart, GuestCartManager


def cart_context(request):
    """Add cart information to template context"""
    cart_count = 0
    
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            cart_count = cart.total_items
        except Cart.DoesNotExist:
            cart_count = 0
    else:
        # Get from session
        cart_count = request.session.get('cart_count', 0)
    
    return {
        'cart_count': cart_count
    }