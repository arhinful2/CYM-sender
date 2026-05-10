from django.db import models
from django.contrib.auth.models import User
from members.models import Member
import uuid



class Message(models.Model):
    MESSAGE_TYPE_CHOICES = [
        ('broadcast', 'Broadcast to All'),
        ('group', 'Group Message'),
        ('individual', 'Individual Message'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPE_CHOICES, default='broadcast')
    subject = models.CharField(max_length=200)
    content = models.TextField()
    
    # Optional member reply link support
    allow_member_replies = models.BooleanField(default=False)
    reply_token = models.UUIDField(default=uuid.uuid4, editable=False)
    
    # For group messages
    recipients = models.ManyToManyField(Member, related_name='received_messages', blank=True)
    
    # For broadcast, we'll track who received it
    is_broadcast = models.BooleanField(default=False)
    
    # Message status
    is_sent = models.BooleanField(default=False)
    is_delivered = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    scheduled_for = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    # For SMS/WhatsApp integration (future enhancement)
    sms_sent = models.BooleanField(default=False)
    whatsapp_sent = models.BooleanField(default=False)
    
    # Soft delete
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.subject} - {self.sender.username} - {self.created_at}"

class MessageResponse(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='responses')
    respondent = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='message_responses')
    response_content = models.TextField()
    respondent_phone = models.CharField(max_length=20, blank=True)
    
    # Response type
    is_acknowledgment = models.BooleanField(default=False)
    is_reply = models.BooleanField(default=False)
    
    # Admin can reply to this response
    admin_reply = models.TextField(blank=True)
    replied_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Soft delete
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['message', 'respondent']
    
    def __str__(self):
        return f"Response from {self.respondent} to {self.message.subject}"
    
    def has_admin_reply(self):
        return bool(self.admin_reply)

class Conversation(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='conversations')
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='conversations')
    
    # Conversation status
    is_read = models.BooleanField(default=False)
    responded = models.BooleanField(default=False)
    
    # Timestamps
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['message', 'member']
        ordering = ['-last_updated']
    
    def __str__(self):
        return f"Conversation: {self.member} - {self.message.subject}"

class SMSLog(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('received', 'Received'),
    ]
    
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='sms_logs', null=True, blank=True)
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='sms_logs')
    phone_number = models.CharField(max_length=20)
    content = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True)
    
    # For incoming messages
    is_incoming = models.BooleanField(default=False)
    response_to = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Provider information
    provider_message_id = models.CharField(max_length=100, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    # Soft delete
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"SMS to {self.member}: {self.status}"


class MessageTemplate(models.Model):
    """Reusable message templates for quick message composition"""
    TEMPLATE_TYPE_CHOICES = [
        ('broadcast', 'Broadcast Template'),
        ('group', 'Group Message Template'),
        ('individual', 'Individual Message Template'),
        ('sms', 'SMS Template'),
        ('email', 'Email Template'),
    ]
    
    name = models.CharField(max_length=100, help_text='Template name for reference')
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPE_CHOICES, default='broadcast')
    subject = models.CharField(max_length=200, blank=True, help_text='Subject line (for email templates)')
    content = models.TextField(help_text='Template content. Use {name}, {member_name}, {date} for placeholders')
    
    # Template metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_templates')
    is_active = models.BooleanField(default=True)
    
    # Category for organization
    category = models.CharField(max_length=50, blank=True, help_text='e.g., Event, Reminder, Announcement')
    description = models.TextField(blank=True, help_text='Notes about when to use this template')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['template_type', 'category', 'name']
        verbose_name = 'Message Template'
        verbose_name_plural = 'Message Templates'
    
    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()})"


from .config import SMSConfiguration, EmailConfiguration    