from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.utils.crypto import get_random_string
from datetime import timedelta
import json

from .forms import (
    LoginForm, RegisterForm, ProfileUpdateForm, 
    PasswordChangeForm, ForgotPasswordForm, ResetPasswordForm
)
from .models import PasswordResetToken
from .utils import migrate_guest_data_to_user, get_guest_designs_count, get_guest_orders_count

User = get_user_model()


def login_view(request):
    """Handle user login"""
    # Redirect if already logged in
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    
    # Check for guest data
    guest_designs = get_guest_designs_count(request)
    guest_orders = get_guest_orders_count(request)
    
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            remember = form.cleaned_data.get('remember')
            
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                
                # Set session expiry based on remember me
                if not remember:
                    request.session.set_expiry(0)  # Browser close
                else:
                    request.session.set_expiry(1209600)  # 2 weeks
                
                # Migrate guest data
                migrated_count = migrate_guest_data_to_user(request, user)
                if migrated_count > 0:
                    messages.success(request, f"Welcome back! We've transferred {migrated_count} item(s) from your guest session to your account.")
                
                # Handle redirect
                next_url = request.GET.get('next', '')
                return_url = request.GET.get('return', '')
                redirect_url = request.GET.get('redirect', '')
                
                # Check for brand owner redirect
                if user.is_brand_owner:
                    # TODO: Implement brand redirect logic
                    pass
                
                if next_url:
                    return redirect(next_url)
                elif return_url:
                    # Handle designer URL with guest design ID mapping
                    if '/designer' in return_url and 'design=guest_' in return_url:
                        # TODO: Implement design ID mapping
                        pass
                    return redirect(return_url)
                elif redirect_url:
                    return redirect(redirect_url)
                else:
                    return redirect('accounts:dashboard')
    else:
        form = LoginForm()
    
    context = {
        'form': form,
        'guest_designs': guest_designs,
        'guest_orders': guest_orders,
        'page_title': 'Login'
    }
    return render(request, 'accounts/login.html', context)


def register_view(request):
    """Handle user registration"""
    # Redirect if already logged in
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    
    # Check for guest data
    guest_designs = get_guest_designs_count(request)
    guest_orders = get_guest_orders_count(request)
    
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Log the user in
            login(request, user)
            
            # Migrate guest data
            migrated_count = migrate_guest_data_to_user(request, user)
            if migrated_count > 0:
                messages.success(request, f"Account created! We've transferred {migrated_count} item(s) from your guest session.")
            
            # Handle redirect
            next_url = request.GET.get('next', '')
            return_url = request.GET.get('return', '')
            redirect_url = request.GET.get('redirect', '')
            
            if next_url:
                return redirect(next_url)
            elif return_url:
                # Handle designer URL with guest design ID mapping
                if '/designer' in return_url and 'design=guest_' in return_url:
                    # TODO: Implement design ID mapping
                    pass
                return redirect(return_url)
            elif redirect_url:
                return redirect(redirect_url)
            else:
                return redirect('accounts:dashboard')
    else:
        form = RegisterForm()
    
    context = {
        'form': form,
        'guest_designs': guest_designs,
        'guest_orders': guest_orders,
        'page_title': 'Register'
    }
    return render(request, 'accounts/register.html', context)


