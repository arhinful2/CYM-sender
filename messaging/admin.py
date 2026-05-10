from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Message, MessageResponse, Conversation, SMSLog, MessageTemplate
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.utils import timezone

from .models import SMSConfiguration, EmailConfiguration
from django.urls import path
from django.shortcuts import render, redirect
import smtplib
from email.mime.text import MIMEText
from django.urls import reverse


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('subject', 'sender', 'message_type', 'created_at',
                    'is_sent', 'allow_member_replies', 'recipients_count', 'responses_count', 'deleted_badge')
    list_filter = ('message_type', 'is_sent', 'allow_member_replies', 'is_deleted', 'created_at', 'sender')
    search_fields = ('subject', 'content', 'sender__username')
    readonly_fields = ('created_at', 'sent_at', 'deleted_at', 'responses_count_display', 'reply_link_preview')
    filter_horizontal = ('recipients',)
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Message Details', {
            'fields': ('sender', 'subject', 'content', 'message_type')
        }),
        ('Reply Link', {
            'fields': ('allow_member_replies', 'reply_token', 'reply_link_preview'),
            'description': 'Enable this to append a secure reply link for members.'
        }),
        ('Recipients', {
            'fields': ('recipients',),
            'description': 'Select members for individual or group messages. Leave empty for broadcast.'
        }),
        ('Scheduling', {
            'fields': ('scheduled_for',),
            'classes': ('collapse',),
        }),
        ('Status', {
            'fields': ('is_sent', 'sent_at', 'sms_sent', 'whatsapp_sent', 'responses_count_display'),
        }),
        ('Soft Delete', {
            'fields': ('is_deleted', 'deleted_at'),
            'classes': ('collapse',),
        }),
    )

    def get_queryset(self, request):
        """By default, exclude soft-deleted messages"""
        qs = super().get_queryset(request)
        # Show deleted items only if filtered explicitly
        if 'is_deleted__exact' not in request.GET:
            qs = qs.filter(is_deleted=False)
        return qs

    def deleted_badge(self, obj):
        if obj.is_deleted:
            return format_html('<span style="background-color: #dc3545; color: white; padding: 3px 10px; border-radius: 3px;">Deleted</span>')
        return "-"
    deleted_badge.short_description = 'Status'

    def recipients_count(self, obj):
        if obj.is_broadcast:
            return "All Members"
        return obj.recipients.count()
    recipients_count.short_description = 'Recipients'

    def responses_count(self, obj):
        return obj.responses.count()
    responses_count.short_description = 'Responses'

    def responses_count_display(self, obj):
        count = obj.responses.count()
        url = reverse('admin:messaging_messageresponse_changelist') + \
            f'?message__id__exact={obj.id}'
        return format_html('<a href="{}">{} Responses</a>', url, count)
    responses_count_display.short_description = 'Total Responses'

    def reply_link_preview(self, obj):
        if not obj.pk:
            return 'Save the message to generate a reply link.'
        url = f'/portal/messaging/{obj.id}/reply/<member_id>/{obj.reply_token}/'
        return format_html('<code style="white-space: normal;">{}</code>', url)
    reply_link_preview.short_description = 'Reply Link Preview'

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.sender = request.user

        # If no recipients selected, it's a broadcast
        if not obj.recipients.exists():
            obj.is_broadcast = True
            obj.message_type = 'broadcast'

        super().save_model(request, obj, form, change)

        # Mark as sent if scheduled time is past or immediate
        if not obj.scheduled_for or obj.scheduled_for <= timezone.now():
            obj.is_sent = True
            obj.sent_at = timezone.now()
            obj.save()

            # Create conversations for recipients
            if obj.is_broadcast:
                from members.models import Member
                recipients = Member.objects.all()
            else:
                recipients = obj.recipients.all()

            for member in recipients:
                Conversation.objects.get_or_create(
                    message=obj,
                    member=member
                )

    def response_stats(self, obj):
        responses = MessageResponse.objects.filter(message=obj, is_deleted=False)
        return f"{responses.filter(is_acknowledgment=True).count()} acknowledgments, {responses.filter(is_reply=True).count()} replies"
    response_stats.short_description = 'Response Stats'


