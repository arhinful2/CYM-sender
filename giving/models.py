from django.db import models
from members.models import Member
import uuid

class Donation(models.Model):
    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('mobile_money', 'Mobile Money'),
        ('bank_transfer', 'Bank Transfer'),
        ('card', 'Credit/Debit Card'),
        ('check', 'Check'),
        ('online', 'Online Payment'),
    ]
    
    DONATION_TYPES = [
        ('tithe', 'Tithe'),
        ('offering', 'Offering'),
        ('seed', 'Seed/Sowing'),
        ('building', 'Building Fund'),
        ('missions', 'Missions'),
        ('benevolence', 'Benevolence'),
        ('other', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    member = models.ForeignKey(Member, on_delete=models.SET_NULL, null=True, blank=True, related_name='donations')
    
    # Donor info (if not a member)
    donor_name = models.CharField(max_length=200, blank=True)
    donor_email = models.EmailField(blank=True)
    donor_phone = models.CharField(max_length=20, blank=True)
    is_anonymous = models.BooleanField(default=False)
    
    # Donation details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    donation_type = models.CharField(max_length=50, choices=DONATION_TYPES)
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHODS)
    
    # Reference/Transaction info
    transaction_id = models.CharField(max_length=100, blank=True)
    reference_number = models.CharField(max_length=100, blank=True)
    
    # Date and time
    donation_date = models.DateField()
    recorded_at = models.DateTimeField(auto_now_add=True)
    recorded_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    
    # Status
    is_confirmed = models.BooleanField(default=False)
    is_recurring = models.BooleanField(default=False)
    
    # Notes
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-donation_date', '-recorded_at']
    
    def __str__(self):
        donor = self.donor_name or (self.member.full_name() if self.member else 'Anonymous')
        return f"{donor} - ${self.amount} - {self.get_donation_type_display()}"
    
    @property
    def donor_display(self):
        if self.is_anonymous:
            return "Anonymous"
        if self.member:
            return str(self.member)
        return self.donor_name

class RecurringDonation(models.Model):
    FREQUENCY_CHOICES = [
        ('weekly', 'Weekly'),
        ('biweekly', 'Bi-weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ]
    
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='recurring_donations')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    donation_type = models.CharField(max_length=50, choices=Donation.DONATION_TYPES)
    payment_method = models.CharField(max_length=50, choices=Donation.PAYMENT_METHODS)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='monthly')
    
    # Bank/Mobile details
    account_number = models.CharField(max_length=100, blank=True)
    bank_name = models.CharField(max_length=100, blank=True)
    mobile_number = models.CharField(max_length=20, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    
    # Next payment
    next_payment_date = models.DateField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['member', '-next_payment_date']
    
    def __str__(self):
        return f"{self.member} - ${self.amount} {self.frequency}"