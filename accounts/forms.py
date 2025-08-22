from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
import re

User = get_user_model()

class LoginForm(AuthenticationForm):
    """Custom login form matching PHP styling"""
    username = forms.EmailField(
        label='Email address',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'id': 'email',
            'required': True,
            'autofocus': True
        })
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'id': 'password',
            'required': True
        })
    )
    remember = forms.BooleanField(
        label='Remember me',
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'remember'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove default labels as we'll use them in template
        self.fields['username'].error_messages = {'required': 'Please enter your email address'}
        self.fields['password'].error_messages = {'required': 'Please enter your password'}


class RegisterForm(UserCreationForm):
    """Custom registration form matching PHP styling"""
    name = forms.CharField(
        label='Full Name',
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'name',
            'required': True,
            'autofocus': True
        })
    )
    email = forms.EmailField(
        label='Email address',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'id': 'email',
            'required': True
        })
    )
    phone = forms.CharField(
        label='Phone Number',
        max_length=14,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'phone',
            'placeholder': '(123) 456-7890',
            'maxlength': '14',
            'required': True
        })
    )
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'id': 'password',
            'required': True
        })
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'id': 'confirm_password',
            'required': True
        })
    )
    
    class Meta:
        model = User
        fields = ('name', 'email', 'phone', 'password1', 'password2')
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('This email is already registered')
        return email
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        # Strip all non-digits
        phone_digits = re.sub(r'\D', '', phone)
        if len(phone_digits) != 10:
            raise ValidationError('Please enter a valid 10-digit phone number')
        return phone_digits
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']
        user.email = self.cleaned_data['email']
        user.name = self.cleaned_data['name']
        user.phone = self.cleaned_data['phone']
        if commit:
            user.save()
        return user


class ProfileUpdateForm(forms.ModelForm):
    """Form for updating user profile"""
    name = forms.CharField(
        label='Full Name',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'name',
            'required': True
        })
    )
    email = forms.EmailField(
        label='Email Address',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'id': 'email',
            'required': True
        })
    )
    phone = forms.CharField(
        label='Phone Number',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'phone',
            'placeholder': '(123) 456-7890'
        })
    )
    
    class Meta:
        model = User
        fields = ('name', 'email', 'phone')
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError('This email is already in use by another account')
        return email


class PasswordChangeForm(forms.Form):
    """Form for changing password"""
    current_password = forms.CharField(
        label='Current Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'id': 'current_password',
            'required': True
        })
    )
    new_password = forms.CharField(
        label='New Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'id': 'new_password',
            'required': True
        })
    )
    confirm_password = forms.CharField(
        label='Confirm New Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'id': 'confirm_password',
            'required': True
        })
    )
    
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
    
    def clean_current_password(self):
        current_password = self.cleaned_data.get('current_password')
        if not self.user.check_password(current_password):
            raise ValidationError('Current password is incorrect')
        return current_password
    
    def clean_new_password(self):
        new_password = self.cleaned_data.get('new_password')
        if len(new_password) < 6:
            raise ValidationError('Password must be at least 6 characters long')
        return new_password
    
    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if new_password and confirm_password and new_password != confirm_password:
            raise ValidationError('New passwords do not match')
        
        return cleaned_data


class ForgotPasswordForm(forms.Form):
    """Form for password reset request"""
    email = forms.EmailField(
        label='Email Address',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'id': 'email',
            'required': True,
            'autofocus': True
        })
    )


class ResetPasswordForm(forms.Form):
    """Form for resetting password with token"""
    password = forms.CharField(
        label='New Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'id': 'password',
            'required': True
        })
    )
    confirm_password = forms.CharField(
        label='Confirm New Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'id': 'confirm_password',
            'required': True
        })
    )
    
    def clean_password(self):
        password = self.cleaned_data.get('password')
        if len(password) < 6:
            raise ValidationError('Password must be at least 6 characters long')
        return password
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password and confirm_password and password != confirm_password:
            raise ValidationError('Passwords do not match')
        
        return cleaned_data