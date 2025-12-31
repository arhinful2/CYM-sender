from django.db import models
from django.contrib.auth.models import User
from members.models import Member
import uuid

class Event(models.Model):
    EVENT_TYPES = [
        ('service', 'Church Service'),
        ('bible_study', 'Bible Study'),
        ('prayer', 'Prayer Meeting'),
        ('youth', 'Youth Meeting'),
        ('outreach', 'Outreach'),
        ('social', 'Social Event'),
        ('training', 'Training'),
        ('other', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    description = models.TextField(blank=True)
    
    # Date and time
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_all_day = models.BooleanField(default=False)
    
    # Location
    venue = models.CharField(max_length=200)
    address = models.TextField(blank=True)
    online_link = models.URLField(blank=True)
    
    # Organizer
    organizer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    coordinator = models.ForeignKey(Member, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Participants
    expected_participants = models.IntegerField(default=0)
    participants = models.ManyToManyField(Member, through='EventRegistration', related_name='events')
    
    # Status
    is_published = models.BooleanField(default=False)
    is_cancelled = models.BooleanField(default=False)
    
    # Reminders
    send_reminder = models.BooleanField(default=True)
    reminder_days = models.IntegerField(default=1)
    
    # Files
    event_image = models.ImageField(upload_to='event_images/', blank=True, null=True)
    documents = models.FileField(upload_to='event_docs/', blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['start_date']
    
    def __str__(self):
        return f"{self.title} - {self.get_event_type_display()}"
    
    @property
    def participant_count(self):
        return self.participants.count()
    
    @property
    def registration_count(self):
        return self.registrations.filter(is_confirmed=True).count()

class EventRegistration(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('attended', 'Attended'),
        ('cancelled', 'Cancelled'),
    ]
    
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations')
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='event_registrations')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    is_confirmed = models.BooleanField(default=False)
    
    # Additional info
    number_of_guests = models.IntegerField(default=0)
    special_requirements = models.TextField(blank=True)
    
    # Check-in
    check_in_time = models.DateTimeField(null=True, blank=True)
    check_in_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    registered_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['event', 'member']
    
    def __str__(self):
        return f"{self.member} - {self.event.title} ({self.status})"

class EventReminder(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='reminders')
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    reminder_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    reminder_type = models.CharField(max_length=20, choices=[('sms', 'SMS'), ('email', 'Email')])
    
    class Meta:
        unique_together = ['event', 'member']
    
    def __str__(self):
        return f"Reminder for {self.member} - {self.event.title}"