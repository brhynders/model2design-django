"""
Custom storage backends for Cloudflare R2
"""
from storages.backends.s3boto3 import S3Boto3Storage
from django.conf import settings


class R2MediaStorage(S3Boto3Storage):
    """
    Custom storage class for Cloudflare R2 media files
    """
    # Override the default domain to use R2's public URL if needed
    # This ensures proper URLs are generated for your media files
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    access_key = settings.AWS_ACCESS_KEY_ID
    secret_key = settings.AWS_SECRET_ACCESS_KEY
    endpoint_url = settings.AWS_S3_ENDPOINT_URL
    region_name = settings.AWS_S3_REGION_NAME
    location = 'media'
    file_overwrite = False
    default_acl = None  # R2 doesn't use ACLs like S3
    querystring_auth = False  # Don't add auth to URLs for public files
    
    def get_object_parameters(self, name):
        """
        Override to set custom parameters for uploaded objects
        """
        params = super().get_object_parameters(name)
        # Add cache control for better performance
        params['CacheControl'] = 'max-age=86400'  # 1 day cache
        return params


class R2StaticStorage(S3Boto3Storage):
    """
    Custom storage class for Cloudflare R2 static files (optional)
    """
    location = 'static'
    default_acl = None
    
    def get_object_parameters(self, name):
        params = super().get_object_parameters(name)
        # Longer cache for static files
        params['CacheControl'] = 'max-age=31536000'  # 1 year cache
        return params