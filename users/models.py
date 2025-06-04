from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    """
    Custom User model with role-based permissions for the school management system.
    Extends Django's AbstractUser to add role field for distinguishing between Teachers and Admins.
    """

    class Role(models.TextChoices):
        ADMIN = 'ADMIN', _('Admin')
        TEACHER = 'TEACHER', _('Teacher')

    # Default role is teacher
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.TEACHER,
        verbose_name=_('Role'),
        help_text=_('Designates the role and permissions of the user')
    )

    # Additional fields
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)

    def is_admin(self):
        """Check if user has admin role"""
        return self.role == self.Role.ADMIN

    def is_teacher(self):
        """Check if user has teacher role"""
        return self.role == self.Role.TEACHER

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
