from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.utils import timezone
from django.db.models import Avg, Count, Sum, Q
import csv
import io

from .models import Subject, AssessmentType, GradingScale, AssessmentTemplate, Assessment, AssessmentResult
from pupils.models import Pupil, Grade

# Assessment Template Views
@login_required
def assessment_template_list(request):
    """View for listing assessment templates"""
    # Get templates created by the current user or filter by subject
    templates = AssessmentTemplate.objects.filter(created_by=request.user).order_by('-created_at')

    # Filter by subject if provided
    subject_id = request.GET.get('subject')
    if subject_id:
        templates = templates.filter(subject_id=subject_id)

    # Filter by assessment type if provided
    type_id = request.GET.get('type')
    if type_id:
        templates = templates.filter(assessment_type_id=type_id)

    # Get all subjects and assessment types for filter dropdowns
    subjects = Subject.objects.all().order_by('name')
    assessment_types = AssessmentType.objects.all().order_by('name')

    context = {
        'templates': templates,
        'subjects': subjects,
        'assessment_types': assessment_types,
        'selected_subject': subject_id,
        'selected_type': type_id,
    }

    return render(request, 'assessments/template_list.html', context)

@login_required
def create_assessment_template(request):
    """View for creating a new assessment template"""
    if not request.user.is_teacher() and not request.user.is_admin():
        messages.error(request, 'You do not have permission to create assessment templates.')
        return redirect('assessment_template_list')

    if request.method == 'POST':
        title = request.POST.get('title')
        subject_id = request.POST.get('subject')
        assessment_type_id = request.POST.get('assessment_type')
        total_points = request.POST.get('total_points')
        description = request.POST.get('description')

        # Validate required fields
        if not all([title, subject_id, assessment_type_id, total_points]):
            messages.error(request, 'Please fill in all required fields.')
            return redirect('create_assessment_template')

        # Create the template
        template = AssessmentTemplate.objects.create(
            title=title,
            subject_id=subject_id,
            assessment_type_id=assessment_type_id,
            total_points=total_points,
            description=description,
            created_by=request.user
        )

        messages.success(request, f'Assessment template "{template.title}" created successfully.')
        return redirect('assessment_template_detail', template_id=template.id)

    # Get all subjects and assessment types for the form
    subjects = Subject.objects.all().order_by('name')
    assessment_types = AssessmentType.objects.all().order_by('name')

    context = {
        'subjects': subjects,
        'assessment_types': assessment_types,
    }

    return render(request, 'assessments/template_form.html', context)

@login_required
def assessment_template_detail(request, template_id):
    """View for viewing an assessment template"""
    template = get_object_or_404(AssessmentTemplate, id=template_id)

    # Get assessments that use this template
    assessments = Assessment.objects.filter(template=template).order_by('-date_assigned')

    context = {
        'template': template,
        'assessments': assessments,
    }

    return render(request, 'assessments/template_detail.html', context)

@login_required
def edit_assessment_template(request, template_id):
    """View for editing an assessment template"""
    template = get_object_or_404(AssessmentTemplate, id=template_id)

    # Check if user has permission to edit this template
    if template.created_by != request.user and not request.user.is_admin():
        messages.error(request, 'You do not have permission to edit this template.')
        return redirect('assessment_template_detail', template_id=template.id)

    if request.method == 'POST':
        title = request.POST.get('title')
        subject_id = request.POST.get('subject')
        assessment_type_id = request.POST.get('assessment_type')
        total_points = request.POST.get('total_points')
        description = request.POST.get('description')

        # Validate required fields
        if not all([title, subject_id, assessment_type_id, total_points]):
            messages.error(request, 'Please fill in all required fields.')
            return redirect('edit_assessment_template', template_id=template.id)

        # Update the template
        template.title = title
        template.subject_id = subject_id
        template.assessment_type_id = assessment_type_id
        template.total_points = total_points
        template.description = description
        template.save()

        messages.success(request, f'Assessment template "{template.title}" updated successfully.')
        return redirect('assessment_template_detail', template_id=template.id)

    # Get all subjects and assessment types for the form
    subjects = Subject.objects.all().order_by('name')
    assessment_types = AssessmentType.objects.all().order_by('name')

    context = {
        'template': template,
        'subjects': subjects,
        'assessment_types': assessment_types,
    }

    return render(request, 'assessments/template_form.html', context)

