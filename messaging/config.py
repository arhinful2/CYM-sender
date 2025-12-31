from django.db import models
from django.core.exceptions import ValidationError

class SMSConfiguration(models.Model):
    """SMS Provider Configuration"""
    PROVIDER_CHOICES = [
        ('twilio', 'Twilio'),
        ('africastalking', 'Africa\'s Talking'),
        ('termii', 'Termii'),
        ('hubtel', 'Hubtel'),
        ('manual', 'Manual/Manual'),
    ]
    
    provider = models.CharField(max_length=50, choices=PROVIDER_CHOICES, default='manual')
    is_active = models.BooleanField(default=True)
    
    # Twilio Settings
    twilio_account_sid = models.CharField(max_length=100, blank=True)
    twilio_auth_token = models.CharField(max_length=100, blank=True)
    twilio_phone_number = models.CharField(max_length=20, blank=True)
    
    # Africa's Talking Settings
    africastalking_username = models.CharField(max_length=100, blank=True)
    africastalking_api_key = models.CharField(max_length=100, blank=True)
    africastalking_sender_id = models.CharField(max_length=20, blank=True)
    
    # General Settings
    default_sender_name = models.CharField(max_length=50, default='Church')
    cost_per_sms = models.DecimalField(max_digits=5, decimal_places=2, default=0.05)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'SMS Configuration'
        verbose_name_plural = 'SMS Configuration'
    
    def __str__(self):
        return f"SMS Config - {self.get_provider_display()}"
    
    def clean(self):
        """Validate configuration based on provider"""
        if self.provider == 'twilio' and not (self.twilio_account_sid and self.twilio_auth_token and self.twilio_phone_number):
            raise ValidationError('Twilio requires Account SID, Auth Token, and Phone Number')
        if self.provider == 'africastalking' and not (self.africastalking_username and self.africastalking_api_key):
            raise ValidationError('Africa\'s Talking requires Username and API Key')

class EmailConfiguration(models.Model):
    """Email SMTP Configuration"""
    PROVIDER_CHOICES = [
        ('gmail', 'Gmail'),
        ('outlook', 'Outlook/Hotmail'),
        ('yahoo', 'Yahoo'),
        ('sendgrid', 'SendGrid'),
        ('custom', 'Custom SMTP'),
    ]
    
    provider = models.CharField(max_length=50, choices=PROVIDER_CHOICES, default='gmail')
    is_active = models.BooleanField(default=True)
    
    # SMTP Settings
    smtp_host = models.CharField(max_length=200, default='smtp.gmail.com')
    smtp_port = models.IntegerField(default=587)
    smtp_username = models.EmailField(blank=True)
    smtp_password = models.CharField(max_length=100, blank=True)
    
    # Email Settings
    from_email = models.EmailField(default='noreply@yourchurch.com')
    from_name = models.CharField(max_length=100, default='Youth Church')
    
    # Security
    use_tls = models.BooleanField(default=True)
    use_ssl = models.BooleanField(default=False)
    
    # Testing
    test_email = models.EmailField(blank=True, help_text='Email to send test messages to')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Email Configuration'
        verbose_name_plural = 'Email Configuration'
    
    def __str__(self):
        return f"Email Config - {self.get_provider_display()}"
    
    def clean(self):
        """Auto-fill settings based on provider"""
        if self.provider == 'gmail':
            self.smtp_host = 'smtp.gmail.com'
            self.smtp_port = 587
            self.use_tls = True
            self.use_ssl = False
        
        elif self.provider == 'outlook':
            self.smtp_host = 'smtp.office365.com'
            self.smtp_port = 587
            self.use_tls = True
            self.use_ssl = False
        
        elif self.provider == 'yahoo':
            self.smtp_host = 'smtp.mail.yahoo.com'
            self.smtp_port = 587
            self.use_tls = True
            self.use_ssl = False
        
        elif self.provider == 'sendgrid':
            self.smtp_host = 'smtp.sendgrid.net'
            self.smtp_port = 587
            self.use_tls = True
            self.use_ssl = False