"""Utility functions for accounts app"""
from django.contrib.auth import get_user_model

User = get_user_model()


def migrate_guest_data_to_user(request, user):
    """
    Migrate guest session data to authenticated user
    Returns the count of migrated items
    """
    migrated_count = 0
    
    # Migrate cart items
    try:
        from cart.models import GuestCartManager
        session_cart = GuestCartManager.get_cart_from_session(request)
        if session_cart:
            GuestCartManager.migrate_to_user_cart(request, user)
            migrated_count += len(session_cart)
    except ImportError:
        # Cart app not available yet
        pass
    
    # TODO: Implement other migration logic when apps are ready:
    # - Guest designs to user designs
    # - Guest orders to user orders  
    # - Guest images to user images
    
    # Clear guest session data after migration
    if 'guest_designs' in request.session:
        del request.session['guest_designs']
    if 'guest_cart' in request.session:
        del request.session['guest_cart']
    if 'guest_orders' in request.session:
        del request.session['guest_orders']
    
    # Store design ID mapping for redirect handling
    if 'design_id_mapping' not in request.session:
        request.session['design_id_mapping'] = {}
    
    return migrated_count


def get_guest_designs_count(request):
    """Get count of guest designs in session"""
    guest_designs = request.session.get('guest_designs', [])
    return len(guest_designs) if isinstance(guest_designs, list) else 0


def get_guest_orders_count(request):
    """Get count of guest orders in session"""
    guest_orders = request.session.get('guest_orders', [])
    return len(guest_orders) if isinstance(guest_orders, list) else 0


def is_valid_redirect_url(url):
    """Validate that a redirect URL is safe (internal only)"""
    if not url:
        return False
    # Only allow relative URLs starting with /
    return url.startswith('/') and not url.startswith('//')