from django.urls import path
from . import views

urlpatterns = [
    # Attendance session management
    path('attendance/sessions/', views.attendance_sessions, name='attendance_sessions'),
    path('attendance/sessions/create/', views.create_attendance_session, name='create_attendance_session'),
    path('attendance/sessions/<int:session_id>/', views.attendance_session_detail, name='attendance_session_detail'),
    
    # QR code scanning and attendance recording
    path('attendance/scan/', views.scan_attendance, name='scan_attendance'),
    path('attendance/record/', views.record_attendance, name='record_attendance'),
    
    # Reports
    path('attendance/report/', views.attendance_report, name='attendance_report'),
]