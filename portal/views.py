from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as auth_logout
from django.contrib import messages
from django.db.models import Q
from members.models import Member
from messaging.models import Message, MessageResponse, Conversation
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.utils import timezone  # ADD THIS IMPORT
import json
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponseForbidden
from datetime import date, timedelta

import csv
from django.http import HttpResponse # Make sure this import exists
from datetime import date  # If not already imported
from members.models import Attendance  # If not already imported
from django.shortcuts import redirect  # If not already imported


def home(request):
    """Homepage - redirects to portal if logged in, otherwise to login"""
    if request.user.is_authenticated:
        return redirect('admin_portal')
    else:
        return redirect('login')

def staff_required(view_func):
    """Decorator to ensure user is staff member"""
    decorated_view_func = user_passes_test(
        lambda u: u.is_authenticated and u.is_staff,
        login_url='/accounts/login/'
    )(view_func)
    return decorated_view_func

def permission_required(permission_name):
    """Decorator to check specific permissions"""
    def decorator(view_func):
        def wrapped_view(request, *args, **kwargs):
            if request.user.is_authenticated:
                try:
                    profile = request.user.userprofile
                    if getattr(profile, permission_name, False):
                        return view_func(request, *args, **kwargs)
                except:
                    pass
            return HttpResponseForbidden("You don't have permission to access this page.")
        return wrapped_view
    return decorator

# Use decorators in your views
@staff_required
@permission_required('can_view_members')


@staff_member_required
def admin_portal(request): 
    """Main admin portal dashboard"""
    total_members = Member.objects.count()
    active_members = Member.objects.filter(status='active').count()
    recent_members = Member.objects.order_by('-date_joined')[:5]
    
    # Message statistics
    total_messages = Message.objects.count()
    recent_messages = Message.objects.order_by('-created_at')[:5]
    
    # Recent responses
    recent_responses = MessageResponse.objects.select_related('respondent', 'message').order_by('-created_at')[:5]
    
    context = {
        'total_members': total_members,
        'active_members': active_members,
        'recent_members': recent_members,
        'total_messages': total_messages,
        'recent_messages': recent_messages,
        'recent_responses': recent_responses,
    }
    return render(request, 'portal/dashboard.html', context)




@staff_member_required
def member_search(request):
    """Advanced member search with AI-like suggestions"""
    query = request.GET.get('q', '')
    members = Member.objects.all()
    
    if query:
        # Search in multiple fields with OR condition
        members = members.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(middle_name__icontains=query) |
            Q(phone_number__icontains=query) |
            Q(email__icontains=query) |
            Q(address__icontains=query) |
            Q(city__icontains=query)
        ).distinct()
    
    # Pagination
    paginator = Paginator(members, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'query': query,
        'page_obj': page_obj,
        'total_results': members.count(),
    }
    return render(request, 'portal/member_search.html', context)





@staff_member_required
def member_detail(request, pk):
    """Member detail view"""
    member = get_object_or_404(Member, pk=pk)
    
    # Get attendance records
    attendance = member.attendances.all()[:10]
    
    # Get family members
    family = member.family_members.all()
    
    # Get message conversations
    conversations = member.conversations.select_related('message').all()[:10]
    
    context = {
        'member': member,
        'attendance': attendance,
        'family': family,
        'conversations': conversations,
    }
    return render(request, 'portal/member_detail.html', context)

@staff_member_required
def messaging_dashboard(request):
    """Messaging dashboard"""
    # Get all messages sent by current user
    sent_messages = Message.objects.filter(sender=request.user).order_by('-created_at')
    
    # Get messages with responses
    messages_with_responses = sent_messages.filter(responses__isnull=False).distinct()
    
    # Get recent responses
    recent_responses = MessageResponse.objects.filter(
        message__sender=request.user
    ).select_related('respondent', 'message').order_by('-created_at')[:10]
    
    context = {
        'sent_messages': sent_messages,
        'messages_with_responses': messages_with_responses,
        'recent_responses': recent_responses,
    }
    return render(request, 'portal/messaging_dashboard.html', context)

