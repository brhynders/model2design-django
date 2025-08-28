from designer.models import Design, DesignImage
from cart.models import Cart


def guest_data_context(request):
    """Check if guest has any data (designs, images, or cart items)"""
    has_guest_data = False
    
    if not request.user.is_authenticated:
        # Check for session key
        session_key = request.session.session_key
        
        if session_key:
            # Check for guest designs
            has_designs = Design.objects.filter(session_id=session_key).exists()
            
            # Check for guest images
            has_images = DesignImage.objects.filter(session_id=session_key).exists()
            
            # Check for guest cart items (Cart model uses session_key, not session_id)
            has_cart_items = Cart.objects.filter(session_key=session_key).exists()
            
            # Set flag if any data exists
            has_guest_data = has_designs or has_images or has_cart_items
    
    return {
        'has_guest_data': has_guest_data
    }