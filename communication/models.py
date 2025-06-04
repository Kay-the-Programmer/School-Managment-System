from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from pupils.models import Pupil, Grade

class MessageThread(models.Model):
    """
    Model for message threads/conversations between users
    """
    subject = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Participants in the conversation
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='message_threads'
    )

    class Meta:
        verbose_name = _('Message Thread')
        verbose_name_plural = _('Message Threads')
        ordering = ['-updated_at']

    def __str__(self):
        return self.subject

    @property
    def last_message(self):
        """Get the most recent message in this thread"""
        return self.messages.order_by('-sent_at').first()

class Message(models.Model):
    """
    Model for individual messages within a thread
    """
    thread = models.ForeignKey(MessageThread, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    content = models.TextField()
    attachment = models.FileField(upload_to='message_attachments/', blank=True, null=True)
    sent_at = models.DateTimeField(auto_now_add=True)

    # Message read tracking
    read_by = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='read_messages',
        blank=True
    )

    class Meta:
        verbose_name = _('Message')
        verbose_name_plural = _('Messages')
        ordering = ['sent_at']

    def __str__(self):
        return f"{self.sender.username}: {self.content[:50]}..."

    @property
    def is_read_by_all(self):
        """Check if message has been read by all participants"""
        participants = self.thread.participants.all()
        return all(participant in self.read_by.all() for participant in participants if participant != self.sender)

class AnnouncementCategory(models.Model):
    """
    Categories for announcements (e.g., General, Academic, Events)
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = _('Announcement Category')
        verbose_name_plural = _('Announcement Categories')
        ordering = ['name']

    def __str__(self):
        return self.name

class Announcement(models.Model):
    """
    Model for school-wide or targeted announcements
    """
    title = models.CharField(max_length=255)
    content = models.TextField()
    category = models.ForeignKey(
        AnnouncementCategory, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='announcements'
    )

    # Announcement metadata
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='authored_announcements'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Publication control
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(blank=True, null=True)
    expires_at = models.DateTimeField(blank=True, null=True)

    # Targeting
    is_school_wide = models.BooleanField(default=True, help_text=_('If true, announcement is visible to all users'))
    target_grades = models.ManyToManyField(Grade, related_name='announcements', blank=True)
    target_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='targeted_announcements',
        blank=True
    )

    # Attachments
    attachment = models.FileField(upload_to='announcement_attachments/', blank=True, null=True)

    # Priority
    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    ]
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM')

    class Meta:
        verbose_name = _('Announcement')
        verbose_name_plural = _('Announcements')
        ordering = ['-created_at']

    def __str__(self):
        return self.title

class Notification(models.Model):
    """
    Model for system notifications to users
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    title = models.CharField(max_length=255)
    message = models.TextField()

    # Link to related content
    link = models.URLField(blank=True, null=True)

    # Notification metadata
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(blank=True, null=True)

    # Notification type
    TYPE_CHOICES = [
        ('SYSTEM', 'System'),
        ('ATTENDANCE', 'Attendance'),
        ('ASSESSMENT', 'Assessment'),
        ('MESSAGE', 'Message'),
        ('ANNOUNCEMENT', 'Announcement'),
    ]
    notification_type = models.CharField(max_length=15, choices=TYPE_CHOICES, default='SYSTEM')

    # Related objects (using generic relations would be better, but keeping it simple)
    related_announcement = models.ForeignKey(
        Announcement, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='notifications'
    )
    related_message = models.ForeignKey(
        Message, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='notifications'
    )

    class Meta:
        verbose_name = _('Notification')
        verbose_name_plural = _('Notifications')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}: {self.title}"

    def mark_as_read(self):
        """Mark notification as read and save the timestamp"""
        from django.utils import timezone
        self.is_read = True
        self.read_at = timezone.now()
        self.save()
