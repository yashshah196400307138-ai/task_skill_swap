from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import CreateView, UpdateView, DetailView, TemplateView
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect, JsonResponse
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.sites.shortcuts import get_current_site
from django.utils.crypto import get_random_string
from django.conf import settings
from django.views import View
from django.views.decorators.http import require_http_methods
from core.models import Department, Branch

from .models import UserProfile, Notification
from .forms import UserProfileForm, ForgotPasswordForm, OTPVerificationForm, PasswordResetForm

# Create your views here.

class RegisterView(CreateView):
    """User registration view"""
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('accounts:login')
    
    def get_form_class(self):
        from .forms import UserRegistrationForm
        return UserRegistrationForm
    
    def form_valid(self, form):
        response = super().form_valid(form)
        # Create user profile with university_email, department, branch, year, bio, and availability
        university_email = form.cleaned_data.get('university_email')
        department = form.cleaned_data.get('department')
        branch = form.cleaned_data.get('branch')
        year = form.cleaned_data.get('year')
        bio = form.cleaned_data.get('bio')
        availability = form.cleaned_data.get('availability')
        UserProfile.objects.create(
            user=form.instance,
            university_email=university_email,
            department=department,
            branch=branch,
            year=year,
            bio=bio,
            availability=availability
        )
        messages.success(self.request, 'Registration successful! Please log in.')
        return response


class ProfileView(LoginRequiredMixin, DetailView):
    """Display user profile"""
    model = UserProfile
    template_name = 'accounts/profile.html'
    context_object_name = 'profile'
    
    def get_object(self):
        # If user_id is provided in URL, show that user's profile
        if 'user_id' in self.kwargs:
            User = get_user_model()
            user = get_object_or_404(User, id=self.kwargs['user_id'])
            return user.profile
        # Otherwise show current user's profile
        return self.request.user.profile
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = self.get_object()
        context['completion_percentage'] = profile.get_completion_percentage()
        context['is_own_profile'] = profile.user == self.request.user
        return context


class ProfileEditView(LoginRequiredMixin, UpdateView):
    """Edit user profile"""
    model = UserProfile
    template_name = 'accounts/profile_edit.html'
    success_url = reverse_lazy('accounts:profile')
    form_class = UserProfileForm
    
    def get_object(self):
        return self.request.user.profile
    
    def form_valid(self, form):
        messages.success(self.request, 'Profile updated successfully!')
        return super().form_valid(form)


class ProfileCompleteView(LoginRequiredMixin, TemplateView):
    """Profile completion wizard"""
    template_name = 'accounts/profile_complete.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = self.request.user.profile
        context['profile'] = profile
        context['completion_percentage'] = profile.get_completion_percentage()
        return context


class VerifyEmailView(TemplateView):
    """Email verification view"""
    template_name = 'accounts/verify_email.html'
    
    def get(self, request, *args, **kwargs):
        token = request.GET.get('token')
        if token:
            return self.verify_email(request, token)
        return super().get(request, *args, **kwargs)
    
    def verify_email(self, request, token):
        try:
            uidb64 = token.split('.')[0]
            uid = force_str(urlsafe_base64_decode(uidb64))
            from django.contrib.auth.models import User
            user = User.objects.get(pk=uid)
            profile = user.profile
            profile.is_verified = True
            profile.save()
            messages.success(request, 'Email verified successfully!')
            return redirect('accounts:profile')
        except:
            messages.error(request, 'Invalid verification link.')
            return redirect('accounts:login')


class EmailVerificationSentView(TemplateView):
    """Email verification sent confirmation"""
    template_name = 'accounts/email_verification_sent.html'


@login_required
def mark_notification_read(request, notification_id):
    """Mark notification as read"""
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notification.is_read = True
    notification.save()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse_lazy('accounts:profile')))


User = get_user_model()

class ForgotPasswordView(View):
    template_name = 'accounts/forgot_password.html'
    def get(self, request):
        return render(request, self.template_name, {'form': ForgotPasswordForm()})
    def post(self, request):
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            otp = get_random_string(6, allowed_chars='0123456789')
            request.session['reset_email'] = email
            request.session['reset_otp'] = otp
            # Send OTP via email (console backend for now)
            send_mail(
                'Your OTP for Password Reset',
                f'Your OTP is: {otp}',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            messages.success(request, 'An OTP has been sent to your email.')
            return redirect('accounts:verify_otp')
        return render(request, self.template_name, {'form': form})

class OTPVerificationView(View):
    template_name = 'accounts/verify_otp.html'
    def get(self, request):
        if not request.session.get('reset_email'):
            return redirect('accounts:forgot_password')
        return render(request, self.template_name, {'form': OTPVerificationForm()})
    def post(self, request):
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            otp = form.cleaned_data['otp']
            session_otp = request.session.get('reset_otp')
            if otp == session_otp:
                request.session['otp_verified'] = True
                return redirect('accounts:reset_password')
            else:
                form.add_error('otp', 'Invalid OTP. Please try again.')
        return render(request, self.template_name, {'form': form})

class PasswordResetView(View):
    template_name = 'accounts/reset_password.html'
    def get(self, request):
        if not (request.session.get('reset_email') and request.session.get('otp_verified')):
            return redirect('accounts:forgot_password')
        return render(request, self.template_name, {'form': PasswordResetForm()})
    def post(self, request):
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            email = request.session.get('reset_email')
            new_password = form.cleaned_data['new_password']
            try:
                user = User.objects.get(email=email)
                user.set_password(new_password)
                user.save()
                # Clear session
                request.session.pop('reset_email', None)
                request.session.pop('reset_otp', None)
                request.session.pop('otp_verified', None)
                # Log the user in
                user = authenticate(request, username=user.username, password=new_password)
                if user:
                    login(request, user)
                messages.success(request, 'Password reset successful! You are now logged in.')
                return redirect('core:dashboard')
            except User.DoesNotExist:
                messages.error(request, 'User not found.')
                return redirect('accounts:forgot_password')
        return render(request, self.template_name, {'form': form})


@require_http_methods(["GET"])
def get_branches(request):
    """AJAX endpoint to get branches for a selected department"""
    department_id = request.GET.get('department_id')
    
    if not department_id:
        return JsonResponse({'branches': []})
    
    try:
        department = Department.objects.get(id=department_id, is_active=True)
        branches = department.branches.filter(is_active=True).values('id', 'name')
        branches_list = list(branches)
        return JsonResponse({'branches': branches_list})
    except Department.DoesNotExist:
        return JsonResponse({'branches': []})
