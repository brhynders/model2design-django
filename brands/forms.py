from django import forms
from django.utils.safestring import mark_safe
from .models import PartnerRequest


class PartnerRequestForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.label_suffix = ''  # Remove the colon after labels
        
        # Make asterisks red for required fields
        for field_name, field in self.fields.items():
            if field.required and '*' in field.label:
                field.label = mark_safe(field.label.replace('*', '<span class="text-danger">*</span>'))
    
    class Meta:
        model = PartnerRequest
        fields = [
            'business_name', 'website', 'business_type', 'expected_volume',
            'contact_name', 'email', 'phone',
            'facebook', 'instagram', 'twitter', 'linkedin',
            'message'
        ]
        widgets = {
            'business_name': forms.TextInput(attrs={
                'class': 'form-control',
                'required': True
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://'
            }),
            'business_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'expected_volume': forms.Select(attrs={
                'class': 'form-select'
            }),
            'contact_name': forms.TextInput(attrs={
                'class': 'form-control',
                'required': True
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'required': True
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'required': True
            }),
            'facebook': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://facebook.com/yourpage'
            }),
            'instagram': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://instagram.com/yourprofile'
            }),
            'twitter': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://twitter.com/yourhandle'
            }),
            'linkedin': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://linkedin.com/company/yourcompany'
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'What products are you interested in? What are your goals for the brand store?'
            })
        }
        labels = {
            'business_name': 'Business Name *',
            'website': 'Website',
            'business_type': 'Business Type',
            'expected_volume': 'Expected Monthly Volume',
            'contact_name': 'Contact Name *',
            'email': 'Email Address *',
            'phone': 'Phone Number *',
            'facebook': 'Facebook',
            'instagram': 'Instagram',
            'twitter': 'Twitter/X',
            'linkedin': 'LinkedIn',
            'message': 'Tell us about your needs'
        }