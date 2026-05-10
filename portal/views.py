from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as auth_logout
from django.contrib import messages
from django.db.models import Q
from django.urls import reverse
from members.models import Member
from messaging.models import Message, MessageResponse, Conversation, SMSLog
from messaging.services import MessageService
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.utils import timezone  # ADD THIS IMPORT
import json
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponseForbidden
from django.http import HttpResponseBadRequest
from datetime import date, timedelta
import re
from django.core.exceptions import ValidationError

import csv
from django.http import HttpResponse  # Make sure this import exists
from datetime import date  # If not already imported
from members.models import Attendance  # If not already imported
from django.shortcuts import redirect  # If not already imported
from django.db.models import Case, When, Value, IntegerField
from django.db.models.functions import ExtractMonth
from django.utils import timezone as django_timezone


def home(request):
    """Homepage - redirects to portal if logged in, otherwise to login"""
    if not request.user.is_authenticated:
        return redirect('login')

    if request.user.is_staff or request.user.is_superuser:
        return redirect('admin_portal')

    return render(request, 'portal/access_denied.html')


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
    from datetime import date
    from django.db.models import Q
    
    total_members = Member.objects.count()
    active_members = Member.objects.filter(status='active').count()
    recent_members = Member.objects.order_by('-date_joined')[:5]

    # Message statistics
    total_messages = Message.objects.filter(is_deleted=False).count()
    recent_messages = Message.objects.filter(
        is_deleted=False).order_by('-created_at')[:5]

    # Recent responses
    recent_responses = MessageResponse.objects.filter(
        is_deleted=False).select_related(
        'respondent', 'message').order_by('-created_at')[:5]

    # Birthday members - today's birthdays
    today = date.today()
    birthday_members = Member.objects.filter(
        Q(date_of_birth__month=today.month) & 
        Q(date_of_birth__day=today.day)
    ).exclude(date_of_birth__isnull=True).order_by('first_name')

    context = {
        'total_members': total_members,
        'active_members': active_members,
        'recent_members': recent_members,
        'total_messages': total_messages,
        'recent_messages': recent_messages,
        'recent_responses': recent_responses,
        'birthday_members': birthday_members,
    }
    return render(request, 'portal/dashboard.html', context)


@staff_member_required
def member_search(request):
    """Advanced member search with AI-like suggestions"""
    query = request.GET.get('q', '').strip()
    scope = request.GET.get('scope', 'name').strip().lower()
    status_filter = request.GET.get('status', 'all').strip().lower()
    members = Member.objects.all()

    if query:
        tokens = [token for token in re.split(r'\s+', query) if token]

        # Build token-aware filters. Each token must match at least one field.
        token_q = Q()
        for token in tokens:
            if scope == 'phone':
                token_q &= Q(phone_number__icontains=token)
            elif scope == 'email':
                token_q &= Q(email__icontains=token)
            elif scope == 'location':
                token_q &= (Q(address__icontains=token) | Q(
                    city__icontains=token) | Q(state__icontains=token))
            elif scope == 'all':
                token_q &= (
                    Q(first_name__icontains=token) |
                    Q(last_name__icontains=token) |
                    Q(middle_name__icontains=token) |
                    Q(phone_number__icontains=token) |
                    Q(email__icontains=token) |
                    Q(address__icontains=token) |
                    Q(city__icontains=token)
                )
            else:
                # Default and recommended: name-focused search for precise results.
                token_q &= (
                    Q(first_name__icontains=token) |
                    Q(last_name__icontains=token) |
                    Q(middle_name__icontains=token)
                )

        members = members.filter(token_q).distinct()

        # Relevance ordering for cleaner result quality.
        members = members.annotate(
            match_priority=Case(
                When(first_name__iexact=query, then=Value(0)),
                When(last_name__iexact=query, then=Value(1)),
                When(middle_name__iexact=query, then=Value(2)),
                When(first_name__istartswith=query, then=Value(3)),
                When(last_name__istartswith=query, then=Value(4)),
                default=Value(9),
                output_field=IntegerField(),
            )
        ).order_by('match_priority', 'last_name', 'first_name')

    if status_filter in {'active', 'inactive', 'visitor', 'transferred'}:
        members = members.filter(status=status_filter)

    quick_members = Member.objects.filter(
        status='active').order_by('-date_joined', 'last_name')[:8]

    # Pagination
    paginator = Paginator(members, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'query': query,
        'scope': scope,
        'status_filter': status_filter,
        'page_obj': page_obj,
        'total_results': members.count(),
        'quick_members': quick_members,
    }
    return render(request, 'portal/member_search.html', context)


@staff_member_required
def member_detail(request, pk):
    """Member detail view"""
    member = get_object_or_404(Member, pk=pk)

    # Get attendance records
    attendance = member.attendances.filter(is_deleted=False)[:10]

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
def add_member(request):
    """Add new member via website form"""
    from members.forms import MemberRegistrationForm

    if request.method == 'POST':
        form = MemberRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            member = form.save(commit=False)
            member.created_by = request.user
            member.save()
            messages.success(
                request, f'✓ {member.full_name()} has been added successfully!')
            return redirect('member_detail', pk=member.pk)
        else:
            # Show errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = MemberRegistrationForm()

    context = {
        'form': form,
        'title': 'Register New Member',
        'is_add': True,
    }
    return render(request, 'portal/member_form.html', context)


@staff_member_required
def edit_member(request, pk):
    """Edit existing member"""
    from members.forms import MemberRegistrationForm

    member = get_object_or_404(Member, pk=pk)

    if request.method == 'POST':
        form = MemberRegistrationForm(
            request.POST, request.FILES, instance=member)
        if form.is_valid():
            member = form.save(commit=False)
            # Note: you may want to add this field to Member model
            member.updated_by = request.user
            member.save()
            messages.success(
                request, f'✓ {member.full_name()} has been updated successfully!')
            return redirect('member_detail', pk=member.pk)
        else:
            # Show errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = MemberRegistrationForm(instance=member)

    context = {
        'form': form,
        'member': member,
        'title': f'Edit {member.full_name()}',
        'is_add': False,
    }
    return render(request, 'portal/member_form.html', context)


