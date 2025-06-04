from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from django.contrib.auth import get_user_model

from .models import MessageThread, Message, AnnouncementCategory, Announcement, Notification
from pupils.models import Grade

User = get_user_model()

# Message Views
@login_required
def message_list(request):
    """View for listing message threads"""
    # Get threads that the current user is a participant in
    threads = MessageThread.objects.filter(participants=request.user).order_by('-updated_at')

    context = {
        'threads': threads,
    }

    return render(request, 'communication/message_list.html', context)

@login_required
def compose_message(request):
    """View for composing a new message"""
    if request.method == 'POST':
        subject = request.POST.get('subject')
        content = request.POST.get('content')
        recipient_ids = request.POST.getlist('recipients')

        # Validate required fields
        if not all([subject, content, recipient_ids]):
            messages.error(request, 'Please fill in all required fields.')
            return redirect('compose_message')

        # Create a new thread
        thread = MessageThread.objects.create(subject=subject)

        # Add participants (sender and recipients)
        thread.participants.add(request.user)
        for recipient_id in recipient_ids:
            thread.participants.add(User.objects.get(id=recipient_id))

        # Create the message
        message = Message.objects.create(
            thread=thread,
            sender=request.user,
            content=content
        )

        # Handle file attachment if provided
        if 'attachment' in request.FILES:
            message.attachment = request.FILES['attachment']
            message.save()

        # Create notifications for recipients
        for recipient_id in recipient_ids:
            recipient = User.objects.get(id=recipient_id)
            Notification.objects.create(
                user=recipient,
                title=f'New Message: {subject}',
                message=f'You have received a new message from {request.user.get_full_name() or request.user.username}',
                notification_type='MESSAGE',
                related_message=message,
                link=f'/messages/thread/{thread.id}/'
            )

        messages.success(request, 'Message sent successfully.')
        return redirect('message_thread', thread_id=thread.id)

    # Get all users for recipient selection (excluding self)
    users = User.objects.exclude(id=request.user.id).order_by('last_name', 'first_name')

    context = {
        'users': users,
    }

    return render(request, 'communication/compose_message.html', context)

@login_required
def message_thread(request, thread_id):
    """View for viewing a message thread"""
    thread = get_object_or_404(MessageThread, id=thread_id)

    # Check if user is a participant in this thread
    if request.user not in thread.participants.all():
        messages.error(request, 'You do not have permission to view this message thread.')
        return redirect('message_list')

    # Get all messages in this thread
    thread_messages = Message.objects.filter(thread=thread).order_by('sent_at')

    # Mark messages as read by current user
    for message in thread_messages:
        if message.sender != request.user and request.user not in message.read_by.all():
            message.read_by.add(request.user)

    # Mark related notifications as read
    notifications = Notification.objects.filter(
        user=request.user,
        related_message__thread=thread,
        is_read=False
    )
    for notification in notifications:
        notification.mark_as_read()

    context = {
        'thread': thread,
        'messages': thread_messages,
    }

    return render(request, 'communication/message_thread.html', context)

@login_required
def reply_to_thread(request, thread_id):
    """View for replying to a message thread"""
    thread = get_object_or_404(MessageThread, id=thread_id)

    # Check if user is a participant in this thread
    if request.user not in thread.participants.all():
        messages.error(request, 'You do not have permission to reply to this message thread.')
        return redirect('message_list')

    if request.method == 'POST':
        content = request.POST.get('content')

        # Validate content
        if not content:
            messages.error(request, 'Message content cannot be empty.')
            return redirect('message_thread', thread_id=thread.id)

        # Create the reply message
        message = Message.objects.create(
            thread=thread,
            sender=request.user,
            content=content
        )

        # Handle file attachment if provided
        if 'attachment' in request.FILES:
            message.attachment = request.FILES['attachment']
            message.save()

        # Update thread timestamp
        thread.updated_at = timezone.now()
        thread.save()

        # Create notifications for other participants
        for participant in thread.participants.exclude(id=request.user.id):
            Notification.objects.create(
                user=participant,
                title=f'New Reply: {thread.subject}',
                message=f'{request.user.get_full_name() or request.user.username} has replied to a message thread',
                notification_type='MESSAGE',
                related_message=message,
                link=f'/messages/thread/{thread.id}/'
            )

        messages.success(request, 'Reply sent successfully.')
        return redirect('message_thread', thread_id=thread.id)

    return redirect('message_thread', thread_id=thread.id)

# Announcement Views
@login_required
def announcement_list(request):
    """View for listing announcements"""
    # Get announcements visible to the current user
    announcements = Announcement.objects.filter(
        Q(is_school_wide=True) |
        Q(target_users=request.user) |
        Q(target_grades__pupils__user=request.user)
    ).distinct().order_by('-created_at')

    # Filter by category if provided
    category_id = request.GET.get('category')
    if category_id:
        announcements = announcements.filter(category_id=category_id)

    # Get all categories for filter dropdown
    categories = AnnouncementCategory.objects.all().order_by('name')

    context = {
        'announcements': announcements,
        'categories': categories,
        'selected_category': category_id,
    }

    return render(request, 'communication/announcement_list.html', context)