@staff_member_required
def compose_message(request):
    """Compose and send messages"""
    if request.method == 'POST':
        subject = request.POST.get('subject')
        content = request.POST.get('content')
        message_type = request.POST.get('message_type', 'broadcast')
        recipient_ids = request.POST.getlist('recipients')
        
        template_id = request.POST.get('template_id')
        if template_id:
            template = MessageTemplate.objects.get(id=template_id)
            templates = MessageTemplate.objects.filter(is_active=True)
            return render(request, 'portal/compose_message.html', {
                'members': members,
                'templates': templates})
       
        # Create message
        message = Message.objects.create(
            sender=request.user,
            subject=subject,
            content=content,
            message_type=message_type,
            is_sent=True,
            sent_at=timezone.now()
        )
        
        # Add recipients
        if message_type != 'broadcast' and recipient_ids:
            recipients = Member.objects.filter(id__in=recipient_ids)
            message.recipients.set(recipients)
            message.is_broadcast = False
        else:
            message.is_broadcast = True
        
        message.save()
        
        # Create conversations for recipients
        if message.is_broadcast:
            recipients = Member.objects.all()
        else:
            recipients = message.recipients.all()
        
        for member in recipients:
            Conversation.objects.get_or_create(
                message=message,
                member=member
            )
        
        messages.success(request, f'Message sent to {recipients.count()} members!')
        return redirect('messaging_dashboard')
    
    # GET request - show form
    members = Member.objects.all()
    return render(request, 'portal/compose_message.html', {'members': members})
    
    
@staff_member_required
def message_responses(request, message_id):
    """View responses to a specific message"""
    message = get_object_or_404(Message, id=message_id, sender=request.user)
    responses = message.responses.select_related('respondent').all()
    
    if request.method == 'POST' and 'reply' in request.POST:
        response_id = request.POST.get('response_id')
        reply_content = request.POST.get('reply_content')
        
        response = get_object_or_404(MessageResponse, id=response_id)
        response.admin_reply = reply_content
        response.replied_at = timezone.now()
        response.save()
        
        messages.success(request, 'Reply sent successfully!')
        return redirect('message_responses', message_id=message_id)
    
    context = {
        'message': message,
        'responses': responses,
    }
    return render(request, 'portal/message_responses.html', context)

@staff_member_required
def member_messages(request, member_id):
    """View all messages with a specific member"""
    member = get_object_or_404(Member, id=member_id)
    conversations = Conversation.objects.filter(member=member).select_related('message')
    
    context = {
        'member': member,
        'conversations': conversations,
    }
    return render(request, 'portal/member_messages.html', context)

@staff_member_required
def analytics_dashboard(request):
    """Analytics and reporting dashboard"""
    from django.db.models import Count, Q
    import datetime
    from django.utils import timezone
    
    # Member statistics
    total_members = Member.objects.count()
    active_members = Member.objects.filter(status='active').count()
    inactive_members = Member.objects.filter(status='inactive').count()
    
    # Gender distribution
    gender_stats = Member.objects.values('gender').annotate(count=Count('id'))
    
    # Age groups
    today = timezone.now().date()
    age_groups = {
        '13_17': Member.objects.filter(
            date_of_birth__lte=today - datetime.timedelta(days=13*365),
            date_of_birth__gte=today - datetime.timedelta(days=18*365)
        ).count(),
        '18_25': Member.objects.filter(
            date_of_birth__lte=today - datetime.timedelta(days=18*365),
            date_of_birth__gte=today - datetime.timedelta(days=26*365)
        ).count(),
        '26_35': Member.objects.filter(
            date_of_birth__lte=today - datetime.timedelta(days=26*365),
            date_of_birth__gte=today - datetime.timedelta(days=36*365)
        ).count(),
        '36+': Member.objects.filter(
            date_of_birth__lte=today - datetime.timedelta(days=36*365)
        ).count(),
    }
    
    # Message statistics
    total_messages = Message.objects.filter(sender=request.user).count()
    broadcast_messages = Message.objects.filter(sender=request.user, is_broadcast=True).count()
    individual_messages = Message.objects.filter(sender=request.user, is_broadcast=False).count()
    
    # Response rates
    messages_with_responses = Message.objects.filter(sender=request.user, responses__isnull=False).distinct().count()
    response_rate = (messages_with_responses / total_messages * 100) if total_messages > 0 else 0
    
    context = {
        'total_members': total_members,
        'active_members': active_members,
        'inactive_members': inactive_members,
        'gender_stats': gender_stats,
        'age_groups': age_groups,
        'total_messages': total_messages,
        'broadcast_messages': broadcast_messages,
        'individual_messages': individual_messages,
        'response_rate': round(response_rate, 2),
    }
    return render(request, 'portal/analytics.html', context)