@staff_member_required
def messaging_dashboard(request):
    """Messaging dashboard"""
    from messaging.models import MessageTemplate, MessageResponse

    # Database-wide message stats so the dashboard reflects real system data.
    sent_messages = Message.objects.filter(is_deleted=False).order_by('-created_at')

    # Messages that have at least one active response.
    messages_with_responses = Message.objects.filter(
        responses__is_deleted=False,
        is_deleted=False,
    ).distinct().order_by('-created_at')

    # Recent responses across the system.
    recent_responses = MessageResponse.objects.filter(
        is_deleted=False
    ).select_related('respondent', 'message').order_by('-created_at')[:10]

    # Unread means responses that have not been answered by an admin yet.
    unread_responses = MessageResponse.objects.filter(
        is_deleted=False,
        admin_reply='',
    ).count()

    templates = MessageTemplate.objects.filter(
        is_active=True).order_by('-updated_at')

    context = {
        'sent_messages': sent_messages,
        'total_messages_count': sent_messages.count(),
        'messages_with_responses_count': messages_with_responses.count(),
        'recent_responses': recent_responses,
        'recent_responses_count': recent_responses.count(),
        'unread_responses_count': unread_responses,
        'templates': templates,
        'templates_count': templates.count(),
    }
    return render(request, 'portal/messaging_dashboard.html', context)


@staff_member_required
def messaging_status(request):
    """Return JSON with messaging-related counts for quick hosted diagnostics."""
    # Import here to avoid top-level import issues
    from messaging.models import MessageTemplate

    templates_qs = MessageTemplate.objects.filter(is_active=True)
    total_templates = templates_qs.count()
    templates_preview = list(templates_qs.order_by('category', 'name').values_list('name', flat=True)[:20])

    total_messages = Message.objects.filter(is_deleted=False).count()
    messages_with_responses = Message.objects.filter(responses__is_deleted=False, is_deleted=False).distinct().count()
    recent_responses_count = MessageResponse.objects.filter(is_deleted=False).count()
    unread_responses = MessageResponse.objects.filter(is_deleted=False, admin_reply='').count()

    data = {
        'total_templates': total_templates,
        'templates_preview': templates_preview,
        'total_messages': total_messages,
        'messages_with_responses': messages_with_responses,
        'recent_responses_count': recent_responses_count,
        'unread_responses': unread_responses,
    }
    return JsonResponse(data)


@staff_member_required
def delete_message(request, message_id):
    """Soft delete a message (move to trash)."""
    if request.method != 'POST':
        return HttpResponseBadRequest('Invalid request method')

    message = get_object_or_404(Message, id=message_id)
    message_subject = message.subject
    message.is_deleted = True
    message.deleted_at = timezone.now()
    message.save()
    messages.success(
        request, f'Message "{message_subject}" moved to trash.')

    next_url = request.POST.get('next') or request.META.get(
        'HTTP_REFERER') or '/portal/messaging/'
    return redirect(next_url)


@staff_member_required
def delete_message_response(request, response_id):
    """Soft delete a message response (move to trash)."""
    if request.method != 'POST':
        return HttpResponseBadRequest('Invalid request method')

    response = get_object_or_404(MessageResponse, id=response_id)
    message_id = response.message_id
    respondent_id = response.respondent_id
    response.is_deleted = True
    response.deleted_at = timezone.now()
    response.save()

    # If no active responses remain for this message/member pair, clear the conversation responded state.
    if not MessageResponse.objects.filter(message_id=message_id, respondent_id=respondent_id, is_deleted=False).exists():
        Conversation.objects.filter(
            message_id=message_id, member_id=respondent_id).update(responded=False)

    messages.success(request, 'Response moved to trash.')
    next_url = request.POST.get('next') or request.META.get(
        'HTTP_REFERER') or f'/portal/messaging/{message_id}/responses/'
    return redirect(next_url)


@staff_member_required
def restore_message(request, message_id):
    """Restore a soft-deleted message from trash."""
    if request.method != 'POST':
        return HttpResponseBadRequest('Invalid request method')

    message = get_object_or_404(Message, id=message_id, is_deleted=True)
    message_subject = message.subject
    message.is_deleted = False
    message.deleted_at = None
    message.save()
    messages.success(
        request, f'Message "{message_subject}" restored from trash.')

    next_url = request.POST.get('next') or request.META.get(
        'HTTP_REFERER') or '/portal/messaging/trash/'
    return redirect(next_url)


@staff_member_required
def restore_message_response(request, response_id):
    """Restore a soft-deleted message response from trash."""
    if request.method != 'POST':
        return HttpResponseBadRequest('Invalid request method')

    response = get_object_or_404(
        MessageResponse, id=response_id, is_deleted=True)
    response.is_deleted = False
    response.deleted_at = None
    response.save()
    messages.success(request, 'Response restored from trash.')

    next_url = request.POST.get('next') or request.META.get(
        'HTTP_REFERER') or '/portal/messaging/trash/'
    return redirect(next_url)


@staff_member_required
def permanently_delete_message(request, message_id):
    """Permanently delete a soft-deleted message."""
    if request.method != 'POST':
        return HttpResponseBadRequest('Invalid request method')

    message = get_object_or_404(Message, id=message_id, is_deleted=True)
    message_subject = message.subject
    message.delete()
    messages.success(
        request, f'Message "{message_subject}" permanently deleted.')

    next_url = request.POST.get('next') or request.META.get(
        'HTTP_REFERER') or '/portal/messaging/trash/'
    return redirect(next_url)


