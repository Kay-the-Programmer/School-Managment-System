from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import (
    MessageThread, Message, AnnouncementCategory, 
    Announcement, Notification
)

class MessageInline(admin.TabularInline):
    """Inline admin for Messages within a MessageThread"""
    model = Message
    extra = 0
    fields = ('sender', 'content', 'sent_at', 'read_by_count')
    readonly_fields = ('sent_at', 'read_by_count')

    def read_by_count(self, obj):
        """Return the number of users who have read this message"""
        if obj.pk:
            return obj.read_by.count()
        return 0

    read_by_count.short_description = _('Read by')

@admin.register(MessageThread)
class MessageThreadAdmin(admin.ModelAdmin):
    """Admin interface for the MessageThread model"""
    list_display = ('subject', 'created_at', 'updated_at', 'participant_count', 'message_count')
    search_fields = ('subject',)
    filter_horizontal = ('participants',)
    readonly_fields = ('created_at', 'updated_at')
    inlines = [MessageInline]

    def participant_count(self, obj):
        """Return the number of participants in this thread"""
        return obj.participants.count()

    def message_count(self, obj):
        """Return the number of messages in this thread"""
        return obj.messages.count()

    participant_count.short_description = _('Participants')
    message_count.short_description = _('Messages')

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """Admin interface for the Message model"""
    list_display = ('sender', 'thread_subject', 'short_content', 'sent_at', 'has_attachment', 'read_by_count')
    list_filter = ('sent_at', 'sender')
    search_fields = ('content', 'thread__subject', 'sender__username')
    readonly_fields = ('sent_at',)
    filter_horizontal = ('read_by',)

    fieldsets = (
        (_('Message Information'), {
            'fields': ('thread', 'sender', 'content', 'attachment', 'sent_at')
        }),
        (_('Read Status'), {
            'fields': ('read_by',),
            'classes': ('collapse',),
        }),
    )

    def thread_subject(self, obj):
        """Return the subject of the thread"""
        return obj.thread.subject

    def short_content(self, obj):
        """Return a shortened version of the content"""
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content

    def has_attachment(self, obj):
        """Return whether this message has an attachment"""
        return bool(obj.attachment)

    def read_by_count(self, obj):
        """Return the number of users who have read this message"""
        return obj.read_by.count()

    thread_subject.short_description = _('Thread')
    short_content.short_description = _('Content')
    has_attachment.short_description = _('Attachment')
    has_attachment.boolean = True
    read_by_count.short_description = _('Read by')

@admin.register(AnnouncementCategory)
class AnnouncementCategoryAdmin(admin.ModelAdmin):
    """Admin interface for the AnnouncementCategory model"""
    list_display = ('name', 'description', 'announcement_count')
    search_fields = ('name', 'description')

    def announcement_count(self, obj):
        """Return the number of announcements in this category"""
        return obj.announcements.count()

    announcement_count.short_description = _('Announcements')

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    """Admin interface for the Announcement model"""
    list_display = ('title', 'category', 'author', 'priority', 'is_published', 
                   'published_at', 'expires_at', 'is_school_wide', 'target_count')
    list_filter = ('is_published', 'priority', 'category', 'is_school_wide', 'created_at')
    search_fields = ('title', 'content', 'author__username')
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('target_grades', 'target_users')

    fieldsets = (
        (_('Announcement Information'), {
            'fields': ('title', 'content', 'category', 'author', 'priority', 'attachment')
        }),
        (_('Publication'), {
            'fields': ('is_published', 'published_at', 'expires_at')
        }),
        (_('Targeting'), {
            'fields': ('is_school_wide', 'target_grades', 'target_users'),
            'classes': ('collapse',),
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def target_count(self, obj):
        """Return the number of targets for this announcement"""
        if obj.is_school_wide:
            return _('All')
        return obj.target_grades.count() + obj.target_users.count()

    target_count.short_description = _('Targets')

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Admin interface for the Notification model"""
    list_display = ('user', 'title', 'notification_type', 'created_at', 'is_read', 'read_at')
    list_filter = ('is_read', 'notification_type', 'created_at')
    search_fields = ('title', 'message', 'user__username')
    readonly_fields = ('created_at', 'read_at')

    fieldsets = (
        (_('Notification Information'), {
            'fields': ('user', 'title', 'message', 'notification_type', 'link')
        }),
        (_('Read Status'), {
            'fields': ('is_read', 'read_at')
        }),
        (_('Related Content'), {
            'fields': ('related_announcement', 'related_message'),
            'classes': ('collapse',),
        }),
        (_('Metadata'), {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )

    actions = ['mark_as_read', 'mark_as_unread']

    def mark_as_read(self, request, queryset):
        """Mark selected notifications as read"""
        from django.utils import timezone
        updated = queryset.update(is_read=True, read_at=timezone.now())
        self.message_user(request, _(f'{updated} notifications marked as read.'))

    def mark_as_unread(self, request, queryset):
        """Mark selected notifications as unread"""
        updated = queryset.update(is_read=False, read_at=None)
        self.message_user(request, _(f'{updated} notifications marked as unread.'))

    mark_as_read.short_description = _('Mark selected notifications as read')
    mark_as_unread.short_description = _('Mark selected notifications as unread')
