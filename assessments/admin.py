from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import (
    Subject, AssessmentType, GradingScale, AssessmentTemplate, 
    Assessment, AssessmentResult
)

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    """Admin interface for the Subject model"""
    list_display = ('name', 'code', 'description')
    search_fields = ('name', 'code', 'description')
    ordering = ('name',)

@admin.register(AssessmentType)
class AssessmentTypeAdmin(admin.ModelAdmin):
    """Admin interface for the AssessmentType model"""
    list_display = ('name', 'weight', 'description')
    search_fields = ('name', 'description')
    ordering = ('name',)

@admin.register(GradingScale)
class GradingScaleAdmin(admin.ModelAdmin):
    """Admin interface for the GradingScale model"""
    list_display = ('grade_letter', 'min_score', 'max_score', 'description')
    search_fields = ('grade_letter', 'description')
    ordering = ('-min_score',)

class AssessmentInline(admin.TabularInline):
    """Inline admin for Assessments within an AssessmentTemplate"""
    model = Assessment
    extra = 0
    fields = ('grade_class', 'date_assigned', 'date_due', 'is_published')

@admin.register(AssessmentTemplate)
class AssessmentTemplateAdmin(admin.ModelAdmin):
    """Admin interface for the AssessmentTemplate model"""
    list_display = ('title', 'subject', 'assessment_type', 'total_points', 'created_by', 'created_at')
    list_filter = ('subject', 'assessment_type', 'created_at')
    search_fields = ('title', 'description', 'subject__name')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [AssessmentInline]

    fieldsets = (
        (_('Basic Information'), {
            'fields': ('title', 'subject', 'assessment_type', 'total_points')
        }),
        (_('Description'), {
            'fields': ('description',)
        }),
        (_('Metadata'), {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

class AssessmentResultInline(admin.TabularInline):
    """Inline admin for AssessmentResults within an Assessment"""
    model = AssessmentResult
    extra = 0
    fields = ('pupil', 'score', 'percentage', 'grade_letter', 'is_submitted', 'graded_by')
    readonly_fields = ('percentage', 'grade_letter')

@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    """Admin interface for the Assessment model"""
    list_display = ('template_title', 'subject', 'grade_class', 'date_assigned', 'date_due', 
                   'is_published', 'assigned_by', 'result_count')
    list_filter = ('is_published', 'date_assigned', 'date_due', 'grade_class', 'template__subject')
    search_fields = ('template__title', 'instructions', 'grade_class__name')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [AssessmentResultInline]

    fieldsets = (
        (_('Assessment Information'), {
            'fields': ('template', 'grade_class', 'date_assigned', 'date_due')
        }),
        (_('Details'), {
            'fields': ('instructions', 'attachment')
        }),
        (_('Publication'), {
            'fields': ('is_published', 'published_at')
        }),
        (_('Metadata'), {
            'fields': ('assigned_by', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def template_title(self, obj):
        """Return the title of the assessment template"""
        return obj.template.title

    def subject(self, obj):
        """Return the subject of the assessment"""
        return obj.template.subject

    def result_count(self, obj):
        """Return the number of results for this assessment"""
        return obj.results.count()

    template_title.short_description = _('Title')
    subject.short_description = _('Subject')
    result_count.short_description = _('Results')

@admin.register(AssessmentResult)
class AssessmentResultAdmin(admin.ModelAdmin):
    """Admin interface for the AssessmentResult model"""
    list_display = ('pupil', 'assessment_title', 'score', 'percentage', 'grade_letter', 
                   'is_submitted', 'submission_date', 'graded_by', 'graded_at')
    list_filter = ('is_submitted', 'grade_letter', 'assessment__template__subject', 
                  'assessment__grade_class')
    search_fields = ('pupil__first_name', 'pupil__last_name', 'pupil__student_id', 
                    'assessment__template__title', 'feedback')
    readonly_fields = ('percentage', 'grade_letter', 'created_at', 'updated_at')

    fieldsets = (
        (_('Result Information'), {
            'fields': ('assessment', 'pupil', 'score', 'percentage', 'grade_letter')
        }),
        (_('Submission'), {
            'fields': ('is_submitted', 'submission_date', 'submission_file')
        }),
        (_('Grading'), {
            'fields': ('feedback', 'graded_by', 'graded_at')
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def assessment_title(self, obj):
        """Return the title of the assessment"""
        return obj.assessment.template.title

    assessment_title.short_description = _('Assessment')

    def get_queryset(self, request):
        """Optimize queryset with select_related to reduce database queries"""
        return super().get_queryset(request).select_related(
            'pupil', 'assessment', 'assessment__template', 'assessment__template__subject',
            'assessment__grade_class', 'graded_by'
        )
