from django.db import models
from django.contrib.auth.models import User, Group
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('super_admin', 'Super Admin'),
        ('admin', 'Church Admin'),
        ('pastor', 'Pastor'),
        ('leader', 'Youth Leader'),
        ('volunteer', 'Volunteer'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='userprofile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='volunteer')
    phone_number = models.CharField(max_length=20, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    bio = models.TextField(blank=True)
    
    # Permissions
    can_view_members = models.BooleanField(default=True)
    can_edit_members = models.BooleanField(default=False)
    can_delete_members = models.BooleanField(default=False)
    can_send_messages = models.BooleanField(default=False)
    can_view_reports = models.BooleanField(default=False)
    can_manage_events = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"

# FIXED: Create user profile when user is created
@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """
    Create or update user profile
    """
    # Use get_or_create to handle both new and existing users
    profile, created = UserProfile.objects.get_or_create(user=instance)
    
    # If it's a new profile, set default permissions based on role
    if created:
        if instance.is_superuser:
            profile.role = 'super_admin'
            profile.can_view_members = True
            profile.can_edit_members = True
            profile.can_delete_members = True
            profile.can_send_messages = True
            profile.can_view_reports = True
            profile.can_manage_events = True
        elif instance.is_staff:
            profile.role = 'admin'
            profile.can_view_members = True
            profile.can_edit_members = True
            profile.can_send_messages = True
            profile.can_view_reports = True
        profile.save()
    
    # Add user to appropriate group
    try:
        group_name = profile.get_role_display().replace(' ', '_').lower()
        group, _ = Group.objects.get_or_create(name=group_name)
        instance.groups.add(group)
    except:
        pass