@staff_member_required
def permanently_delete_message_response(request, response_id):
    """Permanently delete a soft-deleted message response."""
    if request.method != 'POST':
        return HttpResponseBadRequest('Invalid request method')

    response = get_object_or_404(
        MessageResponse, id=response_id, is_deleted=True)
    response.delete()
    messages.success(request, 'Response permanently deleted.')

    next_url = request.POST.get('next') or request.META.get(
        'HTTP_REFERER') or '/portal/messaging/trash/'
    return redirect(next_url)


@staff_member_required
def trash_view(request):
    """View trash/deleted messages and responses."""
    action = request.POST.get('action')
    selected_ids = request.POST.getlist('selected_ids')

    if action == 'restore_messages' and selected_ids:
        Message.objects.filter(id__in=selected_ids, is_deleted=True).update(
            is_deleted=False,
            deleted_at=None
        )
        messages.success(request, f'{len(selected_ids)} message(s) restored.')
    elif action == 'restore_responses' and selected_ids:
        MessageResponse.objects.filter(id__in=selected_ids, is_deleted=True).update(
            is_deleted=False,
            deleted_at=None
        )
        messages.success(request, f'{len(selected_ids)} response(s) restored.')
    elif action == 'delete_messages' and selected_ids:
        Message.objects.filter(id__in=selected_ids, is_deleted=True).delete()
        messages.success(
            request, f'{len(selected_ids)} message(s) permanently deleted.')
    elif action == 'delete_responses' and selected_ids:
        MessageResponse.objects.filter(
            id__in=selected_ids, is_deleted=True).delete()
        messages.success(
            request, f'{len(selected_ids)} response(s) permanently deleted.')
    elif action == 'empty_trash':
        Message.objects.filter(is_deleted=True).delete()
        MessageResponse.objects.filter(is_deleted=True).delete()
        messages.success(request, 'Trash emptied.')

    # Get deleted messages and responses
    deleted_messages = Message.objects.filter(
        is_deleted=True).order_by('-deleted_at')
    deleted_responses = MessageResponse.objects.filter(is_deleted=True).select_related(
        'respondent', 'message').order_by('-deleted_at')

    # Pagination
    page_number = request.GET.get('page', 1)
    paginator = Paginator(deleted_messages, 20)
    messages_page = paginator.get_page(page_number)

    context = {
        'deleted_messages': messages_page,
        'deleted_responses': deleted_responses[:50],
        'total_deleted': deleted_messages.count() + deleted_responses.count(),
    }
    return render(request, 'portal/trash.html', context)


@staff_member_required
def bulk_delete_messages(request):
    """Bulk soft-delete messages."""
    if request.method != 'POST':
        return HttpResponseBadRequest('Invalid request method')

    selected_ids = request.POST.getlist('selected_ids')
    if selected_ids:
        Message.objects.filter(id__in=selected_ids, is_deleted=False).update(
            is_deleted=True,
            deleted_at=timezone.now()
        )
        messages.success(
            request, f'{len(selected_ids)} message(s) moved to trash.')

    next_url = request.POST.get('next') or request.META.get(
        'HTTP_REFERER') or '/portal/messaging/'
    return redirect(next_url)


@staff_member_required
def bulk_delete_responses(request):
    """Bulk soft-delete message responses."""
    if request.method != 'POST':
        return HttpResponseBadRequest('Invalid request method')

    selected_ids = request.POST.getlist('selected_ids')
    if selected_ids:
        MessageResponse.objects.filter(id__in=selected_ids, is_deleted=False).update(
            is_deleted=True,
            deleted_at=timezone.now()
        )
        messages.success(
            request, f'{len(selected_ids)} response(s) moved to trash.')

    next_url = request.POST.get('next') or request.META.get(
        'HTTP_REFERER') or '/portal/messaging/'
    return redirect(next_url)