# Assessment Views
@login_required
def assessment_list(request):
    """View for listing assessments"""
    # Get assessments assigned by the current user or filter by grade/subject
    assessments = Assessment.objects.filter(assigned_by=request.user).order_by('-date_assigned')

    # Filter by grade if provided
    grade_id = request.GET.get('grade')
    if grade_id:
        assessments = assessments.filter(grade_class_id=grade_id)

    # Filter by subject if provided
    subject_id = request.GET.get('subject')
    if subject_id:
        assessments = assessments.filter(template__subject_id=subject_id)

    # Filter by status if provided
    status = request.GET.get('status')
    if status == 'published':
        assessments = assessments.filter(is_published=True)
    elif status == 'draft':
        assessments = assessments.filter(is_published=False)

    # Get all grades and subjects for filter dropdowns
    grades = Grade.objects.all().order_by('name')
    subjects = Subject.objects.all().order_by('name')

    context = {
        'assessments': assessments,
        'grades': grades,
        'subjects': subjects,
        'selected_grade': grade_id,
        'selected_subject': subject_id,
        'selected_status': status,
    }

    return render(request, 'assessments/assessment_list.html', context)

@login_required
def create_assessment(request):
    """View for creating a new assessment"""
    if not request.user.is_teacher() and not request.user.is_admin():
        messages.error(request, 'You do not have permission to create assessments.')
        return redirect('assessment_list')

    if request.method == 'POST':
        template_id = request.POST.get('template')
        grade_id = request.POST.get('grade')
        date_assigned = request.POST.get('date_assigned')
        date_due = request.POST.get('date_due')
        instructions = request.POST.get('instructions')

        # Validate required fields
        if not all([template_id, grade_id, date_assigned, date_due]):
            messages.error(request, 'Please fill in all required fields.')
            return redirect('create_assessment')

        # Create the assessment
        assessment = Assessment.objects.create(
            template_id=template_id,
            grade_class_id=grade_id,
            date_assigned=date_assigned,
            date_due=date_due,
            instructions=instructions,
            assigned_by=request.user
        )

        # Handle file upload if provided
        if 'attachment' in request.FILES:
            assessment.attachment = request.FILES['attachment']
            assessment.save()

        messages.success(request, f'Assessment created successfully.')
        return redirect('assessment_detail', assessment_id=assessment.id)

    # Get all templates and grades for the form
    templates = AssessmentTemplate.objects.filter(created_by=request.user).order_by('-created_at')
    grades = Grade.objects.all().order_by('name')

    context = {
        'templates': templates,
        'grades': grades,
    }

    return render(request, 'assessments/assessment_form.html', context)

@login_required
def assessment_detail(request, assessment_id):
    """View for viewing an assessment"""
    assessment = get_object_or_404(Assessment, id=assessment_id)

    # Get results for this assessment
    results = AssessmentResult.objects.filter(assessment=assessment).order_by('pupil__last_name', 'pupil__first_name')

    # Calculate statistics
    total_pupils = Pupil.objects.filter(grade=assessment.grade_class, is_active=True).count()
    submitted_count = results.filter(is_submitted=True).count()
    graded_count = results.filter(score__isnull=False).count()

    if graded_count > 0:
        average_score = results.filter(score__isnull=False).aggregate(Avg('score'))['score__avg']
        average_percentage = results.filter(percentage__isnull=False).aggregate(Avg('percentage'))['percentage__avg']
    else:
        average_score = None
        average_percentage = None

    context = {
        'assessment': assessment,
        'results': results,
        'total_pupils': total_pupils,
        'submitted_count': submitted_count,
        'graded_count': graded_count,
        'average_score': average_score,
        'average_percentage': average_percentage,
    }

    return render(request, 'assessments/assessment_detail.html', context)

