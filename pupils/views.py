from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Pupil, Grade

@login_required
def pupil_list(request):
    """View for listing all pupils"""
    # Get all active pupils
    pupils = Pupil.objects.filter(is_active=True).order_by('last_name', 'first_name')

    # Filter by grade if provided
    grade_id = request.GET.get('grade')
    if grade_id:
        pupils = pupils.filter(grade_id=grade_id)

    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        pupils = pupils.filter(
            first_name__icontains=search_query) | pupils.filter(
            last_name__icontains=search_query) | pupils.filter(
            student_id__icontains=search_query
        )

    # Get all grades for filter dropdown
    grades = Grade.objects.all().order_by('name')

    context = {
        'pupils': pupils,
        'grades': grades,
        'selected_grade': grade_id,
        'search_query': search_query,
    }

    return render(request, 'pupils/pupil_list.html', context)

@login_required
def pupil_detail(request, pupil_id):
    """View for displaying pupil details including QR code"""
    pupil = get_object_or_404(Pupil, id=pupil_id)

    # Get attendance records for this pupil
    from attendance.models import Attendance
    attendances = Attendance.objects.filter(pupil=pupil).order_by('-session__date', '-timestamp')[:10]

    # Get assessment results for this pupil
    from assessments.models import AssessmentResult
    assessment_results = AssessmentResult.objects.filter(pupil=pupil).order_by('-assessment__date_assigned')[:10]

    context = {
        'pupil': pupil,
        'attendances': attendances,
        'assessment_results': assessment_results,
    }

    return render(request, 'pupils/pupil_detail.html', context)

@login_required
def generate_qr_code(request, pupil_id):
    """View for generating/regenerating QR code for a pupil"""
    if not request.user.is_teacher() and not request.user.is_admin():
        messages.error(request, 'You do not have permission to generate QR codes.')
        return redirect('pupil_list')

    pupil = get_object_or_404(Pupil, id=pupil_id)

    # Force regeneration of QR code
    pupil.qr_code = None
    pupil.generate_qr_code()
    pupil.save()

    messages.success(request, f'QR code for {pupil.get_full_name()} has been regenerated.')
    return redirect('pupil_detail', pupil_id=pupil.id)
