from django.urls import path
from . import views

urlpatterns = [
    # Messages
    path('messages/', views.message_list, name='message_list'),
    path('messages/compose/', views.compose_message, name='compose_message'),
    path('messages/thread/<int:thread_id>/', views.message_thread, name='message_thread'),
    path('messages/thread/<int:thread_id>/reply/', views.reply_to_thread, name='reply_to_thread'),
    
    # Announcements
    path('announcements/', views.announcement_list, name='announcement_list'),
    path('announcements/create/', views.create_announcement, name='create_announcement'),
    path('announcements/<int:announcement_id>/', views.announcement_detail, name='announcement_detail'),
    path('announcements/<int:announcement_id>/edit/', views.edit_announcement, name='edit_announcement'),
    path('announcements/<int:announcement_id>/publish/', views.publish_announcement, name='publish_announcement'),
    
    # Notifications
    path('notifications/', views.notification_list, name='notification_list'),
    path('notifications/mark-read/', views.mark_notifications_read, name='mark_notifications_read'),
    path('notifications/<int:notification_id>/mark-read/', views.mark_notification_read, name='mark_notification_read'),
    
    # API endpoints for AJAX
    path('api/notifications/count/', views.notification_count, name='notification_count'),
    path('api/notifications/recent/', views.recent_notifications, name='recent_notifications'),
]