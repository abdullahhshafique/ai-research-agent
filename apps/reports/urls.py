from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('<int:pk>/preview/', views.report_preview, name='report_preview'),
    path('<int:pk>/download/', views.report_download, name='report_download'),
    path('<int:pk>/stream/', views.report_stream, name='report_stream'),
    path('<int:pk>/delete/', views.report_delete, name='report_delete'),
    path('<int:pk>/rate/', views.report_rate, name='report_rate'),
    path('<int:pk>/share/', views.report_share, name='report_share'),
    path('<int:pk>/regenerate/', views.report_regenerate, name='report_regenerate'),
]