@admin.register(MessageResponse)
class MessageResponseAdmin(admin.ModelAdmin):
    list_display = ('message', 'respondent', 'respondent_phone', 'created_at',
                    'has_admin_reply', 'is_acknowledgment', 'is_reply', 'deleted_badge')
    list_filter = ('is_acknowledgment', 'is_reply', 'is_deleted', 'created_at', 'replied_at')
    search_fields = ('response_content', 'respondent__first_name',
                     'respondent__last_name', 'respondent_phone', 'message__subject')
    readonly_fields = ('created_at', 'replied_at', 'deleted_at', 'admin_reply_preview', 'respondent_phone')
    autocomplete_fields = ['message', 'respondent']

    fieldsets = (
        ('Response Details', {
            'fields': ('message', 'respondent', 'respondent_phone', 'response_content', 'is_acknowledgment', 'is_reply')
        }),
        ('Admin Reply', {
            'fields': ('admin_reply', 'admin_reply_preview', 'replied_at')
        }),
        ('Soft Delete', {
            'fields': ('is_deleted', 'deleted_at'),
            'classes': ('collapse',),
        }),
    )

    def get_queryset(self, request):
        """By default, exclude soft-deleted responses"""
        qs = super().get_queryset(request)
        # Show deleted items only if filtered explicitly
        if 'is_deleted__exact' not in request.GET:
            qs = qs.filter(is_deleted=False)
        return qs

    def deleted_badge(self, obj):
        if obj.is_deleted:
            return format_html('<span style="background-color: #dc3545; color: white; padding: 3px 10px; border-radius: 3px;">Deleted</span>')
        return "-"
    deleted_badge.short_description = 'Status'

    def has_admin_reply(self, obj):
        return bool(obj.admin_reply)
    has_admin_reply.boolean = True
    has_admin_reply.short_description = 'Replied'

    def admin_reply_preview(self, obj):
        if obj.admin_reply:
            return format_html('<div style="background-color: #f0f0f0; padding: 10px; border-radius: 5px;">{}</div>', obj.admin_reply)
        return "No reply yet"
    admin_reply_preview.short_description = 'Reply Preview'

    def save_model(self, request, obj, form, change):
        # Keep the responder phone in sync for auditing and reporting.
        if obj.respondent and not obj.respondent_phone:
            obj.respondent_phone = str(obj.respondent.phone_number or '')

        # If admin reply is added/updated, update replied_at
        if 'admin_reply' in form.changed_data and obj.admin_reply:
            obj.replied_at = timezone.now()

        # Update conversation status
        conversation = Conversation.objects.filter(
            message=obj.message, member=obj.respondent).first()
        if conversation:
            conversation.responded = True
            conversation.save()

        super().save_model(request, obj, form, change)


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('message', 'member', 'is_read',
                    'responded', 'last_updated')
    list_filter = ('is_read', 'responded', 'last_updated')
    search_fields = ('member__first_name',
                     'member__last_name', 'message__subject')
    readonly_fields = ('last_updated',)
    autocomplete_fields = ['message', 'member']


@admin.register(SMSLog)
class SMSLogAdmin(admin.ModelAdmin):
    list_display = ('member', 'phone_number', 'status',
                    'is_incoming', 'created_at', 'content_preview', 'deleted_badge')
    list_filter = ('status', 'is_incoming', 'is_deleted', 'created_at')
    search_fields = ('member__first_name', 'member__last_name',
                     'phone_number', 'content')
    readonly_fields = ('created_at', 'sent_at', 'delivered_at', 'deleted_at')

    def get_queryset(self, request):
        """By default, exclude soft-deleted logs"""
        qs = super().get_queryset(request)
        # Show deleted items only if filtered explicitly
        if 'is_deleted__exact' not in request.GET:
            qs = qs.filter(is_deleted=False)
        return qs

    def deleted_badge(self, obj):
        if obj.is_deleted:
            return format_html('<span style="background-color: #dc3545; color: white; padding: 3px 10px; border-radius: 3px;">Deleted</span>')
        return "-"
    deleted_badge.short_description = 'Status'

    def content_preview(self, obj):
        if len(obj.content) > 50:
            return f"{obj.content[:50]}..."
        return obj.content
    content_preview.short_description = 'Content'


