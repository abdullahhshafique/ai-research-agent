"""
Accounts app URL configuration.
"""
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('verify-email/', views.verify_email_send, name='verify_email_send'),
    path('verify-email/<uidb64>/<token>/', views.verify_email_confirm, name='verify_email_confirm'),

    # Password Reset
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='pages/accounts/password_reset.html',
             email_template_name='pages/accounts/password_reset_email.html'
         ), 
         name='password_reset'),
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='pages/accounts/password_reset_done.html'
         ), 
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='pages/accounts/password_reset_confirm.html'
         ), 
         name='password_reset_confirm'),
    path('password-reset-complete/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='pages/accounts/password_reset_complete.html'
         ), 
         name='password_reset_complete'),
]