@login_required
def create_announcement(request):
    """View for creating a new announcement"""
    # Only admins and teachers can create announcements
    if not request.user.is_teacher() and not request.user.is_admin():
        messages.error(request, 'You do not have permission to create announcements.')
        return redirect('announcement_list')

    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        category_id = request.POST.get('category')
        is_school_wide = request.POST.get('is_school_wide') == 'on'
        priority = request.POST.get('priority')

        # Get target grades and users if not school-wide
        target_grade_ids = request.POST.getlist('target_grades')
        target_user_ids = request.POST.getlist('target_users')

        # Validate required fields
        if not all([title, content, priority]):
            messages.error(request, 'Please fill in all required fields.')
            return redirect('create_announcement')

        # Create the announcement
        announcement = Announcement.objects.create(
            title=title,
            content=content,
            category_id=category_id if category_id else None,
            author=request.user,
            is_school_wide=is_school_wide,
            priority=priority
        )

        # Handle file attachment if provided
        if 'attachment' in request.FILES:
            announcement.attachment = request.FILES['attachment']
            announcement.save()

        # Add target grades and users if not school-wide
        if not is_school_wide:
            for grade_id in target_grade_ids:
                announcement.target_grades.add(Grade.objects.get(id=grade_id))

            for user_id in target_user_ids:
                announcement.target_users.add(User.objects.get(id=user_id))

        messages.success(request, 'Announcement created successfully.')
        return redirect('announcement_detail', announcement_id=announcement.id)

    # Get all categories, grades, and users for the form
    categories = AnnouncementCategory.objects.all().order_by('name')
    grades = Grade.objects.all().order_by('name')
    users = User.objects.all().order_by('last_name', 'first_name')

    context = {
        'categories': categories,
        'grades': grades,
        'users': users,
    }

    return render(request, 'communication/announcement_form.html', context)

@login_required
def announcement_detail(request, announcement_id):
    """View for viewing an announcement"""
    announcement = get_object_or_404(Announcement, id=announcement_id)

    # Check if user has permission to view this announcement
    user_can_view = (
        announcement.is_school_wide or
        request.user in announcement.target_users.all() or
        request.user.is_admin() or
        announcement.author == request.user
    )

    if not user_can_view:
        messages.error(request, 'You do not have permission to view this announcement.')
        return redirect('announcement_list')

    # Mark related notifications as read
    notifications = Notification.objects.filter(
        user=request.user,
        related_announcement=announcement,
        is_read=False
    )
    for notification in notifications:
        notification.mark_as_read()

    context = {
        'announcement': announcement,
    }

    return render(request, 'communication/announcement_detail.html', context)

@login_required
def edit_announcement(request, announcement_id):
    """View for editing an announcement"""
    announcement = get_object_or_404(Announcement, id=announcement_id)

    # Check if user has permission to edit this announcement
    if announcement.author != request.user and not request.user.is_admin():
        messages.error(request, 'You do not have permission to edit this announcement.')
        return redirect('announcement_detail', announcement_id=announcement.id)

    # Don't allow editing published announcements
    if announcement.is_published:
        messages.error(request, 'Published announcements cannot be edited.')
        return redirect('announcement_detail', announcement_id=announcement.id)

    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        category_id = request.POST.get('category')
        is_school_wide = request.POST.get('is_school_wide') == 'on'
        priority = request.POST.get('priority')

        # Get target grades and users if not school-wide
        target_grade_ids = request.POST.getlist('target_grades')
        target_user_ids = request.POST.getlist('target_users')

        # Validate required fields
        if not all([title, content, priority]):
            messages.error(request, 'Please fill in all required fields.')
            return redirect('edit_announcement', announcement_id=announcement.id)

        # Update the announcement
        announcement.title = title
        announcement.content = content
        announcement.category_id = category_id if category_id else None
        announcement.is_school_wide = is_school_wide
        announcement.priority = priority

        # Handle file attachment if provided
        if 'attachment' in request.FILES:
            announcement.attachment = request.FILES['attachment']

        announcement.save()

        # Update target grades and users if not school-wide
        if not is_school_wide:
            announcement.target_grades.clear()
            for grade_id in target_grade_ids:
                announcement.target_grades.add(Grade.objects.get(id=grade_id))

            announcement.target_users.clear()
            for user_id in target_user_ids:
                announcement.target_users.add(User.objects.get(id=user_id))
        else:
            announcement.target_grades.clear()
            announcement.target_users.clear()

        messages.success(request, 'Announcement updated successfully.')
        return redirect('announcement_detail', announcement_id=announcement.id)

    # Get all categories, grades, and users for the form
    categories = AnnouncementCategory.objects.all().order_by('name')
    grades = Grade.objects.all().order_by('name')
    users = User.objects.all().order_by('last_name', 'first_name')

    context = {
        'announcement': announcement,
        'categories': categories,
        'grades': grades,
        'users': users,
    }

    return render(request, 'communication/announcement_form.html', context)

