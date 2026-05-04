from django.db import models
from django.contrib.auth.models import User
from members.models import Member
import uuid

class PrayerRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'Being Prayed For'),
        ('answered', 'Answered'),
        ('closed', 'Closed'),
    ]
    
    PRIVACY_CHOICES = [
        ('public', 'Public - Everyone can see'),
        ('private', 'Private - Only leaders can see'),
        ('anonymous', 'Anonymous - No name shown'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='prayer_requests')
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=100, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    privacy = models.CharField(max_length=20, choices=PRIVACY_CHOICES, default='public')
    
    # Prayer warriors
    prayed_by = models.ManyToManyField(User, related_name='prayers_prayed', blank=True)
    prayer_count = models.IntegerField(default=0)
    
    # Answer
    answer_description = models.TextField(blank=True)
    answered_date = models.DateField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.member}"
    
    @property
    def is_anonymous(self):
        return self.privacy == 'anonymous'
    
    @property
    def display_name(self):
        if self.privacy == 'anonymous':
            return "Anonymous"
        return str(self.member)

class PrayerResponse(models.Model):
    prayer_request = models.ForeignKey(PrayerRequest, on_delete=models.CASCADE, related_name='responses')
    responder = models.ForeignKey(User, on_delete=models.CASCADE)
    response_text = models.TextField()
    
    # Can be a prayer or encouragement
    is_prayer = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Response to {self.prayer_request.title}"