@staff_member_required
def compose_message(request):
    """Compose and send messages"""
    from messaging.models import MessageTemplate

    if request.method == 'POST':
        subject = request.POST.get('subject')
        content = request.POST.get('content')
        message_type = request.POST.get('message_type', 'broadcast')
        allow_member_replies = request.POST.get('allow_member_replies') == 'on'
        recipient_ids = request.POST.getlist('recipients')

        # Filter out empty strings from recipient_ids to prevent ValueError
        recipient_ids = [rid for rid in recipient_ids if rid and rid.strip()]

        # Handle comma-separated values (in case they come as '3,2' instead of separate entries)
        split_ids = []
        for rid in recipient_ids:
            if ',' in rid:
                split_ids.extend(rid.split(','))
            else:
                split_ids.append(rid)
        recipient_ids = split_ids

        # Convert to integers
        try:
            recipient_ids = [int(rid.strip())
                             for rid in recipient_ids if rid.strip()]
        except (ValueError, TypeError):
            recipient_ids = []

        # Create message
        message = Message.objects.create(
            sender=request.user,
            subject=subject,
            content=content,
            message_type=message_type,
            allow_member_replies=allow_member_replies,
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

        # Send SMS to recipients
        sms_sent_count = 0
        sms_failed_count = 0

        for member in recipients:
            if member.phone_number:
                # Send SMS
                phone = str(member.phone_number)
                outgoing_content = content
                if allow_member_replies:
                    reply_url = request.build_absolute_uri(reverse('member_message_reply', kwargs={
                        'message_id': message.id,
                        'member_id': member.id,
                        'token': message.reply_token,
                    }))
                    outgoing_content = f"{content}\n\nReply here: {reply_url}\nType your response and submit."

                sms_result = MessageService.send_sms(
                    phone,
                    f"{subject}\n\n{outgoing_content}"
                )

                # Create SMS Log
                sms_log = SMSLog.objects.create(
                    message=message,
                    member=member,
                    phone_number=phone,
                    content=outgoing_content,
                    status='pending'
                )

                if sms_result.get('success'):
                    sms_log.status = 'sent'
                    sms_log.provider_message_id = sms_result.get(
                        'message_id', '')
                    sms_log.sent_at = timezone.now()
                    sms_sent_count += 1
                else:
                    sms_log.status = 'failed'
                    sms_log.error_message = sms_result.get(
                        'error', 'Unknown error')
                    sms_failed_count += 1

                sms_log.save()

        # Update message SMS status
        if sms_sent_count > 0:
            message.sms_sent = True
            message.save()

        # Success message with SMS status
        success_msg = f'Message sent to {recipients.count()} members!'
        if sms_sent_count > 0:
            success_msg += f' SMS delivered to {sms_sent_count} members.'
        if sms_failed_count > 0:
            success_msg += f' {sms_failed_count} SMS failed.'

        messages.success(request, success_msg)
        return redirect('messaging_dashboard')

    # GET request - show form
    from messaging.models import MessageTemplate
    
    # Support gender filtering in query params
    gender_filter = request.GET.get('gender', '')  # '', 'M', 'F', or 'O'
    
    if gender_filter in ['M', 'F', 'O']:
        members = Member.objects.filter(gender=gender_filter)
    else:
        members = Member.objects.all()
    
    templates = MessageTemplate.objects.filter(
        is_active=True).order_by('category', 'name')
    
    context = {
        'members': members,
        'templates': templates,
        'selected_gender_filter': gender_filter,
    }
    
    return render(request, 'portal/compose_message.html', context)


def member_message_reply(request, message_id, member_id, token):
    """Public reply page for a specific member and message"""
    message = get_object_or_404(
        Message,
        id=message_id,
        reply_token=token,
        is_deleted=False,
        allow_member_replies=True,
    )
    member = get_object_or_404(Member, id=member_id)

    if not message.is_broadcast and not message.recipients.filter(id=member.id).exists():
        return HttpResponseForbidden("This reply link is not valid for this member.")

    existing_response = MessageResponse.objects.filter(
        message=message,
        respondent=member,
        is_deleted=False,
    ).first()

    if request.method == 'POST':
        response_content = request.POST.get('response_content', '').strip()

        if not response_content:
            return render(request, 'portal/message_reply.html', {
                'message': message,
                'member': member,
                'existing_response': existing_response,
                'error': 'Please type a response before submitting.',
            })

        response, _created = MessageResponse.objects.update_or_create(
            message=message,
            respondent=member,
            defaults={
                'response_content': response_content,
                'is_reply': True,
                'respondent_phone': str(member.phone_number or ''),
            }
        )

        conversation, _created = Conversation.objects.get_or_create(
            message=message,
            member=member,
        )
        conversation.responded = True
        conversation.is_read = True
        conversation.save(update_fields=['responded', 'is_read', 'last_updated'])

        return render(request, 'portal/message_reply.html', {
            'message': message,
            'member': member,
            'existing_response': response,
            'success': 'Your response has been submitted successfully.',
        })

    return render(request, 'portal/message_reply.html', {
        'message': message,
        'member': member,
        'existing_response': existing_response,
    })


@staff_member_required
def quick_announcement(request):
    """Quick broadcast announcement to all members"""
    if request.method == 'POST':
        title = request.POST.get('title', 'Announcement')
        content = request.POST.get('content', '').strip()

        # Validate content is not empty
        if not content:
            messages.error(request, 'Announcement content cannot be empty.')
            return redirect('admin_portal')

        try:
            # Create message as broadcast
            message = Message.objects.create(
                sender=request.user,
                subject=title,
                content=content,
                message_type='broadcast',
                is_broadcast=True,
                is_sent=True,
                sent_at=timezone.now()
            )

            # Get all active members
            recipients = Member.objects.filter(status='active')

            # Create conversations for all members
            for member in recipients:
                Conversation.objects.get_or_create(
                    message=message,
                    member=member
                )

            # Send SMS to all members with phone numbers
            sms_sent_count = 0
            sms_failed_count = 0

            for member in recipients:
                if member.phone_number:
                    phone = str(member.phone_number)
                    sms_result = MessageService.send_sms(
                        phone,
                        f"{title}\n\n{content}"
                    )

                    # Create SMS Log
                    sms_log = SMSLog.objects.create(
                        message=message,
                        member=member,
                        phone_number=phone,
                        content=content,
                        status='pending'
                    )

                    if sms_result.get('success'):
                        sms_log.status = 'sent'
                        sms_log.provider_message_id = sms_result.get(
                            'message_id', '')
                        sms_log.sent_at = timezone.now()
                        sms_sent_count += 1
                    else:
                        sms_log.status = 'failed'
                        sms_log.error_message = sms_result.get(
                            'error', 'Unknown error')
                        sms_failed_count += 1

                    sms_log.save()

            # Update message SMS status
            if sms_sent_count > 0:
                message.sms_sent = True
                message.save()

            # Build success message
            success_msg = f'Announcement sent to {recipients.count()} members!'
            if sms_sent_count > 0:
                success_msg += f' SMS delivered to {sms_sent_count} members.'
            if sms_failed_count > 0:
                success_msg += f' {sms_failed_count} SMS failed.'

            messages.success(request, success_msg)

        except Exception as e:
            messages.error(request, f'Error sending announcement: {str(e)}')

        return redirect('admin_portal')

    return redirect('admin_portal')


@staff_member_required
def message_responses(request, message_id):
    """View responses to a specific message"""
    message = get_object_or_404(
        Message, id=message_id, sender=request.user, is_deleted=False)
    responses = message.responses.filter(
        is_deleted=False).select_related('respondent').all()

    if request.method == 'POST' and 'reply' in request.POST:
        response_id = request.POST.get('response_id')
        reply_content = request.POST.get('reply_content')

        response = get_object_or_404(
            MessageResponse, id=response_id, is_deleted=False)
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
    conversations = Conversation.objects.filter(
        member=member, message__is_deleted=False).select_related('message')

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
    visitor_members = Member.objects.filter(status='visitor').count()

    # Gender distribution from the database with stable labels.
    gender_counts = {
        'M': Member.objects.filter(gender='M').count(),
        'F': Member.objects.filter(gender='F').count(),
        'O': Member.objects.filter(gender='O').count(),
    }

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

    # Attendance charts from the database.
    attendance_by_service = Attendance.objects.filter(is_deleted=False).values('service_type').annotate(
        count=Count('id')
    ).order_by('service_type')
    attendance_by_month = Attendance.objects.filter(
        is_deleted=False,
        service_date__year=today.year
    ).annotate(
        month_num=ExtractMonth('service_date')
    ).values('month_num').annotate(
        count=Count('id')
    ).order_by('month_num')

    # Weekly attendance for the last 8 weeks.
    week_labels = []
    week_counts = []
    week_end = today
    for _ in range(8):
        week_start = week_end - datetime.timedelta(days=6)
        week_labels.insert(
            0, f"{week_start.strftime('%d %b')} - {week_end.strftime('%d %b')}")
        week_counts.insert(0, Attendance.objects.filter(
            is_deleted=False,
            service_date__gte=week_start,
            service_date__lte=week_end,
        ).count())
        week_end = week_start - datetime.timedelta(days=1)

    current_week_start = today - datetime.timedelta(days=today.weekday())
    current_month_start = today.replace(day=1)
    current_week_total = Attendance.objects.filter(
        is_deleted=False, service_date__gte=current_week_start, service_date__lte=today).count()
    current_month_total = Attendance.objects.filter(
        is_deleted=False, service_date__gte=current_month_start, service_date__lte=today).count()
    today_attendance_count = Attendance.objects.filter(
        is_deleted=False, service_date=today).count()

    # Message statistics
    total_messages = Message.objects.filter(
        sender=request.user, is_deleted=False).count()
    broadcast_messages = Message.objects.filter(
        sender=request.user, is_broadcast=True, is_deleted=False).count()
    individual_messages = Message.objects.filter(
        sender=request.user, is_broadcast=False, is_deleted=False).count()

    # Response rates
    messages_with_responses = Message.objects.filter(
        sender=request.user, responses__is_deleted=False, is_deleted=False).distinct().count()
    response_rate = (messages_with_responses /
                     total_messages * 100) if total_messages > 0 else 0

    service_labels = {
        'sunday_service': 'Sunday Service',
        'wednesday_service': 'Wednesday Service',
        'friday_service': 'Friday Service',
        'bible_study': 'Bible Study',
        'prayer_meeting': 'Prayer Meeting',
        'youth_meeting': 'Youth Meeting',
        'special_event': 'Special Event',
    }

    month_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May',
                    'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    month_counts = [0] * 12
    for row in attendance_by_month:
        month_index = int(row['month_num']) - \
            1 if row.get('month_num') else None
        if month_index is not None and 0 <= month_index < 12:
            month_counts[month_index] = row['count']

    context = {
        'total_members': total_members,
        'active_members': active_members,
        'inactive_members': inactive_members,
        'visitor_members': visitor_members,
        'age_groups': age_groups,
        'total_messages': total_messages,
        'broadcast_messages': broadcast_messages,
        'individual_messages': individual_messages,
        'response_rate': round(response_rate, 2),
        'gender_chart_labels': json.dumps(['Male', 'Female', 'Other']),
        'gender_chart_data': json.dumps([
            gender_counts['M'],
            gender_counts['F'],
            gender_counts['O'],
        ]),
        'age_chart_labels': json.dumps(['13-17', '18-25', '26-35', '36+']),
        'age_chart_data': json.dumps([
            age_groups['13_17'],
            age_groups['18_25'],
            age_groups['26_35'],
            age_groups['36+'],
        ]),
        'attendance_service_labels': json.dumps([
            service_labels.get(
                row['service_type'], row['service_type'].replace('_', ' ').title())
            for row in attendance_by_service
        ]),
        'attendance_service_data': json.dumps([row['count'] for row in attendance_by_service]),
        'attendance_month_labels': json.dumps(month_labels),
        'attendance_month_data': json.dumps(month_counts),
        'attendance_week_labels': json.dumps(week_labels),
        'attendance_week_data': json.dumps(week_counts),
        'current_week_total': current_week_total,
        'current_month_total': current_month_total,
        'today_attendance_count': today_attendance_count,
    }
    return render(request, 'portal/analytics.html', context)


@staff_member_required
def ajax_search_members(request):
    """AJAX endpoint for member search suggestions"""
    query = request.GET.get('q', '')
    status = request.GET.get('status', '')
    gender = request.GET.get('gender', '')  # NEW: Gender filter support
    get_all = request.GET.get('all', '')

    # Start with base queryset, applying gender filter if specified
    base_qs = Member.objects.all()
    if gender in ['M', 'F', 'O']:
        base_qs = base_qs.filter(gender=gender)

    # Handle "Select All Members" request
    if get_all == 'true':
        members = base_qs[:100]  # Limit to 100 for safety
    # Handle "Select Active Members" request
    elif status == 'active':
        members = base_qs.filter(status='active')[:100]
    # Handle search query
    elif len(query) >= 2:
        members = base_qs.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(phone_number__icontains=query) |
            Q(email__icontains=query)
        )[:10]
    else:
        return JsonResponse({'results': []})

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
        Q(date_of_birth__month=next_30_days.month,
          date_of_birth__day__lte=next_30_days.day)
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
    writer.writerow(['ID', 'First Name', 'Last Name', 'Email',
                    'Phone', 'Status', 'Date Joined', 'Address', 'City'])

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

        # Normalize member ids to ints
        try:
            member_ids = [int(mid) for mid in member_ids]
        except Exception:
            member_ids = []

        if not service_type:
            messages.error(
                request, 'Please select a service type before saving attendance.')
            return redirect('quick_attendance')

        # Find already recorded attendances for these members
        existing = Attendance.objects.filter(
            member_id__in=member_ids,
            service_date=service_date,
            service_type=service_type,
            is_deleted=False
        ).values_list('member_id', flat=True)
        existing_ids = set(existing)

        deleted_records = Attendance.objects.filter(
            member_id__in=member_ids,
            service_date=service_date,
            service_type=service_type,
            is_deleted=True,
        ).select_related('member')
        deleted_map = {record.member_id: record for record in deleted_records}

        # Prepare list of members to create attendance for
        to_create = []
        skipped = []
        members_qs = Member.objects.filter(id__in=member_ids)
        members_map = {m.id: m for m in members_qs}

        for mid in member_ids:
            if mid in existing_ids:
                m = members_map.get(mid)
                if m:
                    skipped.append(m.full_name() if callable(
                        getattr(m, 'full_name', None)) else str(m))
                continue
            if mid in deleted_map:
                restored = deleted_map[mid]
                restored.is_deleted = False
                restored.deleted_at = None
                restored.attended = True
                restored.save(
                    update_fields=['is_deleted', 'deleted_at', 'attended'])
                created_count += 1
                continue
            # create Attendance instance (but don't save yet)
            to_create.append(Attendance(
                member_id=mid,
                service_date=service_date,
                service_type=service_type,
                attended=True
            ))

        created_count = 0
        for attendance in to_create:
            saved_attendance, created = Attendance.objects.get_or_create(
                member_id=attendance.member_id,
                service_date=attendance.service_date,
                service_type=attendance.service_type,
                defaults={'attended': True}
            )
            if created:
                created_count += 1
            else:
                member = members_map.get(attendance.member_id)
                if member:
                    skipped.append(member.full_name() if callable(
                        getattr(member, 'full_name', None)) else str(member))

        # Success and skipped messages
        if created_count > 0:
            messages.success(
                request, f'Attendance recorded for {created_count} member(s)!')
        else:
            messages.info(request, 'Attendance recorded for 0 members.')

        if skipped:
            # show skipped member names in a warning
            names = ', '.join(skipped[:20])
            more = len(skipped) - len(skipped[:20])
            if more > 0:
                names = f"{names} and {more} more"
            messages.warning(
                request, f"These members were already recorded for {service_type} on {service_date}: {names}")

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

    # Today's attendance stats (all service types)
    today = date.today()
    today_attendance_count = Attendance.objects.filter(
        service_date=today, is_deleted=False).count()
    total_active = active_members.count()
    attendance_rate = round(
        (today_attendance_count / total_active * 100), 2) if total_active > 0 else 0
    today_attendance_records = Attendance.objects.filter(
        service_date=today,
        is_deleted=False,
    ).select_related('member').order_by('service_type', 'member__last_name', 'member__first_name')

    return render(request, 'portal/quick_attendance.html', {
        'members': active_members,
        'today': today,
        'service_types': SERVICE_TYPES,
        'today_attendance_count': today_attendance_count,
        'attendance_rate': attendance_rate,
        'today_attendance_records': today_attendance_records,
    })