@login_required
def edit_assessment(request, assessment_id):
    """View for editing an assessment"""
    assessment = get_object_or_404(Assessment, id=assessment_id)

    # Check if user has permission to edit this assessment
    if assessment.assigned_by != request.user and not request.user.is_admin():
        messages.error(request, 'You do not have permission to edit this assessment.')
        return redirect('assessment_detail', assessment_id=assessment.id)

    # Don't allow editing published assessments
    if assessment.is_published:
        messages.error(request, 'Published assessments cannot be edited.')
        return redirect('assessment_detail', assessment_id=assessment.id)

    if request.method == 'POST':
        template_id = request.POST.get('template')
        grade_id = request.POST.get('grade')
        date_assigned = request.POST.get('date_assigned')
        date_due = request.POST.get('date_due')
        instructions = request.POST.get('instructions')

        # Validate required fields
        if not all([template_id, grade_id, date_assigned, date_due]):
            messages.error(request, 'Please fill in all required fields.')
            return redirect('edit_assessment', assessment_id=assessment.id)

        # Update the assessment
        assessment.template_id = template_id
        assessment.grade_class_id = grade_id
        assessment.date_assigned = date_assigned
        assessment.date_due = date_due
        assessment.instructions = instructions

        # Handle file upload if provided
        if 'attachment' in request.FILES:
            assessment.attachment = request.FILES['attachment']

        assessment.save()

        messages.success(request, f'Assessment updated successfully.')
        return redirect('assessment_detail', assessment_id=assessment.id)

    # Get all templates and grades for the form
    templates = AssessmentTemplate.objects.filter(created_by=request.user).order_by('-created_at')
    grades = Grade.objects.all().order_by('name')

    context = {
        'assessment': assessment,
        'templates': templates,
        'grades': grades,
    }

    return render(request, 'assessments/assessment_form.html', context)

@login_required
def publish_assessment(request, assessment_id):
    """View for publishing an assessment"""
    assessment = get_object_or_404(Assessment, id=assessment_id)

    # Check if user has permission to publish this assessment
    if assessment.assigned_by != request.user and not request.user.is_admin():
        messages.error(request, 'You do not have permission to publish this assessment.')
        return redirect('assessment_detail', assessment_id=assessment.id)

    if request.method == 'POST':
        # Publish the assessment
        assessment.is_published = True
        assessment.published_at = timezone.now()
        assessment.save()

        # Create assessment results for all pupils in the grade
        pupils = Pupil.objects.filter(grade=assessment.grade_class, is_active=True)
        for pupil in pupils:
            # Skip if result already exists
            if not AssessmentResult.objects.filter(assessment=assessment, pupil=pupil).exists():
                AssessmentResult.objects.create(
                    assessment=assessment,
                    pupil=pupil
                )

        messages.success(request, f'Assessment published successfully and assigned to {pupils.count()} pupils.')
        return redirect('assessment_detail', assessment_id=assessment.id)

    # Get count of pupils in the grade
    pupil_count = Pupil.objects.filter(grade=assessment.grade_class, is_active=True).count()

    context = {
        'assessment': assessment,
        'pupil_count': pupil_count,
    }

    return render(request, 'assessments/publish_assessment.html', context)

# Assessment Result Views
@login_required
def assessment_results(request, assessment_id):
    """View for listing results for an assessment"""
    assessment = get_object_or_404(Assessment, id=assessment_id)

    # Get results for this assessment
    results = AssessmentResult.objects.filter(assessment=assessment).order_by('pupil__last_name', 'pupil__first_name')

    # Filter by status if provided
    status = request.GET.get('status')
    if status == 'submitted':
        results = results.filter(is_submitted=True)
    elif status == 'not_submitted':
        results = results.filter(is_submitted=False)
    elif status == 'graded':
        results = results.filter(score__isnull=False)
    elif status == 'not_graded':
        results = results.filter(is_submitted=True, score__isnull=True)

    context = {
        'assessment': assessment,
        'results': results,
        'selected_status': status,
    }

    return render(request, 'assessments/results_list.html', context)

