from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import AttendanceSession, Attendance

class AttendanceInline(admin.TabularInline):
    """Inline admin for Attendance records within an AttendanceSession"""
    model = Attendance
    extra = 0
    readonly_fields = ('timestamp',)
    autocomplete_fields = ('pupil',)
    fields = ('pupil', 'status', 'minutes_late', 'excuse_reason', 'notes', 'recorded_by', 'timestamp')

@admin.register(AttendanceSession)
class AttendanceSessionAdmin(admin.ModelAdmin):
    """Admin interface for the AttendanceSession model"""
    list_display = ('date', 'period', 'grade', 'created_by', 'is_active', 'attendance_count', 'present_count', 'absent_count')
    list_filter = ('date', 'period', 'grade', 'is_active')
    search_fields = ('grade__name', 'notes')
    readonly_fields = ('created_at',)
    inlines = [AttendanceInline]

    def attendance_count(self, obj):
        """Return the total number of attendance records for this session"""
        return obj.attendances.count()

    def present_count(self, obj):
        """Return the number of present pupils for this session"""
        return obj.attendances.filter(status='PRESENT').count()

    def absent_count(self, obj):
        """Return the number of absent pupils for this session"""
        return obj.attendances.filter(status='ABSENT').count()

    attendance_count.short_description = _('Total')
    present_count.short_description = _('Present')
    absent_count.short_description = _('Absent')

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    """Admin interface for the Attendance model"""
    list_display = ('pupil', 'session', 'status', 'timestamp', 'recorded_by', 'minutes_late')
    list_filter = ('status', 'session__date', 'session__period', 'session__grade')
    search_fields = ('pupil__first_name', 'pupil__last_name', 'pupil__student_id', 'notes')
    readonly_fields = ('timestamp',)
    autocomplete_fields = ('pupil', 'session')

    fieldsets = (
        (_('Attendance Information'), {
            'fields': ('session', 'pupil', 'status', 'timestamp', 'recorded_by')
        }),
        (_('Additional Details'), {
            'fields': ('minutes_late', 'excuse_reason', 'notes'),
            'classes': ('collapse',),
        }),
    )

    def get_queryset(self, request):
        """Optimize queryset with select_related to reduce database queries"""
        return super().get_queryset(request).select_related(
            'pupil', 'session', 'recorded_by', 'session__grade'
        )