@staff_member_required
def check_attendance(request):
    """AJAX endpoint to check which selected members already have attendance for a date/service."""
    if request.method not in ('GET', 'POST'):
        return JsonResponse({'error': 'Invalid method'}, status=400)

    service_type = request.POST.get(
        'service_type') or request.GET.get('service_type')
    service_date = request.POST.get(
        'service_date') or request.GET.get('service_date')
    member_ids = request.POST.getlist(
        'member_ids[]') or request.GET.getlist('member_ids[]')

    # parse date
    try:
        from datetime import datetime
        if isinstance(service_date, str) and service_date:
            service_date = datetime.strptime(service_date, '%Y-%m-%d').date()
    except Exception:
        service_date = None

    try:
        member_ids = [int(m) for m in member_ids]
    except Exception:
        member_ids = []

    result = {'already': []}
    if service_type and service_date and member_ids:
        existing = Attendance.objects.filter(
            member_id__in=member_ids,
            service_date=service_date,
            service_type=service_type,
            is_deleted=False
        ).select_related('member')
        for a in existing:
            result['already'].append(
                {'id': a.member_id, 'name': a.member.full_name()})

    return JsonResponse(result)


def _build_attendance_queryset(request, include_deleted=False):
    SERVICE_TYPES = [
        ('sunday_service', 'Sunday Service'),
        ('bible_study', 'Bible Study'),
        ('prayer_meeting', 'Prayer Meeting'),
        ('youth_meeting', 'Youth Meeting'),
        ('special_event', 'Special Event'),
    ]

    qs = Attendance.objects.select_related(
        'member').order_by('-service_date', '-check_in_time')
    if include_deleted:
        qs = qs.filter(is_deleted=True)
    else:
        qs = qs.filter(is_deleted=False)

    service_type = request.GET.get('service_type')
    date_str = request.GET.get('date')
    from_date_str = request.GET.get('from_date')
    to_date_str = request.GET.get('to_date')
    member_q = request.GET.get('member')

    if service_type:
        qs = qs.filter(service_type=service_type)
    if date_str:
        try:
            from datetime import datetime
            date_val = datetime.strptime(date_str, '%Y-%m-%d').date()
            qs = qs.filter(service_date=date_val)
        except Exception:
            pass
    if from_date_str:
        try:
            from datetime import datetime
            from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
            qs = qs.filter(service_date__gte=from_date)
        except Exception:
            pass
    if to_date_str:
        try:
            from datetime import datetime
            to_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()
            qs = qs.filter(service_date__lte=to_date)
        except Exception:
            pass
    if member_q:
        qs = qs.filter(
            Q(member__first_name__icontains=member_q) |
            Q(member__last_name__icontains=member_q) |
            Q(member__middle_name__icontains=member_q) |
            Q(member__phone_number__icontains=member_q)
        )

    return {
        'SERVICE_TYPES': SERVICE_TYPES,
        'qs': qs,
        'service_type': service_type or '',
        'date': date_str or '',
        'from_date': from_date_str or '',
        'to_date': to_date_str or '',
        'member_q': member_q or '',
        'include_deleted': include_deleted,
    }


