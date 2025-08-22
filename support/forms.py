from django import forms
from .models import SupportSubmission


class BaseSupportForm(forms.Form):
    """Base form with common fields for all support requests"""
    name = forms.CharField(max_length=255, widget=forms.TextInput(attrs={
        'class': 'form-control', 
        'required': True
    }))
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'form-control', 
        'required': True
    }))
    message = forms.CharField(widget=forms.Textarea(attrs={
        'class': 'form-control', 
        'rows': 4, 
        'required': True
    }))


class OrdersSupportForm(BaseSupportForm):
    """Form for order-related support requests"""
    order_number = forms.CharField(
        max_length=50, 
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'e.g., #12345'
        })
    )
    issue_type = forms.ChoiceField(
        choices=[
            ('', 'Select an issue type'),
            ('tracking', 'Order Tracking'),
            ('damaged', 'Damaged Product'),
            ('wrong', 'Wrong Item Received'),
            ('missing', 'Missing Items'),
            ('return', 'Return Request'),
            ('other', 'Other'),
        ],
        widget=forms.Select(attrs={'class': 'form-select', 'required': True})
    )


class AccountSupportForm(BaseSupportForm):
    """Form for account-related support requests"""
    issue_type = forms.ChoiceField(
        choices=[
            ('', 'Select an issue type'),
            ('login', "Can't Log In"),
            ('password', 'Password Reset'),
            ('email', 'Email Change'),
            ('delete', 'Delete Account'),
            ('other', 'Other'),
        ],
        widget=forms.Select(attrs={'class': 'form-select', 'required': True})
    )


class DesigningSupportForm(BaseSupportForm):
    """Form for design-related support requests"""
    issue_type = forms.ChoiceField(
        choices=[
            ('', 'Select an issue type'),
            ('upload', "Can't Upload Images"),
            ('save', "Can't Save Design"),
            ('editor', 'Editor Not Loading'),
            ('quality', 'Design Quality Issue'),
            ('custom_model', 'Request Custom Model'),
            ('features', 'Feature Request'),
            ('other', 'Other'),
        ],
        widget=forms.Select(attrs={'class': 'form-select', 'required': True})
    )
    product = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., T-Shirt, Mug'
        })
    )
    browser_info = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., Chrome on Windows 10'
        })
    )


class RequestModelForm(BaseSupportForm):
    """Form for 3D model requests"""
    model_type = forms.ChoiceField(
        choices=[
            ('', 'Select a model type'),
            ('apparel', 'Apparel (T-shirt, Hoodie, etc.)'),
            ('drinkware', 'Drinkware (Mug, Tumbler, etc.)'),
            ('accessories', 'Accessories (Hat, Bag, etc.)'),
            ('home_decor', 'Home Decor'),
            ('office', 'Office Supplies'),
            ('electronics', 'Electronics Accessories'),
            ('other', 'Other'),
        ],
        widget=forms.Select(attrs={'class': 'form-select', 'required': True})
    )
    model_name = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., V-neck T-shirt, 20oz Travel Mug',
            'required': True
        })
    )
    priority = forms.ChoiceField(
        choices=[
            ('normal', 'Normal'),
            ('high', 'High - Need ASAP'),
            ('low', 'Low - When convenient'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        initial='normal'
    )
    intended_use = forms.ChoiceField(
        choices=[
            ('personal', 'Personal Project'),
            ('business', 'Business/Commercial'),
            ('testing', 'Testing/Prototype'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        initial='personal'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['message'].widget.attrs.update({
            'placeholder': 'Please provide details about the model you need, including specific features, dimensions, or variations'
        })


class WebsiteProblemForm(BaseSupportForm):
    """Form for website problem reports"""
    page_url = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., /products or checkout page',
            'required': True
        })
    )
    browser = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., Chrome, Firefox, Safari',
            'required': True
        })
    )
    device = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., iPhone, Windows PC',
            'required': True
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['message'].widget.attrs.update({
            'placeholder': 'Please be as specific as possible'
        })


class GeneralSupportForm(BaseSupportForm):
    """Form for general inquiries"""
    subject = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'required': True
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['message'].widget.attrs['rows'] = 5


# Form mapping for easy access
SUPPORT_FORMS = {
    'orders': OrdersSupportForm,
    'account': AccountSupportForm,
    'designing': DesigningSupportForm,
    'request_model': RequestModelForm,
    'website': WebsiteProblemForm,
    'general': GeneralSupportForm,
}