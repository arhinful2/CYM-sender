from django.urls import path
from . import views

urlpatterns = [
    path('', views.admin_portal, name='admin_portal'),
    path('search/', views.member_search, name='member_search'),
    path('member/<int:pk>/', views.member_detail, name='member_detail'),
    path('messaging/', views.messaging_dashboard, name='messaging_dashboard'),
    path('messaging/compose/', views.compose_message, name='compose_message'),
    path('messaging/<uuid:message_id>/responses/', views.message_responses, name='message_responses'),
    path('member/<int:member_id>/messages/', views.member_messages, name='member_messages'),
    path('analytics/', views.analytics_dashboard, name='analytics_dashboard'),
    path('ajax/search-members/', views.ajax_search_members, name='ajax_search_members'),
    path('export-members-csv/', views.export_members_csv, name='export_members_csv'),
    path('quick-attendance/', views.quick_attendance, name='quick_attendance'),
    path('setup-sms-email/', views.setup_sms_email, name='setup_sms_email'),
    path('send-test-message/', views.send_test_message, name='send_test_message'),
    
    path('birthday-tracker/', views.birthday_tracker, name='birthday_tracker'),
]