@staff_member_required
def attendance_history(request):
    """Show attendance records with filters, export CSV, edit, restore, and delete links."""
    filter_state = _build_attendance_queryset(
        request, include_deleted=request.GET.get('deleted') == '1')
    qs = filter_state['qs']
    SERVICE_TYPES = filter_state['SERVICE_TYPES']
    show_deleted = filter_state['include_deleted']

    total_records = qs.count()
    total_members = qs.values('member_id').distinct().count()
    today = date.today()
    today_records = qs.filter(service_date=today).count()
    latest_record = qs.first()
    deleted_total = Attendance.objects.filter(is_deleted=True).count()
    active_total = Attendance.objects.filter(is_deleted=False).count()

    # Export CSV
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="attendance_export.csv"'
        writer = csv.writer(response)
        writer.writerow(['Member ID', 'Member Name', 'Service Date',
                        'Service Type', 'Attended', 'Check-In Time', 'Notes'])
        for a in qs:
            recorded_at = a.check_in_time if hasattr(
                a, 'check_in_time') else ''
            member_name = a.member.full_name() if hasattr(
                a.member, 'full_name') else str(a.member)
            writer.writerow([a.member.id, member_name, a.service_date,
                            a.service_type, a.attended, recorded_at, a.notes])
        return response

    if request.GET.get('print') == '1':
        return render(request, 'portal/attendance_report.html', {
            'records': qs,
            'service_types': SERVICE_TYPES,
            'service_type': filter_state['service_type'],
            'date': filter_state['date'],
            'from_date': filter_state['from_date'],
            'to_date': filter_state['to_date'],
            'member_q': filter_state['member_q'],
            'show_deleted': show_deleted,
            'total_records': total_records,
            'total_members': total_members,
            'today_records': today_records,
            'latest_record': latest_record,
            'active_total': active_total,
            'deleted_total': deleted_total,
        })

    # Pagination
    paginator = Paginator(qs, 50)
    page = request.GET.get('page')
    records = paginator.get_page(page)

    context = {
        'records': records,
        'service_types': SERVICE_TYPES,
        'service_type': filter_state['service_type'],
        'date': filter_state['date'],
        'from_date': filter_state['from_date'],
        'to_date': filter_state['to_date'],
        'member_q': filter_state['member_q'],
        'show_deleted': show_deleted,
        'total_records': total_records,
        'total_members': total_members,
        'today_records': today_records,
        'latest_record': latest_record,
        'active_total': active_total,
        'deleted_total': deleted_total,
    }
    return render(request, 'portal/attendance_history.html', context)


