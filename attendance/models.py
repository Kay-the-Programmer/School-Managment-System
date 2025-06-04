from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from pupils.models import Pupil, Grade

class AttendanceSession(models.Model):
    """
    Model to represent an attendance session (e.g., morning attendance, afternoon attendance)
    """
    date = models.DateField()
    PERIOD_CHOICES = [
        ('MORNING', 'Morning'),
        ('AFTERNOON', 'Afternoon'),
        ('FULL_DAY', 'Full Day'),
        ('SPECIAL', 'Special Event'),
    ]
    period = models.CharField(max_length=20, choices=PERIOD_CHOICES, default='MORNING')
    grade = models.ForeignKey(Grade, on_delete=models.CASCADE, related_name='attendance_sessions')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_sessions')
    notes = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Attendance Session')
        verbose_name_plural = _('Attendance Sessions')
        unique_together = ['date', 'period', 'grade']
        ordering = ['-date', 'period']

    def __str__(self):
        return f"{self.grade} - {self.get_period_display()} - {self.date}"

class Attendance(models.Model):
    """
    Model for tracking pupil attendance using QR codes
    """
    session = models.ForeignKey(AttendanceSession, on_delete=models.CASCADE, related_name='attendances')
    pupil = models.ForeignKey(Pupil, on_delete=models.CASCADE, related_name='attendances')

    STATUS_CHOICES = [
        ('PRESENT', 'Present'),
        ('ABSENT', 'Absent'),
        ('LATE', 'Late'),
        ('EXCUSED', 'Excused'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PRESENT')

    # Time when attendance was recorded
    timestamp = models.DateTimeField(auto_now_add=True)

    # Teacher who recorded the attendance
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='recorded_attendances'
    )

    # For late arrivals, store the minutes late
    minutes_late = models.PositiveIntegerField(blank=True, null=True)

    # For excused absences, store the reason
    excuse_reason = models.TextField(blank=True, null=True)

    # Notes or comments
    notes = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = _('Attendance')
        verbose_name_plural = _('Attendances')
        # Ensure a pupil can only have one attendance record per session
        unique_together = ['session', 'pupil']
        ordering = ['session', 'pupil']

    def __str__(self):
        return f"{self.pupil} - {self.get_status_display()} - {self.session.date}"

    def save(self, *args, **kwargs):
        # If status is changed to LATE and minutes_late is not set, default to 1
        if self.status == 'LATE' and self.minutes_late is None:
            self.minutes_late = 1
        super().save(*args, **kwargs)
