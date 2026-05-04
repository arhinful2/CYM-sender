from django.db import models
from django.contrib.auth.models import User
from members.models import Member
import uuid

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('message', 'New Message'),
        ('response', 'Message Response'),
        ('prayer', 'Prayer Request'),
        ('event', 'Event Reminder'),
        ('attendance', 'Attendance Alert'),
        ('birthday', 'Birthday'),
        ('anniversary', 'Anniversary'),
        ('system', 'System Notification'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    
    # Content
    title = models.CharField(max_length=200)
    message = models.TextField()
    
    # Link/Reference
    target_url = models.URLField(blank=True)
    reference_id = models.CharField(max_length=100, blank=True)
    
    # Status
    is_read = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    
    # Priority
    priority = models.IntegerField(
        choices=[(1, 'Low'), (2, 'Medium'), (3, 'High'), (4, 'Urgent')],
        default=2
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.recipient.username}"
    
    def mark_as_read(self):
        from django.utils import timezone
        self.is_read = True
        self.read_at = timezone.now()
        self.save()