@login_required
def publish_announcement(request, announcement_id):
    """View for publishing an announcement"""
    announcement = get_object_or_404(Announcement, id=announcement_id)

    # Check if user has permission to publish this announcement
    if announcement.author != request.user and not request.user.is_admin():
        messages.error(request, 'You do not have permission to publish this announcement.')
        return redirect('announcement_detail', announcement_id=announcement.id)

    if request.method == 'POST':
        # Publish the announcement
        announcement.is_published = True
        announcement.published_at = timezone.now()
        announcement.save()

        # Create notifications for target users
        if announcement.is_school_wide:
            # Notify all users
            for user in User.objects.all():
                if user != announcement.author:  # Don't notify the author
                    Notification.objects.create(
                        user=user,
                        title=f'New Announcement: {announcement.title}',
                        message=f'A new announcement has been published by {announcement.author.get_full_name() or announcement.author.username}',
                        notification_type='ANNOUNCEMENT',
                        related_announcement=announcement,
                        link=f'/announcements/{announcement.id}/'
                    )
        else:
            # Notify targeted users
            for user in announcement.target_users.all():
                if user != announcement.author:  # Don't notify the author
                    Notification.objects.create(
                        user=user,
                        title=f'New Announcement: {announcement.title}',
                        message=f'A new announcement has been published by {announcement.author.get_full_name() or announcement.author.username}',
                        notification_type='ANNOUNCEMENT',
                        related_announcement=announcement,
                        link=f'/announcements/{announcement.id}/'
                    )

            # Notify users in targeted grades
            for grade in announcement.target_grades.all():
                for pupil in grade.pupils.all():
                    if hasattr(pupil, 'user') and pupil.user and pupil.user != announcement.author:
                        Notification.objects.create(
                            user=pupil.user,
                            title=f'New Announcement: {announcement.title}',
                            message=f'A new announcement has been published by {announcement.author.get_full_name() or announcement.author.username}',
                            notification_type='ANNOUNCEMENT',
                            related_announcement=announcement,
                            link=f'/announcements/{announcement.id}/'
                        )

        messages.success(request, 'Announcement published successfully.')
        return redirect('announcement_detail', announcement_id=announcement.id)

    context = {
        'announcement': announcement,
    }

    return render(request, 'communication/publish_announcement.html', context)

# Notification Views
@login_required
def notification_list(request):
    """View for listing notifications"""
    # Get notifications for the current user
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')

    # Filter by type if provided
    notification_type = request.GET.get('type')
    if notification_type:
        notifications = notifications.filter(notification_type=notification_type)

    # Filter by read status if provided
    read_status = request.GET.get('read')
    if read_status == 'read':
        notifications = notifications.filter(is_read=True)
    elif read_status == 'unread':
        notifications = notifications.filter(is_read=False)

    context = {
        'notifications': notifications,
        'selected_type': notification_type,
        'selected_read_status': read_status,
    }

    return render(request, 'communication/notification_list.html', context)

@login_required
def mark_notifications_read(request):
    """View for marking all notifications as read"""
    if request.method == 'POST':
        # Mark all unread notifications as read
        notifications = Notification.objects.filter(user=request.user, is_read=False)
        for notification in notifications:
            notification.mark_as_read()

        messages.success(request, f'{notifications.count()} notifications marked as read.')

        # Redirect back to the notifications list
        return redirect('notification_list')

    return redirect('notification_list')

@login_required
def mark_notification_read(request, notification_id):
    """View for marking a single notification as read"""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)

    if request.method == 'POST':
        notification.mark_as_read()
        messages.success(request, 'Notification marked as read.')

        # Redirect to the notification's link if available, otherwise back to the list
        if notification.link:
            return redirect(notification.link)
        else:
            return redirect('notification_list')

    return redirect('notification_list')

# API endpoints for AJAX
@login_required
def notification_count(request):
    """API endpoint for getting the unread notification count"""
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({'count': count})

@login_required
def recent_notifications(request):
    """API endpoint for getting recent notifications"""
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:5]

    notification_data = []
    for notification in notifications:
        notification_data.append({
            'id': notification.id,
            'title': notification.title,
            'message': notification.message,
            'created_at': notification.created_at.strftime('%Y-%m-%d %H:%M'),
            'is_read': notification.is_read,
            'link': notification.link,
            'type': notification.notification_type,
        })

    return JsonResponse({'notifications': notification_data})