@staff_member_required
def ajax_search_members(request):
    """AJAX endpoint for member search suggestions"""
    query = request.GET.get('q', '')
    
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    members = Member.objects.filter(
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query) |
        Q(phone_number__icontains=query) |
        Q(email__icontains=query)
    )[:10]
    
    results = []
    for member in members:
        results.append({
            'id': member.id,
            'text': f"{member.full_name()} - {member.phone_number}",
            'name': member.full_name(),
            'phone': str(member.phone_number),
            'photo_url': member.photo_url,
        })
    
    return JsonResponse({'results': results})


def birthday_tracker(request):
    """View upcoming birthdays"""
    today = date.today()
    next_30_days = today + timedelta(days=30)
    
    # Get birthdays in next 30 days
    birthdays = Member.objects.filter(
        Q(date_of_birth__month=today.month, date_of_birth__day__gte=today.day) |
        Q(date_of_birth__month=next_30_days.month, date_of_birth__day__lte=next_30_days.day)
    ).order_by('date_of_birth__month', 'date_of_birth__day')
    
    # Calculate days until birthday
    for member in birthdays:
        member.days_until_birthday = member.days_until_birthday()
    
    return render(request, 'portal/birthdays.html', {'birthdays': birthdays})

def send_birthday_wishes(request, member_id):
    """Send automated birthday wishes"""
    member = get_object_or_404(Member, id=member_id)
    
    # Create birthday message
    message = f"🎉 Happy Birthday {member.first_name}! 🎂\n"
    message += f"May God bless you abundantly on your special day!"
    
    # Send message
    Message.objects.create(
        sender=request.user,
        subject=f"Happy Birthday {member.first_name}!",
        content=message,
        message_type='individual',
        is_sent=True,
        sent_at=timezone.now()
    )
    
    messages.success(request, f"Birthday wish sent to {member.full_name()}!")
    return redirect('birthday_tracker')


@login_required
def export_members_csv(request):
    """Export all members to CSV"""
    # Create the HttpResponse object with CSV header
    response = HttpResponse(
        content_type='text/csv',
        headers={'Content-Disposition': 'attachment; filename="members.csv"'},
    )
    
    writer = csv.writer(response)
    writer.writerow(['ID', 'First Name', 'Last Name', 'Email', 'Phone', 'Status', 'Date Joined', 'Address', 'City'])
    
    members = Member.objects.all()
    for member in members:
        writer.writerow([
            member.id,
            member.first_name,
            member.last_name,
            member.email,
            member.phone_number,
            member.status,
            member.date_joined,
            member.address,
            member.city
        ])
    
    return response

@login_required
def quick_attendance(request):
    """Quick attendance taking interface"""
    if request.method == 'POST':
        service_type = request.POST.get('service_type')
        service_date = request.POST.get('service_date', date.today())
        member_ids = request.POST.getlist('members')
        
        # Convert string date to date object if needed
        if isinstance(service_date, str):
            from datetime import datetime
            service_date = datetime.strptime(service_date, '%Y-%m-%d').date()
        
        count = 0
        for member_id in member_ids:
            try:
                Attendance.objects.create(
                    member_id=member_id,
                    service_date=service_date,
                    service_type=service_type,
                    attended=True
                )
                count += 1
            except Exception as e:
                messages.error(request, f"Error recording attendance for member {member_id}: {str(e)}")
        
        messages.success(request, f"Attendance recorded for {count} members!")
        return redirect('quick_attendance')
    
    # GET request - show form
    # Get active members
    active_members = Member.objects.filter(status='active')
    
    # Predefined service types
    SERVICE_TYPES = [
        ('sunday_service', 'Sunday Service'),
        ('bible_study', 'Bible Study'),
        ('prayer_meeting', 'Prayer Meeting'),
        ('youth_meeting', 'Youth Meeting'),
        ('special_event', 'Special Event'),
    ]
    
    return render(request, 'portal/quick_attendance.html', {
        'members': active_members,
        'today': date.today(),
        'service_types': SERVICE_TYPES,
    })
    
    
    
@login_required
def setup_sms_email(request):
    """Simple SMS and Email setup page"""
    
    # This is a temporary placeholder view
    # We'll implement the full SMS/Email setup later
    
    context = {
        'title': 'SMS & Email Setup',
        'message': 'SMS and Email setup will be available after migrations.'
    }
    
    return render(request, 'portal/setup_sms_email.html', context)

@login_required  
def send_test_message(request):
    """Send test message endpoint"""
    # Placeholder for now
    from django.http import JsonResponse
    return JsonResponse({
        'success': False, 
        'message': 'Feature not available yet. Complete migrations first.'
    })