@staff_member_required
def delete_attendance(request, attendance_id):
    if request.method != 'POST':
        return HttpResponseBadRequest('Invalid request method for deletion.')

    try:
        a = Attendance.objects.get(pk=attendance_id)
        member_name = a.member.full_name() if hasattr(
            a.member, 'full_name') else str(a.member)
        service_date = a.service_date
        a.is_deleted = True
        a.deleted_at = django_timezone.now()
        a.save(update_fields=['is_deleted', 'deleted_at'])
        messages.success(
            request, f'Attendance record for {member_name} on {service_date} moved to trash.')
    except Attendance.DoesNotExist:
        messages.error(request, 'Attendance record not found.')

    return redirect('attendance_history')


@staff_member_required
def restore_attendance(request, attendance_id):
    if request.method != 'POST':
        return HttpResponseBadRequest('Invalid request method for restore.')

    attendance = get_object_or_404(
        Attendance, pk=attendance_id, is_deleted=True)
    duplicate_exists = Attendance.objects.filter(
        member=attendance.member,
        service_date=attendance.service_date,
        service_type=attendance.service_type,
        is_deleted=False,
    ).exclude(pk=attendance.pk).exists()
    if duplicate_exists:
        messages.error(
            request, 'A live attendance record already exists for that member and service.')
        return redirect('attendance_history')

    attendance.is_deleted = False
    attendance.deleted_at = None
    attendance.save(update_fields=['is_deleted', 'deleted_at'])
    messages.success(request, 'Attendance record restored successfully.')
    return redirect('attendance_history?deleted=1')


@staff_member_required
def permanently_delete_attendance(request, attendance_id):
    if request.method != 'POST':
        return HttpResponseBadRequest('Invalid request method for permanent deletion.')

    attendance = get_object_or_404(
        Attendance, pk=attendance_id, is_deleted=True)
    attendance.delete()
    messages.success(request, 'Attendance record permanently deleted.')
    return redirect('attendance_history?deleted=1')


@staff_member_required
def edit_attendance(request, attendance_id):
    attendance = get_object_or_404(Attendance, pk=attendance_id)
    service_types = [
        ('sunday_service', 'Sunday Service'),
        ('bible_study', 'Bible Study'),
        ('prayer_meeting', 'Prayer Meeting'),
        ('youth_meeting', 'Youth Meeting'),
        ('special_event', 'Special Event'),
    ]

    if request.method == 'POST':
        service_type = request.POST.get('service_type')
        service_date_str = request.POST.get('service_date')
        attended = 'attended' in request.POST
        notes = request.POST.get('notes', '').strip()

        try:
            from datetime import datetime
            service_date = datetime.strptime(
                service_date_str, '%Y-%m-%d').date()
        except Exception:
            messages.error(request, 'Please provide a valid service date.')
            return redirect('edit_attendance', attendance_id=attendance_id)

        if not service_type:
            messages.error(request, 'Please choose a service type.')
            return redirect('edit_attendance', attendance_id=attendance_id)

        duplicate_exists = Attendance.objects.filter(
            member=attendance.member,
            service_date=service_date,
            service_type=service_type,
        ).exclude(pk=attendance.pk).exists()
        if duplicate_exists:
            messages.error(
                request, 'Another attendance record already exists for that member, date, and service type.')
            return redirect('edit_attendance', attendance_id=attendance_id)

        attendance.service_type = service_type
        attendance.service_date = service_date
        attendance.attended = attended
        attendance.notes = notes
        if attendance.is_deleted:
            attendance.is_deleted = False
            attendance.deleted_at = None
        attendance.save()
        messages.success(request, 'Attendance record updated successfully.')
        return redirect('attendance_history')

    return render(request, 'portal/attendance_edit.html', {
        'attendance': attendance,
        'service_types': service_types,
    })


