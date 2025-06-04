from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView, PasswordResetView
from django.urls import reverse_lazy
from .models import User

class CustomLoginView(LoginView):
    """Custom login view"""
    template_name = 'users/login.html'
    redirect_authenticated_user = True

class CustomLogoutView(LogoutView):
    """Custom logout view"""
    next_page = 'login'

class CustomPasswordChangeView(PasswordChangeView):
    """Custom password change view"""
    success_url = reverse_lazy('profile')

    def form_valid(self, form):
        messages.success(self.request, 'Your password was successfully updated!')
        return super().form_valid(form)

class CustomPasswordResetView(PasswordResetView):
    """Custom password reset view"""
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        messages.info(self.request, 'We\'ve emailed you instructions for setting your password.')
        return super().form_valid(form)

@login_required
def profile_view(request):
    """View for user profile page"""
    if request.method == 'POST':
        # Get form data
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        address = request.POST.get('address')

        # Update user
        user = request.user
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.phone_number = phone_number
        user.address = address

        # Handle profile picture
        if 'profile_picture' in request.FILES:
            user.profile_picture = request.FILES['profile_picture']
        elif 'remove_picture' in request.POST:
            user.profile_picture = None

        user.save()
        messages.success(request, 'Your profile has been updated successfully!')
        return redirect('profile')

    return render(request, 'users/profile.html')

@login_required
def teacher_dashboard(request):
    """Dashboard view for teachers"""
    if not request.user.is_teacher():
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('profile')

    # Get counts for dashboard
    from pupils.models import Pupil
    from attendance.models import AttendanceSession, Attendance

    pupil_count = Pupil.objects.filter(is_active=True).count()
    session_count = AttendanceSession.objects.filter(created_by=request.user).count()
    attendance_count = Attendance.objects.filter(recorded_by=request.user).count()

    context = {
        'pupil_count': pupil_count,
        'session_count': session_count,
        'attendance_count': attendance_count,
    }

    return render(request, 'users/teacher_dashboard.html', context)

def home_view(request):
    """Home page view"""
    if request.user.is_authenticated:
        if request.user.is_teacher():
            return redirect('teacher_dashboard')
        elif request.user.is_admin():
            return redirect('admin:index')

    return render(request, 'users/home.html')
