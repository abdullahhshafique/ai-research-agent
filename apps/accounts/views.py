# apps/accounts/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth import get_user_model
from django.db.models import Count, Q, Max
from django.core.paginator import Paginator
from django.contrib.admin.views.decorators import staff_member_required

from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings

from .forms import RegisterForm, LoginForm, ProfileForm

User = get_user_model()


def home_view(request):
    """Home/landing page."""
    return render(request, 'pages/home.html')


def register_view(request):
    """User registration."""
    if request.user.is_authenticated:
        return redirect('accounts:home')
    
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('accounts:home')
    else:
        form = RegisterForm()
    
    return render(request, 'pages/accounts/register.html', {'form': form})


def login_view(request):
    """User login."""
    if request.user.is_authenticated:
        return redirect('accounts:home')
    
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            next_url = request.GET.get('next', 'accounts:home')
            return redirect(next_url)
    else:
        form = LoginForm()
    
    return render(request, 'pages/accounts/login.html', {'form': form})


@login_required
def logout_view(request):
    """User logout."""
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('accounts:home')


@login_required
def verify_email_send(request):
    """Queue a verification email (or display the link if console backend)."""
    user = request.user
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    verify_url = request.build_absolute_uri(f"/accounts/verify-email/{uid}/{token}/")
    profile = user.profile

    if settings.EMAIL_BACKEND != 'django.core.mail.backends.console.EmailBackend':
        send_mail(
            subject='Verify your email — AI Research Agent',
            message=f'Click to verify: {verify_url}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        messages.success(request, f'Verification email sent to {user.email}.')
    else:
        messages.info(request, f'Console backend — verification link: {verify_url}')

    return redirect('accounts:profile')


@login_required
def verify_email_confirm(request, uidb64, token):
    """Consume the verification token and flip `email_verified`."""
    try:
        user_id = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=user_id)
    except (User.DoesNotExist, ValueError, TypeError):
        messages.error(request, 'Verification link is invalid.')
        return redirect('accounts:profile')

    if default_token_generator.check_token(user, token):
        user.profile.email_verified = True
        user.profile.save(update_fields=['email_verified'])
        messages.success(request, 'Email verified successfully.')
    else:
        messages.error(request, 'Verification link expired or already used.')

    return redirect('accounts:profile')


@login_required
def profile_view(request):
    """User profile management."""
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user.profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:profile')
    else:
        form = ProfileForm(instance=request.user.profile)
    
    return render(request, 'pages/accounts/profile.html', {'form': form})