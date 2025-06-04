from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from pupils.models import Pupil, Grade

class Subject(models.Model):
    """Model for academic subjects"""
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = _('Subject')
        verbose_name_plural = _('Subjects')
        ordering = ['name']

    def __str__(self):
        return self.name

class AssessmentType(models.Model):
    """Model for different types of assessments (e.g., quiz, exam, project)"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    weight = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text=_('Weight of this assessment type in the final grade calculation (percentage)')
    )

    class Meta:
        verbose_name = _('Assessment Type')
        verbose_name_plural = _('Assessment Types')
        ordering = ['name']

    def __str__(self):
        return self.name

class GradingScale(models.Model):
    """Model for defining grading scales (e.g., A=90-100, B=80-89)"""
    grade_letter = models.CharField(max_length=2)
    min_score = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    max_score = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    description = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        verbose_name = _('Grading Scale')
        verbose_name_plural = _('Grading Scales')
        ordering = ['-min_score']

    def __str__(self):
        return f"{self.grade_letter} ({self.min_score}-{self.max_score})"

class AssessmentTemplate(models.Model):
    """
    Template for assessments that can be reused across multiple classes
    """
    title = models.CharField(max_length=200)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='assessment_templates')
    assessment_type = models.ForeignKey(AssessmentType, on_delete=models.CASCADE, related_name='templates')
    total_points = models.DecimalField(
        max_digits=7, 
        decimal_places=2, 
        validators=[MinValueValidator(0)]
    )
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_templates')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Assessment Template')
        verbose_name_plural = _('Assessment Templates')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.subject} ({self.assessment_type})"

class Assessment(models.Model):
    """
    Model for tracking pupil assessments, including grades and scores
    """
    template = models.ForeignKey(AssessmentTemplate, on_delete=models.CASCADE, related_name='assessments')
    grade_class = models.ForeignKey(Grade, on_delete=models.CASCADE, related_name='assessments')
    date_assigned = models.DateField()
    date_due = models.DateField()

    # Additional fields specific to this instance of the assessment
    instructions = models.TextField(blank=True, null=True)
    attachment = models.FileField(upload_to='assessment_attachments/', blank=True, null=True)

    # Status tracking
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(blank=True, null=True)

    # Teacher who created/assigned this assessment
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='assigned_assessments'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Assessment')
        verbose_name_plural = _('Assessments')
        ordering = ['-date_assigned']

    def __str__(self):
        return f"{self.template.title} - {self.grade_class} ({self.date_assigned})"

class AssessmentResult(models.Model):
    """
    Model for storing individual pupil results for assessments
    """
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='results')
    pupil = models.ForeignKey(Pupil, on_delete=models.CASCADE, related_name='assessment_results')

    # Score and grade
    score = models.DecimalField(
        max_digits=7, 
        decimal_places=2, 
        validators=[MinValueValidator(0)],
        blank=True, 
        null=True
    )

    # Automatically calculated percentage
    percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        blank=True, 
        null=True
    )

    # Letter grade (can be automatically determined based on percentage and grading scale)
    grade_letter = models.CharField(max_length=2, blank=True, null=True)

    # Submission tracking
    is_submitted = models.BooleanField(default=False)
    submission_date = models.DateTimeField(blank=True, null=True)
    submission_file = models.FileField(upload_to='assessment_submissions/', blank=True, null=True)

    # Feedback
    feedback = models.TextField(blank=True, null=True)

    # Teacher who graded this assessment
    graded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='graded_assessments',
        blank=True, 
        null=True
    )

    graded_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Assessment Result')
        verbose_name_plural = _('Assessment Results')
        # Ensure a pupil can only have one result per assessment
        unique_together = ['assessment', 'pupil']
        ordering = ['assessment', 'pupil']

    def __str__(self):
        return f"{self.pupil} - {self.assessment} - {self.score}/{self.assessment.template.total_points}"

    def save(self, *args, **kwargs):
        # Calculate percentage if score is provided
        if self.score is not None and self.assessment.template.total_points > 0:
            self.percentage = (self.score / self.assessment.template.total_points) * 100

            # Determine letter grade based on percentage and grading scale
            try:
                grading_scale = GradingScale.objects.filter(
                    min_score__lte=self.percentage,
                    max_score__gte=self.percentage
                ).first()

                if grading_scale:
                    self.grade_letter = grading_scale.grade_letter
            except:
                pass

        super().save(*args, **kwargs)
