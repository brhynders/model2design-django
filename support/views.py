from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.generic import TemplateView
from django.views import View
from .models import SupportSubmission, FAQ, Tutorial
from .forms import SUPPORT_FORMS


class SupportView(TemplateView):
    template_name = 'support/support.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['faqs'] = FAQ.objects.filter(is_active=True)
        
        # Pre-populate user data if authenticated
        initial_data = {}
        if self.request.user.is_authenticated:
            initial_data = {
                'name': f"{self.request.user.first_name} {self.request.user.last_name}".strip(),
                'email': self.request.user.email,
            }
        
        # Create all form instances
        context['forms'] = {
            'orders': SUPPORT_FORMS['orders'](initial=initial_data),
            'account': SUPPORT_FORMS['account'](initial=initial_data),
            'designing': SUPPORT_FORMS['designing'](initial=initial_data),
            'request_model': SUPPORT_FORMS['request_model'](initial=initial_data),
            'website': SUPPORT_FORMS['website'](initial=initial_data),
            'general': SUPPORT_FORMS['general'](initial=initial_data),
        }
        
        return context


class SupportSubmitView(View):
    def post(self, request):
        category = request.POST.get('category', 'general')
        
        # Get the appropriate form class for this category
        form_class = SUPPORT_FORMS.get(category, SUPPORT_FORMS['general'])
        form = form_class(request.POST)
        
        if form.is_valid():
            # Get cleaned data
            cleaned_data = form.cleaned_data
            name = cleaned_data['name']
            email = cleaned_data['email']
            message = cleaned_data['message']
            
            # Build subject based on category and form data
            subject = self._build_subject(cleaned_data, category)
            
            # Collect additional form data (excluding standard fields)
            additional_data = {}
            exclude_fields = {'name', 'email', 'message'}
            for key, value in cleaned_data.items():
                if key not in exclude_fields and value:
                    additional_data[key] = value
            
            try:
                submission = SupportSubmission.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    name=name,
                    email=email,
                    subject=subject,
                    message=message,
                    category=category,
                    additional_data=additional_data if additional_data else None
                )
                messages.success(request, 'Your support request has been submitted successfully!')
                return redirect('support:support')
            except Exception as e:
                messages.error(request, 'There was an error submitting your request. Please try again.')
                return redirect('support:support')
        else:
            # Form validation failed
            error_messages = []
            for field, errors in form.errors.items():
                for error in errors:
                    if field == '__all__':
                        error_messages.append(error)
                    else:
                        field_name = form.fields[field].label or field.replace('_', ' ').title()
                        error_messages.append(f"{field_name}: {error}")
            
            if error_messages:
                messages.error(request, f"Please correct the following errors: {'; '.join(error_messages)}")
            else:
                messages.error(request, 'Please fill in all required fields.')
            return redirect('support:support')
    
    def _build_subject(self, post_data, category):
        """Build an appropriate subject line based on the form category and data"""
        if category == 'orders':
            issue_type = post_data.get('issue_type', 'Order Issue')
            order_number = post_data.get('order_number', '')
            if order_number:
                return f"Order Support - {issue_type} (Order: {order_number})"
            else:
                return f"Order Support - {issue_type}"
        
        elif category == 'account':
            issue_type = post_data.get('issue_type', 'Account Issue')
            return f"Account Support - {issue_type}"
        
        elif category == 'designing':
            issue_type = post_data.get('issue_type', 'Design Issue')
            product = post_data.get('product', '')
            if product:
                return f"Design Support - {issue_type} ({product})"
            else:
                return f"Design Support - {issue_type}"
        
        elif category == 'request_model':
            model_type = post_data.get('model_type', 'Model Request')
            model_name = post_data.get('model_name', '')
            priority = post_data.get('priority', 'normal')
            if model_name:
                return f"Model Request - {model_name} ({model_type}) - Priority: {priority.title()}"
            else:
                return f"Model Request - {model_type} - Priority: {priority.title()}"
        
        elif category == 'website':
            page_url = post_data.get('page_url', 'Unknown Page')
            browser = post_data.get('browser', 'Unknown Browser')
            return f"Website Problem - {page_url} ({browser})"
        
        elif category == 'general':
            subject = post_data.get('subject', 'General Inquiry')
            return subject
        
        else:
            return f"Support Request - {category.title()}"


class PrivacyPolicyView(TemplateView):
    template_name = 'support/privacy_policy.html'


class TermsOfServiceView(TemplateView):
    template_name = 'support/terms_of_service.html'


class ReturnPolicyView(TemplateView):
    template_name = 'support/return_policy.html'


class ShippingInfoView(TemplateView):
    template_name = 'support/shipping_info.html'


class TutorialsView(TemplateView):
    template_name = 'support/tutorials.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tutorials'] = Tutorial.objects.filter(is_active=True)
        return context


class TutorialDetailView(TemplateView):
    template_name = 'support/tutorial_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context['tutorial'] = Tutorial.objects.get(
                slug=kwargs['slug'], 
                is_active=True
            )
        except Tutorial.DoesNotExist:
            context['tutorial'] = None
        return context
