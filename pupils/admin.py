from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import Grade, Pupil

@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    """Admin interface for the Grade model"""
    list_display = ('name', 'description', 'pupil_count')
    search_fields = ('name', 'description')

    def pupil_count(self, obj):
        """Return the number of pupils in this grade"""
        return obj.pupils.count()

    pupil_count.short_description = _('Number of Pupils')

@admin.register(Pupil)
class PupilAdmin(admin.ModelAdmin):
    """Admin interface for the Pupil model"""
    list_display = ('student_id', 'get_full_name', 'grade', 'gender', 'date_of_birth', 
                   'enrollment_date', 'is_active', 'display_qr_code')
    list_filter = ('is_active', 'gender', 'grade', 'enrollment_date')
    search_fields = ('first_name', 'last_name', 'student_id', 'parent_name', 'parent_phone')
    readonly_fields = ('qr_code', 'uuid', 'enrollment_date')

    fieldsets = (
        (_('Basic Information'), {
            'fields': ('first_name', 'last_name', 'date_of_birth', 'gender', 'photo')
        }),
        (_('Enrollment Details'), {
            'fields': ('student_id', 'grade', 'enrollment_date', 'is_active')
        }),
        (_('Contact Information'), {
            'fields': ('address', 'city', 'state_province', 'postal_code', 'country')
        }),
        (_('Parent/Guardian Information'), {
            'fields': ('parent_name', 'parent_phone', 'parent_email', 
                      'emergency_contact_name', 'emergency_contact_phone')
        }),
        (_('QR Code Information'), {
            'fields': ('qr_code', 'uuid'),
            'classes': ('collapse',),
        }),
    )

    def display_qr_code(self, obj):
        """Display QR code as an image in the admin list view"""
        if obj.qr_code:
            return format_html('<img src="{}" width="50" height="50" />', obj.qr_code.url)
        return "-"

    display_qr_code.short_description = _('QR Code')
