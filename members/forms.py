from django import forms
from .models import Member
from django.core.exceptions import ValidationError


class MemberRegistrationForm(forms.ModelForm):
    """Form for registering/adding new youth members"""
    
    class Meta:
        model = Member
        fields = [
            'first_name', 'middle_name', 'last_name',
            'date_of_birth', 'gender',
            'email', 'phone_number', 'alternate_phone',
            'address', 'city', 'state', 'postal_code',
            'date_joined', 'baptism_date',
            'status', 'department',
            'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relationship',
            'occupation', 'school',
            'spiritual_gifts', 'talents',
            'notes',
            'photo',
        ]
        
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'First Name',
            }),
            'middle_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Middle Name (Optional)'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Last Name',
            }),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'gender': forms.Select(attrs={
                'class': 'form-select',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email Address',
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Phone Number (e.g., +233xxxxxxxxxx)',
            }),
            'alternate_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Alternate Phone (Optional)'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Street Address',
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'City',
            }),
            'state': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'State/Region',
            }),
            'postal_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Postal Code',
            }),
            'date_joined': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'baptism_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select',
            }),
            'department': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Youth, College, Young Adults (Optional)'
            }),
            'emergency_contact_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Emergency Contact Name',
            }),
            'emergency_contact_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Emergency Contact Phone',
            }),
            'emergency_contact_relationship': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Parent, Sibling, Guardian',
            }),
            'occupation': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Occupation (Optional)'
            }),
            'school': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'School/University (Optional)'
            }),
            'spiritual_gifts': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Spiritual Gifts (Optional)'
            }),
            'talents': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Talents and Skills (Optional)'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Additional Notes (Optional)'
            }),
            'photo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
        }
        
        help_texts = {
            'middle_name': 'Optional',
            'alternate_phone': 'Optional',
            'baptism_date': 'Leave blank if not baptized',
            'department': 'Optional - helps organize members by age group',
            'school': 'Optional',
            'occupation': 'Optional',
            'spiritual_gifts': 'Optional - helps identify member strengths',
            'talents': 'Optional - for event planning and activities',
        }

    def clean_email(self):
        """Validate that email is unique"""
        email = self.cleaned_data.get('email')
        if email:
            # Check if email exists (excluding current member if editing)
            if self.instance.pk:
                if Member.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
                    raise ValidationError('This email is already registered.')
            else:
                if Member.objects.filter(email=email).exists():
                    raise ValidationError('This email is already registered.')
        return email

    def clean_phone_number(self):
        """Validate that phone number is unique"""
        phone_number = self.cleaned_data.get('phone_number')
        if phone_number:
            # Check if phone exists (excluding current member if editing)
            if self.instance.pk:
                if Member.objects.filter(phone_number=phone_number).exclude(pk=self.instance.pk).exists():
                    raise ValidationError('This phone number is already registered.')
            else:
                if Member.objects.filter(phone_number=phone_number).exists():
                    raise ValidationError('This phone number is already registered.')
        return phone_number

    def clean(self):
        """Additional validation"""
        cleaned_data = super().clean()
        date_of_birth = cleaned_data.get('date_of_birth')
        date_joined = cleaned_data.get('date_joined')
        baptism_date = cleaned_data.get('baptism_date')
        
        # Check that date_of_birth is in the past
        from datetime import date
        if date_of_birth is not None and date_of_birth >= date.today():
            self.add_error('date_of_birth', 'Date of birth must be in the past.')
        
        # Check that date_joined is not in the future
        if date_joined is not None and date_joined > date.today():
            self.add_error('date_joined', 'Date joined cannot be in the future.')
        
        # Check that baptism_date is after date_of_birth
        if baptism_date is not None and date_of_birth is not None and baptism_date < date_of_birth:
            self.add_error('baptism_date', 'Baptism date cannot be before date of birth.')
        
        return cleaned_data
