from django.utils.deprecation import MiddlewareMixin
from django.http import Http404
from .models import Brand


class BrandMiddleware(MiddlewareMixin):
    """
    Middleware to detect brand from subdomain and attach to request
    """
    
    def process_request(self, request):
        # Get the host from the request
        host = request.get_host()
        
        # Extract subdomain
        subdomain = self.extract_subdomain(host)
        
        # Get brand based on subdomain
        request.brand = Brand.get_by_subdomain(subdomain)
        
        # Also store the subdomain for debugging/logging
        request.subdomain = subdomain
        
        return None
    
    def extract_subdomain(self, host):
        """
        Extract subdomain from host
        Examples:
        - 'localhost:8000' -> None
        - 'example.com' -> None  
        - 'brand1.example.com' -> 'brand1'
        - 'brand1.localhost:8000' -> 'brand1'
        """
        # Remove port if present
        if ':' in host:
            host = host.split(':')[0]
        
        # Split by dots
        parts = host.split('.')
        
        # If we have more than 2 parts (or more than 1 for localhost), 
        # treat first part as subdomain
        if len(parts) > 2 or (len(parts) > 1 and not parts[0] in ['localhost', '127', '0']):
            subdomain = parts[0]
            # Ignore common prefixes that aren't brand subdomains
            if subdomain.lower() not in ['www', 'api', 'admin']:
                return subdomain
        
        return None
    
    def process_response(self, request, response):
        """
        Add brand information to response headers for debugging
        """
        if hasattr(request, 'brand') and hasattr(request, 'subdomain'):
            if hasattr(response, '__setitem__'):  # Check if response supports headers
                response['X-Brand-Name'] = request.brand.name
                response['X-Brand-Subdomain'] = request.subdomain or 'default'
        
        return response