@login_required
def logout_view(request):
    """Handle user logout"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')


@login_required
def dashboard_view(request):
    """User dashboard"""
    user = request.user
    
    # TODO: Get current brand from session/context
    # current_brand = get_current_brand(request)
    
    # Get user statistics (placeholder for now)
    user_orders_count = 0  # TODO: Implement after orders app
    user_designs_count = 0  # TODO: Implement after designer app
    user_favorites_count = 0  # TODO: Implement favorites
    
    # Calculate member duration
    created_date = user.created_at if hasattr(user, 'created_at') else user.date_joined
    current_date = timezone.now()
    interval = current_date - created_date
    
    # Format member duration
    if interval.days > 365:
        years = interval.days // 365
        member_duration = f"{years} {'year' if years == 1 else 'years'}"
    elif interval.days > 30:
        months = interval.days // 30
        member_duration = f"{months} {'month' if months == 1 else 'months'}"
    else:
        member_duration = f"{interval.days} {'day' if interval.days == 1 else 'days'}"
    
    # Get recent orders and designs (placeholder)
    recent_orders = []  # TODO: Implement after orders app
    recent_designs = []  # TODO: Implement after designer app
    
    context = {
        'user': user,
        'user_orders_count': user_orders_count,
        'user_designs_count': user_designs_count,
        'user_favorites_count': user_favorites_count,
        'member_duration': member_duration,
        'recent_orders': recent_orders,
        'recent_designs': recent_designs,
        'page_title': 'Dashboard'
    }
    return render(request, 'accounts/dashboard.html', context)


@login_required
def profile_view(request):
    """User profile settings"""
    user = request.user
    success_message = ''
    error_message = ''
    
    if request.method == 'POST':
        if 'update_profile' in request.POST:
            # Update profile information
            profile_form = ProfileUpdateForm(request.POST, instance=user)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, 'Profile updated successfully!')
                return redirect('accounts:profile')
            else:
                for field, errors in profile_form.errors.items():
                    for error in errors:
                        messages.error(request, error)
        
        elif 'change_password' in request.POST:
            # Change password
            password_form = PasswordChangeForm(user, request.POST)
            if password_form.is_valid():
                new_password = password_form.cleaned_data['new_password']
                user.set_password(new_password)
                user.save()
                update_session_auth_hash(request, user)  # Keep user logged in
                messages.success(request, 'Password changed successfully!')
                return redirect('accounts:profile')
            else:
                for field, errors in password_form.errors.items():
                    for error in errors:
                        messages.error(request, error)
    
    # Initialize forms
    profile_form = ProfileUpdateForm(instance=user)
    password_form = PasswordChangeForm(user)
    
    context = {
        'user': user,
        'profile_form': profile_form,
        'password_form': password_form,
        'page_title': 'Profile Settings'
    }
    return render(request, 'accounts/profile.html', context)


def forgot_password_view(request):
    """Handle password reset request"""
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            
            # Always show success message for security (don't reveal if email exists)
            try:
                user = User.objects.get(email=email)
                
                # Generate reset token only if user exists
                token = get_random_string(64)
                reset_token = PasswordResetToken.objects.create(
                    user=user,
                    token=token
                )
                
                # Send reset email
                reset_url = request.build_absolute_uri(
                    reverse('accounts:reset_password') + f'?token={token}'
                )
                
                # TODO: Implement email sending
                # send_mail(
                #     'Password Reset Request',
                #     f'Click here to reset your password: {reset_url}',
                #     settings.DEFAULT_FROM_EMAIL,
                #     [email],
                #     fail_silently=False,
                # )
                
            except User.DoesNotExist:
                # Don't reveal that the email doesn't exist - just silently continue
                pass
            
            # Always show success message regardless of whether email exists
            messages.success(request, 'If an account with that email address exists, we\'ve sent you a password reset link. Please check your email.')
            return redirect('accounts:login')
    else:
        form = ForgotPasswordForm()
    
    context = {
        'form': form,
        'page_title': 'Forgot Password'
    }
    return render(request, 'accounts/forgot_password.html', context)


def reset_password_view(request):
    """Handle password reset with token"""
    token = request.GET.get('token', '')
    
    if not token:
        messages.error(request, 'Invalid reset link.')
        return redirect('accounts:login')
    
    try:
        reset_token = PasswordResetToken.objects.get(
            token=token,
            used=False,
            created_at__gte=timezone.now() - timedelta(hours=1)
        )
    except PasswordResetToken.DoesNotExist:
        messages.error(request, 'Invalid or expired reset link.')
        return redirect('accounts:login')
    
    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data['password']
            user = reset_token.user
            user.set_password(new_password)
            user.save()
            
            # Mark token as used
            reset_token.used = True
            reset_token.save()
            
            messages.success(request, 'Password reset successfully. You can now login with your new password.')
            return redirect('accounts:login')
    else:
        form = ResetPasswordForm()
    
    context = {
        'form': form,
        'token': token,
        'page_title': 'Reset Password'
    }
    return render(request, 'accounts/reset_password.html', context)