@admin.register(SMSConfiguration)
class SMSConfigurationAdmin(admin.ModelAdmin):
    list_display = ('provider', 'is_active', 'created_at')
    list_editable = ('is_active',)

    fieldsets = (
        ('Provider Selection', {
            'fields': ('provider', 'is_active', 'default_sender_name', 'cost_per_sms')
        }),
        ('Twilio Settings (if using Twilio)', {
            'fields': ('twilio_account_sid', 'twilio_auth_token', 'twilio_phone_number', 'twilio_api_url'),
            'classes': ('collapse',),
        }),
        ('Africa\'s Talking Settings (if using Africa\'s Talking)', {
            'fields': ('africastalking_username', 'africastalking_api_key', 'africastalking_sender_id', 'africastalking_api_url'),
            'classes': ('collapse',),
        }),
        ('Arkesel Settings (if using Arkesel)', {
            'fields': ('arkesel_api_key', 'arkesel_sender_id', 'arkesel_api_url'),
            'classes': ('collapse',),
            'description': 'Arkesel API URL: Default is v1 (sms/api). Change to api/v2/sms/send for v2 if needed.'
        }),
    )

    def has_add_permission(self, request):
        """Only allow one configuration"""
        return SMSConfiguration.objects.count() == 0

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of configuration"""
        return False


@admin.register(EmailConfiguration)
class EmailConfigurationAdmin(admin.ModelAdmin):
    list_display = ('provider', 'from_email', 'is_active', 'test_button')
    list_editable = ('is_active',)
    readonly_fields = ('test_button',)

    fieldsets = (
        ('Provider Selection', {
            'fields': ('provider', 'is_active', 'from_email', 'from_name', 'test_email')
        }),
        ('SMTP Settings', {
            'fields': ('smtp_host', 'smtp_port', 'smtp_username', 'smtp_password')
        }),
        ('Security', {
            'fields': ('use_tls', 'use_ssl')
        }),
        ('Test Configuration', {
            'fields': ('test_button',),
            'classes': ('collapse',),
        }),
    )

    def test_button(self, obj):
        return format_html(
            '<a class="button" href="test-email/">Test Email Configuration</a>'
        )
    test_button.short_description = 'Test'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('test-email/', self.admin_site.admin_view(self.test_email_view),
                 name='test_email'),
        ]
        return custom_urls + urls

    def test_email_view(self, request):
        """Test email configuration"""
        config = EmailConfiguration.objects.first()

        if request.method == 'POST':
            try:
                # Test sending email
                msg = MIMEText(
                    'This is a test email from your Church Management System.')
                msg['Subject'] = 'Test Email from Church System'
                msg['From'] = f"{config.from_name} <{config.from_email}>"
                msg['To'] = config.test_email

                if config.use_ssl:
                    server = smtplib.SMTP_SSL(
                        config.smtp_host, config.smtp_port)
                else:
                    server = smtplib.SMTP(config.smtp_host, config.smtp_port)
                    if config.use_tls:
                        server.starttls()

                if config.smtp_username and config.smtp_password:
                    server.login(config.smtp_username, config.smtp_password)

                server.send_message(msg)
                server.quit()

                messages.success(
                    request, f'Test email sent successfully to {config.test_email}!')
            except Exception as e:
                messages.error(request, f'Failed to send test email: {str(e)}')

            return redirect('admin:messaging_emailconfiguration_changelist')

        context = {
            'config': config,
            'title': 'Test Email Configuration',
        }
        return render(request, 'admin/test_email.html', context)

    def has_add_permission(self, request):
        """Only allow one configuration"""
        return EmailConfiguration.objects.count() == 0

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of configuration"""
        return False


@admin.register(MessageTemplate)
class MessageTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'template_type', 'category', 'is_active', 'created_by', 'updated_at', 'view_button')
    list_filter = ('template_type', 'category', 'is_active', 'created_at')
    search_fields = ('name', 'subject', 'content', 'description')
    readonly_fields = ('created_by', 'created_at', 'updated_at', 'preview_content')
    
    fieldsets = (
        ('Template Information', {
            'fields': ('name', 'template_type', 'category', 'is_active')
        }),
        ('Content', {
            'fields': ('subject', 'content', 'preview_content'),
            'classes': ('wide',),
            'description': 'Use placeholders like {name}, {member_name}, {date} in your content'
        }),
        ('Description & Notes', {
            'fields': ('description',),
            'classes': ('collapse',),
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def preview_content(self, obj):
        """Show a preview of the template content"""
        if obj.content:
            preview = obj.content[:200] + '...' if len(obj.content) > 200 else obj.content
            return format_html('<pre style="white-space: pre-wrap; word-wrap: break-word;">{}</pre>', preview)
        return '(Empty)'
    preview_content.short_description = 'Content Preview'

    def view_button(self, obj):
        """Button to view full template"""
        return format_html(
            '<a class="button" href="#" onclick="alert(\'{}\'); return false;">View</a>',
            obj.content.replace("'", "\\'").replace("\n", "\\n")
        )
    view_button.short_description = 'Action'

    def save_model(self, request, obj, form, change):
        """Set the created_by field to the current user"""
        if not change:  # Only on creation
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    class Media:
        css = {
            'all': ('admin/css/template_admin.css',)
        }

