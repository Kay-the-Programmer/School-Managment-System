from django.urls import path
from . import views

urlpatterns = [
    # Assessment templates
    path('assessments/templates/', views.assessment_template_list, name='assessment_template_list'),
    path('assessments/templates/create/', views.create_assessment_template, name='create_assessment_template'),
    path('assessments/templates/<int:template_id>/', views.assessment_template_detail, name='assessment_template_detail'),
    path('assessments/templates/<int:template_id>/edit/', views.edit_assessment_template, name='edit_assessment_template'),
    
    # Assessments
    path('assessments/', views.assessment_list, name='assessment_list'),
    path('assessments/create/', views.create_assessment, name='create_assessment'),
    path('assessments/<int:assessment_id>/', views.assessment_detail, name='assessment_detail'),
    path('assessments/<int:assessment_id>/edit/', views.edit_assessment, name='edit_assessment'),
    path('assessments/<int:assessment_id>/publish/', views.publish_assessment, name='publish_assessment'),
    
    # Assessment results
    path('assessments/<int:assessment_id>/results/', views.assessment_results, name='assessment_results'),
    path('assessments/<int:assessment_id>/grade/', views.grade_assessment, name='grade_assessment'),
    path('assessments/results/<int:result_id>/', views.assessment_result_detail, name='assessment_result_detail'),
    
    # Reports
    path('assessments/reports/', views.assessment_reports, name='assessment_reports'),
    path('assessments/reports/pupil/<int:pupil_id>/', views.pupil_assessment_report, name='pupil_assessment_report'),
    path('assessments/reports/grade/<int:grade_id>/', views.grade_assessment_report, name='grade_assessment_report'),
    path('assessments/reports/subject/<int:subject_id>/', views.subject_assessment_report, name='subject_assessment_report'),
    
    # Export
    path('assessments/export/<int:assessment_id>/', views.export_assessment_results, name='export_assessment_results'),
]