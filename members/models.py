from django.db import models
from django.contrib.auth.models import User
from phonenumber_field.modelfields import PhoneNumberField
from datetime import date
import os

def member_photo_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/member_photos/<id>/<filename>
    ext = filename.split('.')[-1]
    filename = f'profile_{instance.id}.{ext}'
    return os.path.join('member_photos', filename)

class Member(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('visitor', 'Visitor'),
        ('transferred', 'Transferred'),
    ]
    
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True)
    
    # Personal Information
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    email = models.EmailField(unique=True)
    phone_number = PhoneNumberField(unique=True)
    alternate_phone = PhoneNumberField(blank=True)
    
    # Address
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    
    # Church Information
    date_joined = models.DateField(default=date.today)
    baptism_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    department = models.CharField(max_length=100, blank=True)
    spiritual_gifts = models.TextField(blank=True)
    
    # Photo
    photo = models.ImageField(upload_to=member_photo_path, blank=True, null=True)
    
    # Emergency Contact
    emergency_contact_name = models.CharField(max_length=200)
    emergency_contact_phone = PhoneNumberField()
    emergency_contact_relationship = models.CharField(max_length=100)
    
    # Additional Information
    occupation = models.CharField(max_length=100, blank=True)
    school = models.CharField(max_length=200, blank=True)
    talents = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='members_created')
    
    class Meta:
        ordering = ['last_name', 'first_name']
        indexes = [
            models.Index(fields=['last_name', 'first_name']),
            models.Index(fields=['phone_number']),
            models.Index(fields=['email']),
            models.Index(fields=['status']),
        ]
    
    
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    def full_name(self):
        return f"{self.first_name} {self.middle_name} {self.last_name}".strip()
    
    def age(self):
        from datetime import date
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )
    
    @property
    def photo_url(self):
        if self.photo and hasattr(self.photo, 'url'):
            return self.photo.url
        return '/static/images/default_profile.png'
    
    def save(self, *args, **kwargs):
        # If this is a new member and date_joined wasn't set, set it to today
        if not self.pk and not self.date_joined:
            self.date_joined = date.today()
        super().save(*args, **kwargs)
    
    
    def get_upcoming_birthdays(self, days=30):
        """
        Get members with birthdays in the next X days
        """
        from datetime import date, timedelta
        from django.db.models import Q
        
        today = date.today()
        future_date = today + timedelta(days=days)
        
        # Create Q objects for birthdays in date range
        q_objects = Q()
        
        # For each day in the range
        current_date = today
        while current_date <= future_date:
            q_objects |= Q(
                date_of_birth__month=current_date.month,
                date_of_birth__day=current_date.day
            )
            current_date += timedelta(days=1)
        
        return Member.objects.filter(q_objects).exclude(id=self.id)
    
    @property
    def days_until_birthday(self):
        """
        Calculate days until next birthday
        """
        from datetime import date
        
        today = date.today()
        next_birthday = date(
            today.year,
            self.date_of_birth.month,
            self.date_of_birth.day
        )
        
        if next_birthday < today:
            next_birthday = date(
                today.year + 1,
                self.date_of_birth.month,
                self.date_of_birth.day
            )
        
        return (next_birthday - today).days
    
    @classmethod
    def get_todays_birthdays(cls):
        """
        Get all members with birthdays today
        """
        from datetime import date
        
        today = date.today()
        return cls.objects.filter(
            date_of_birth__month=today.month,
            date_of_birth__day=today.day
        )
    
    @classmethod
    def get_birthday_announcements(cls):
        """
        Get formatted birthday announcements
        """
        birthdays_today = cls.get_todays_birthdays()
        
        announcements = []
        for member in birthdays_today:
            age = member.age()
            announcements.append(
                f"🎉 Happy Birthday {member.first_name}! "
                f"Today they turn {age} years old!"
            )
        
        return announcements

class Family(models.Model):
    RELATIONSHIP_CHOICES = [
        ('parent', 'Parent'),
        ('sibling', 'Sibling'),
        ('spouse', 'Spouse'),
        ('child', 'Child'),
        ('guardian', 'Guardian'),
    ]
    
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='family_members')
    relative = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='related_to')
    relationship = models.CharField(max_length=20, choices=RELATIONSHIP_CHOICES)
    is_primary = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['member', 'relative', 'relationship']
    
    def __str__(self):
        return f"{self.member} - {self.relationship} - {self.relative}"

class Attendance(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='attendances')
    service_date = models.DateField()
    service_type = models.CharField(max_length=50)  # e.g., 'Sunday Service', 'Bible Study'
    attended = models.BooleanField(default=True)
    check_in_time = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-service_date']
        unique_together = ['member', 'service_date', 'service_type']
    
    def __str__(self):
        return f"{self.member} - {self.service_date} - {self.service_type}"
    
    
class AttendanceSession(models.Model):
    SESSION_TYPES = [
        ('sunday_service', 'Sunday Service'),
        ('wednesday_service', 'Wednesday Service'),
        ('friday_service', 'Friday Service'),
        ('bible_study', 'Bible Study'),
        ('youth_meeting', 'Youth Meeting'),
        ('special_event', 'Special Event'),
    ]
    
    session_name = models.CharField(max_length=200)
    session_type = models.CharField(max_length=50, choices=SESSION_TYPES)
    session_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField(null=True, blank=True)
    
    # Location
    venue = models.CharField(max_length=200, blank=True)
    
    # Statistics
    total_present = models.IntegerField(default=0)
    total_absent = models.IntegerField(default=0)
    total_visitors = models.IntegerField(default=0)
    
    # QR Code for check-in
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
    qr_code_data = models.CharField(max_length=255, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_completed = models.BooleanField(default=False)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-session_date', '-start_time']
    
    def __str__(self):
        return f"{self.session_name} - {self.session_date}"
    
    def save(self, *args, **kwargs):
        if not self.qr_code_data:
            import qrcode
            import io
            from django.core.files.base import ContentFile
            
            # Generate QR code data
            qr_data = f"ATTENDANCE:{self.id}:{self.session_date}"
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(qr_data)
            qr.make(fit=True)
            
            img = qr.make_image(fill='black', back_color='white')
            
            # Save to image field
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            filename = f'qr_{self.id}.png'
            
            self.qr_code.save(filename, ContentFile(buffer.getvalue()), save=False)
            self.qr_code_data = qr_data
        
        super().save(*args, **kwargs)