@staff_member_required
def attendance_report(request):
    """Printable attendance report view."""
    filter_state = _build_attendance_queryset(
        request, include_deleted=request.GET.get('deleted') == '1')
    qs = filter_state['qs']
    today = date.today()
    total_records = qs.count()
    total_members = qs.values('member_id').distinct().count()
    today_records = qs.filter(service_date=today).count()
    latest_record = qs.first()

    return render(request, 'portal/attendance_report.html', {
        'records': qs,
        'service_types': filter_state['SERVICE_TYPES'],
        'service_type': filter_state['service_type'],
        'date': filter_state['date'],
        'from_date': filter_state['from_date'],
        'to_date': filter_state['to_date'],
        'member_q': filter_state['member_q'],
        'show_deleted': filter_state['include_deleted'],
        'total_records': total_records,
        'total_members': total_members,
        'today_records': today_records,
        'latest_record': latest_record,
    })


@login_required
def setup_sms_email(request):
    """SMS and Email setup page with full configuration support"""
    from messaging.models import SMSConfiguration, EmailConfiguration
    from messaging.services import MessageService

    # Get or create configurations
    sms_config, _ = SMSConfiguration.objects.get_or_create(
        defaults={
            'provider': 'manual',
            'is_active': True,
            'default_sender_name': 'Church'
        }
    )

    email_config, _ = EmailConfiguration.objects.get_or_create(
        defaults={
            'provider': 'gmail',
            'is_active': True,
            'from_name': 'Youth Church',
            'from_email': 'noreply@yourchurch.com'
        }
    )

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'save_sms':
            # Update SMS Configuration
            sms_config.provider = request.POST.get('provider', 'manual')
            sms_config.default_sender_name = request.POST.get(
                'sender_name', 'Church')

            # Twilio settings
            sms_config.twilio_account_sid = request.POST.get(
                'twilio_account_sid', '')
            sms_config.twilio_auth_token = request.POST.get(
                'twilio_auth_token', '')
            sms_config.twilio_phone_number = request.POST.get(
                'twilio_phone_number', '')
            sms_config.twilio_api_url = request.POST.get(
                'twilio_api_url', 'https://api.twilio.com/2010-04-01/Accounts')

            # Africa's Talking settings
            sms_config.africastalking_username = request.POST.get(
                'africastalking_username', '')
            sms_config.africastalking_api_key = request.POST.get(
                'africastalking_api_key', '')
            sms_config.africastalking_sender_id = request.POST.get(
                'africastalking_sender_id', '')
            sms_config.africastalking_api_url = request.POST.get(
                'africastalking_api_url', 'https://api.africastalking.com/version1')

            # Arkesel settings
            sms_config.arkesel_api_key = request.POST.get(
                'arkesel_api_key', '')
            sms_config.arkesel_sender_id = request.POST.get(
                'arkesel_sender_id', '')
            sms_config.arkesel_api_url = request.POST.get(
                'arkesel_api_url', 'https://sms.arkesel.com/sms/api')

            try:
                sms_config.is_active = True
                sms_config.full_clean()
                sms_config.save()
                messages.success(
                    request, 'SMS configuration saved successfully!')
            except ValidationError as exc:
                messages.error(
                    request, 'SMS configuration could not be saved: ' + '; '.join(exc.messages))
                return redirect('setup_sms_email')
            return redirect('setup_sms_email')

        elif action == 'save_email':
            # Update Email Configuration
            email_config.provider = request.POST.get('provider', 'gmail')
            email_config.smtp_host = request.POST.get(
                'smtp_host', 'smtp.gmail.com')
            email_config.smtp_port = request.POST.get('smtp_port', 587)
            email_config.smtp_username = request.POST.get('smtp_username', '')
            email_config.smtp_password = request.POST.get('smtp_password', '')
            email_config.from_email = request.POST.get('from_email', '')
            email_config.from_name = request.POST.get(
                'from_name', 'Youth Church')
            email_config.use_tls = 'use_tls' in request.POST
            email_config.use_ssl = 'use_ssl' in request.POST

            try:
                email_config.is_active = True
                email_config.full_clean()
                email_config.save()
                messages.success(
                    request, 'Email configuration saved successfully!')
            except ValidationError as exc:
                messages.error(
                    request, 'Email configuration could not be saved: ' + '; '.join(exc.messages))
                return redirect('setup_sms_email')
            return redirect('setup_sms_email')

        elif action == 'test_sms':
            # Send test SMS
            test_phone = request.POST.get('test_phone')
            if test_phone:
                result = MessageService.send_sms(
                    test_phone,
                    f"Test SMS from {sms_config.default_sender_name}. Your SMS provider is working!"
                )
                if result.get('success'):
                    messages.success(
                        request, f'Test SMS sent successfully to {test_phone}!')
                else:
                    messages.error(
                        request, f'Failed to send SMS: {result.get("error")}')
            else:
                messages.error(request, 'Please provide a phone number')
            return redirect('setup_sms_email')

        elif action == 'test_email':
            # Send test email
            test_email = request.POST.get('test_email')
            if test_email:
                result = MessageService.send_email(
                    test_email,
                    'Test Email from Church Management System',
                    'This is a test email. Your email configuration is working correctly!',
                    '<p>This is a test email. Your email configuration is working correctly!</p>'
                )
                if result.get('success'):
                    messages.success(
                        request, f'Test email sent successfully to {test_email}!')
                else:
                    messages.error(
                        request, f'Failed to send email: {result.get("error")}')
            else:
                messages.error(request, 'Please provide an email address')
            return redirect('setup_sms_email')

    context = {
        'sms_config': sms_config,
        'email_config': email_config,
        'title': 'SMS & Email Setup'
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