@login_required
def grade_assessment(request, assessment_id):
    """View for grading an assessment"""
    assessment = get_object_or_404(Assessment, id=assessment_id)

    # Check if user has permission to grade this assessment
    if assessment.assigned_by != request.user and not request.user.is_admin():
        messages.error(request, 'You do not have permission to grade this assessment.')
        return redirect('assessment_results', assessment_id=assessment.id)

    if request.method == 'POST':
        # Process grading form
        for key, value in request.POST.items():
            if key.startswith('score_'):
                result_id = key.split('_')[1]
                score = value
                feedback = request.POST.get(f'feedback_{result_id}', '')

                if score:  # Only update if score is provided
                    result = get_object_or_404(AssessmentResult, id=result_id)
                    result.score = score
                    result.feedback = feedback
                    result.graded_by = request.user
                    result.graded_at = timezone.now()
                    result.save()

        messages.success(request, 'Assessment graded successfully.')
        return redirect('assessment_results', assessment_id=assessment.id)

    # Get submitted results that need grading
    results = AssessmentResult.objects.filter(
        assessment=assessment,
        is_submitted=True
    ).order_by('pupil__last_name', 'pupil__first_name')

    context = {
        'assessment': assessment,
        'results': results,
    }

    return render(request, 'assessments/grade_assessment.html', context)

@login_required
def assessment_result_detail(request, result_id):
    """View for viewing a single assessment result"""
    result = get_object_or_404(AssessmentResult, id=result_id)

    # Check if user has permission to view this result
    if result.assessment.assigned_by != request.user and not request.user.is_admin():
        messages.error(request, 'You do not have permission to view this result.')
        return redirect('assessment_list')

    context = {
        'result': result,
    }

    return render(request, 'assessments/result_detail.html', context)

# Report Views
@login_required
def assessment_reports(request):
    """View for assessment reports landing page"""
    # Get all grades and subjects for filter options
    grades = Grade.objects.all().order_by('name')
    subjects = Subject.objects.all().order_by('name')

    context = {
        'grades': grades,
        'subjects': subjects,
    }

    return render(request, 'assessments/reports.html', context)

@login_required
def pupil_assessment_report(request, pupil_id):
    """View for generating a report for a specific pupil"""
    pupil = get_object_or_404(Pupil, id=pupil_id)

    # Get all results for this pupil
    results = AssessmentResult.objects.filter(
        pupil=pupil,
        score__isnull=False  # Only include graded assessments
    ).order_by('-assessment__date_assigned')

    # Filter by subject if provided
    subject_id = request.GET.get('subject')
    if subject_id:
        results = results.filter(assessment__template__subject_id=subject_id)

    # Filter by date range if provided
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date:
        results = results.filter(assessment__date_assigned__gte=start_date)
    if end_date:
        results = results.filter(assessment__date_assigned__lte=end_date)

    # Calculate statistics
    total_assessments = results.count()
    if total_assessments > 0:
        average_percentage = results.aggregate(Avg('percentage'))['percentage__avg']
    else:
        average_percentage = None

    # Group results by subject
    subjects = Subject.objects.filter(
        assessment_templates__assessments__results__in=results
    ).distinct()

    subject_stats = []
    for subject in subjects:
        subject_results = results.filter(assessment__template__subject=subject)
        subject_avg = subject_results.aggregate(Avg('percentage'))['percentage__avg']
        subject_stats.append({
            'subject': subject,
            'count': subject_results.count(),
            'average': subject_avg
        })

    context = {
        'pupil': pupil,
        'results': results,
        'total_assessments': total_assessments,
        'average_percentage': average_percentage,
        'subject_stats': subject_stats,
        'subjects': Subject.objects.all().order_by('name'),
        'selected_subject': subject_id,
        'start_date': start_date,
        'end_date': end_date,
    }

    return render(request, 'assessments/pupil_report.html', context)

