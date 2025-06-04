from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
import uuid

from .models import AttendanceSession, Attendance
from pupils.models import Pupil, Grade

@login_required
def attendance_sessions(request):
    """View for listing attendance sessions"""
    # Get all sessions created by the current user
    sessions = AttendanceSession.objects.filter(created_by=request.user).order_by('-date', '-created_at')

    # Filter by date if provided
    date_filter = request.GET.get('date')
    if date_filter:
        sessions = sessions.filter(date=date_filter)

    # Filter by grade if provided
    grade_id = request.GET.get('grade')
    if grade_id:
        sessions = sessions.filter(grade_id=grade_id)

    # Get all grades for filter dropdown
    grades = Grade.objects.all().order_by('name')

    context = {
        'sessions': sessions,
        'grades': grades,
        'selected_date': date_filter,
        'selected_grade': grade_id,
    }

    return render(request, 'attendance/session_list.html', context)

@login_required
def create_attendance_session(request):
    """View for creating a new attendance session"""
    if not request.user.is_teacher() and not request.user.is_admin():
        messages.error(request, 'You do not have permission to create attendance sessions.')
        return redirect('attendance_sessions')

    if request.method == 'POST':
        date = request.POST.get('date')
        period = request.POST.get('period')
        grade_id = request.POST.get('grade')
        notes = request.POST.get('notes')

        # Validate required fields
        if not all([date, period, grade_id]):
            messages.error(request, 'Please fill in all required fields.')
            return redirect('create_attendance_session')

        # Check if session already exists
        if AttendanceSession.objects.filter(date=date, period=period, grade_id=grade_id).exists():
            messages.error(request, 'An attendance session for this date, period, and grade already exists.')
            return redirect('create_attendance_session')

        # Create new session
        session = AttendanceSession.objects.create(
            date=date,
            period=period,
            grade_id=grade_id,
            notes=notes,
            created_by=request.user
        )

        messages.success(request, 'Attendance session created successfully.')
        return redirect('attendance_session_detail', session_id=session.id)

    # Get all grades for dropdown
    grades = Grade.objects.all().order_by('name')

    context = {
        'grades': grades,
        'today': timezone.now().date().isoformat(),
    }

    return render(request, 'attendance/create_session.html', context)

@login_required
def attendance_session_detail(request, session_id):
    """View for viewing attendance session details"""
    session = get_object_or_404(AttendanceSession, id=session_id)

    # Get all attendances for this session
    attendances_qs = Attendance.objects.filter(session=session).select_related('pupil')

    # Get all pupils in this grade who don't have attendance records yet
    pupils_with_attendance_ids = attendances_qs.values_list('pupil_id', flat=True)
    missing_pupils = Pupil.objects.filter(grade=session.grade, is_active=True).exclude(id__in=pupils_with_attendance_ids)

    # Calculate counts for statistics
    present_count = attendances_qs.filter(status='PRESENT').count()
    # This counts pupils explicitly marked as ABSENT in the attendance records
    explicitly_absent_count = attendances_qs.filter(status='ABSENT').count()
    late_count = attendances_qs.filter(status='LATE').count()
    excused_count = attendances_qs.filter(status='EXCUSED').count() # In case you need it

    # Total pupils expected for the session (all active pupils in the grade)
    # total_pupils_in_grade = Pupil.objects.filter(grade=session.grade, is_active=True).count()
    # An alternative for total_pupils_in_grade that matches the template's previous logic:
    total_pupils_for_stats = attendances_qs.count() + missing_pupils.count()


    context = {
        'session': session,
        'attendances': attendances_qs, # The full queryset for listing
        'missing_pupils': missing_pupils,
        'present_count': present_count,
        'explicitly_absent_count': explicitly_absent_count, # Use this for the "Absent" stat calculation
        'late_count': late_count,
        'excused_count': excused_count,
        'total_pupils_for_stats': total_pupils_for_stats,
    }

    return render(request, 'attendance/session_detail.html', context)

@login_required
def scan_attendance(request):
    """View for scanning QR codes to record attendance"""
    if not request.user.is_teacher() and not request.user.is_admin():
        messages.error(request, 'You do not have permission to record attendance.')
        return redirect('teacher_dashboard')

    # Get active sessions for dropdown
    active_sessions = AttendanceSession.objects.filter(
        is_active=True,
        date=timezone.now().date()
    ).order_by('-created_at')

    context = {
        'active_sessions': active_sessions,
    }

    return render(request, 'attendance/scan_attendance.html', context)

@login_required
@require_POST
@csrf_exempt
def record_attendance(request):
    """API endpoint for recording attendance from QR code scan"""
    if not request.user.is_teacher() and not request.user.is_admin():
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)

    try:
        data = json.loads(request.body)
        pupil_uuid = data.get('uuid')
        session_id = data.get('session_id')
        status = data.get('status', 'PRESENT')

        # Validate required fields
        if not all([pupil_uuid, session_id]):
            return JsonResponse({'success': False, 'error': 'Missing required fields'}, status=400)

        # Get pupil and session
        try:
            pupil = Pupil.objects.get(uuid=pupil_uuid)
            session = AttendanceSession.objects.get(id=session_id)
        except (Pupil.DoesNotExist, AttendanceSession.DoesNotExist, ValueError):
            return JsonResponse({'success': False, 'error': 'Invalid pupil or session'}, status=404)

        # Check if attendance already exists
        attendance, created = Attendance.objects.get_or_create(
            session=session,
            pupil=pupil,
            defaults={
                'status': status,
                'recorded_by': request.user,
            }
        )

        if not created:
            # Update existing attendance
            attendance.status = status
            attendance.recorded_by = request.user
            attendance.timestamp = timezone.now()
            attendance.save()

        return JsonResponse({
            'success': True, 
            'pupil_name': pupil.get_full_name(),
            'status': attendance.get_status_display(),
            'created': created
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
def attendance_report(request):
    """View for generating attendance reports"""
    # Get filter parameters
    grade_id = request.GET.get('grade')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # Base queryset
    attendances = Attendance.objects.all().select_related('pupil', 'session')

    # Apply filters
    if grade_id:
        attendances = attendances.filter(session__grade_id=grade_id)

    if start_date:
        attendances = attendances.filter(session__date__gte=start_date)

    if end_date:
        attendances = attendances.filter(session__date__lte=end_date)

    # Get all grades for filter dropdown
    grades = Grade.objects.all().order_by('name')

    # Calculate statistics
    total_count = attendances.count()
    present_count = attendances.filter(status='PRESENT').count()
    absent_count = attendances.filter(status='ABSENT').count()
    late_count = attendances.filter(status='LATE').count()
    excused_count = attendances.filter(status='EXCUSED').count()

    # Calculate percentages
    present_percent = (present_count / total_count * 100) if total_count > 0 else 0
    absent_percent = (absent_count / total_count * 100) if total_count > 0 else 0
    late_percent = (late_count / total_count * 100) if total_count > 0 else 0
    excused_percent = (excused_count / total_count * 100) if total_count > 0 else 0

    context = {
        'attendances': attendances[:100],  # Limit to 100 records for performance
        'grades': grades,
        'selected_grade': grade_id,
        'start_date': start_date,
        'end_date': end_date,
        'total_count': total_count,
        'present_count': present_count,
        'absent_count': absent_count,
        'late_count': late_count,
        'excused_count': excused_count,
        'present_percent': present_percent,
        'absent_percent': absent_percent,
        'late_percent': late_percent,
        'excused_percent': excused_percent,
    }

    return render(request, 'attendance/report.html', context)
