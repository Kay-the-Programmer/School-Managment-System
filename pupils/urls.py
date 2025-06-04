from django.urls import path
from . import views

urlpatterns = [
    # Pupil list and detail views
    path('pupils/', views.pupil_list, name='pupil_list'),
    path('pupils/<int:pupil_id>/', views.pupil_detail, name='pupil_detail'),
    path('pupils/<int:pupil_id>/generate-qr-code/', views.generate_qr_code, name='generate_qr_code'),
]