@login_required
def grade_assessment_report(request, grade_id):
    """View for generating a report for a specific grade"""
    grade = get_object_or_404(Grade, id=grade_id)

    # Get all assessments for this grade
    assessments = Assessment.objects.filter(
        grade_class=grade,
        is_published=True
    ).order_by('-date_assigned')

    # Filter by subject if provided
    subject_id = request.GET.get('subject')
    if subject_id:
        assessments = assessments.filter(template__subject_id=subject_id)

    # Filter by date range if provided
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date:
        assessments = assessments.filter(date_assigned__gte=start_date)
    if end_date:
        assessments = assessments.filter(date_assigned__lte=end_date)

    # Calculate statistics for each assessment
    assessment_stats = []
    for assessment in assessments:
        results = AssessmentResult.objects.filter(assessment=assessment, score__isnull=False)
        if results.exists():
            avg_score = results.aggregate(Avg('score'))['score__avg']
            avg_percentage = results.aggregate(Avg('percentage'))['percentage__avg']
            total_pupils = Pupil.objects.filter(grade=grade, is_active=True).count()
            graded_count = results.count()
        else:
            avg_score = None
            avg_percentage = None
            total_pupils = Pupil.objects.filter(grade=grade, is_active=True).count()
            graded_count = 0

        assessment_stats.append({
            'assessment': assessment,
            'avg_score': avg_score,
            'avg_percentage': avg_percentage,
            'total_pupils': total_pupils,
            'graded_count': graded_count,
        })

    context = {
        'grade': grade,
        'assessment_stats': assessment_stats,
        'subjects': Subject.objects.all().order_by('name'),
        'selected_subject': subject_id,
        'start_date': start_date,
        'end_date': end_date,
    }

    return render(request, 'assessments/grade_report.html', context)

@login_required
def subject_assessment_report(request, subject_id):
    """View for generating a report for a specific subject"""
    subject = get_object_or_404(Subject, id=subject_id)

    # Get all assessments for this subject
    assessments = Assessment.objects.filter(
        template__subject=subject,
        is_published=True
    ).order_by('-date_assigned')

    # Filter by grade if provided
    grade_id = request.GET.get('grade')
    if grade_id:
        assessments = assessments.filter(grade_class_id=grade_id)

    # Filter by date range if provided
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date:
        assessments = assessments.filter(date_assigned__gte=start_date)
    if end_date:
        assessments = assessments.filter(date_assigned__lte=end_date)

    # Calculate statistics by grade
    grades = Grade.objects.filter(
        assessments__template__subject=subject
    ).distinct().order_by('name')

    grade_stats = []
    for grade in grades:
        grade_assessments = assessments.filter(grade_class=grade)
        grade_results = AssessmentResult.objects.filter(
            assessment__in=grade_assessments,
            score__isnull=False
        )

        if grade_results.exists():
            avg_percentage = grade_results.aggregate(Avg('percentage'))['percentage__avg']
            assessment_count = grade_assessments.count()
        else:
            avg_percentage = None
            assessment_count = grade_assessments.count()

        grade_stats.append({
            'grade': grade,
            'assessment_count': assessment_count,
            'avg_percentage': avg_percentage,
        })

    context = {
        'subject': subject,
        'assessments': assessments,
        'grade_stats': grade_stats,
        'grades': Grade.objects.all().order_by('name'),
        'selected_grade': grade_id,
        'start_date': start_date,
        'end_date': end_date,
    }

    return render(request, 'assessments/subject_report.html', context)

# Export Views
@login_required
def export_assessment_results(request, assessment_id):
    """View for exporting assessment results to CSV"""
    assessment = get_object_or_404(Assessment, id=assessment_id)

    # Check if user has permission to export results
    if assessment.assigned_by != request.user and not request.user.is_admin():
        messages.error(request, 'You do not have permission to export these results.')
        return redirect('assessment_detail', assessment_id=assessment.id)

    # Get results for this assessment
    results = AssessmentResult.objects.filter(assessment=assessment).order_by('pupil__last_name', 'pupil__first_name')

    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{assessment.template.title}_{assessment.grade_class.name}_results.csv"'

    # Create CSV writer
    buffer = io.StringIO()
    writer = csv.writer(buffer)

    # Write header row
    writer.writerow([
        'Student ID', 'Last Name', 'First Name', 'Score', 'Total Points', 
        'Percentage', 'Grade', 'Submitted', 'Submission Date', 'Feedback'
    ])

    # Write data rows
    for result in results:
        writer.writerow([
            result.pupil.student_id,
            result.pupil.last_name,
            result.pupil.first_name,
            result.score if result.score is not None else '',
            assessment.template.total_points,
            f"{result.percentage:.2f}%" if result.percentage is not None else '',
            result.grade_letter if result.grade_letter else '',
            'Yes' if result.is_submitted else 'No',
            result.submission_date.strftime('%Y-%m-%d %H:%M') if result.submission_date else '',
            result.feedback if result.feedback else ''
        ])

    # Write to response
    response.write(buffer.getvalue())
    return response
