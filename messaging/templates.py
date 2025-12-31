from django.db import models
import uuid

class MessageTemplate(models.Model):
    TEMPLATE_TYPES = [
        ('welcome', 'Welcome Message'),
        ('announcement', 'Announcement'),
        ('reminder', 'Reminder'),
        ('birthday', 'Birthday Greeting'),
        ('followup', 'Follow-up'),
        ('prayer', 'Prayer Request'),
        ('event', 'Event Invitation'),
        ('giving', 'Giving Receipt'),
        ('custom', 'Custom'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    template_type = models.CharField(max_length=50, choices=TEMPLATE_TYPES)
    
    # Content
    subject = models.CharField(max_length=200)
    content = models.TextField(help_text="Use {{member.name}}, {{member.phone}}, etc. for variables")
    
    # Variables available
    available_variables = models.TextField(
        help_text="Comma-separated list of available variables",
        default="member.name, member.phone, member.email, church.name, date, time"
    )
    
    # Format
    is_sms = models.BooleanField(default=True)
    is_email = models.BooleanField(default=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()})"
    
    def render_template(self, context):
        """
        Render template with context variables
        """
        content = self.content
        for key, value in context.items():
            placeholder = f"{{{{{key}}}}}"
            content = content.replace(placeholder, str(value))
        return content