from django.contrib import admin
from django.contrib.auth.models import Group
from import_export.admin import ImportExportModelAdmin
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from .models import Member, Family, Attendance
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.templatetags.static import static

class MemberResource(resources.ModelResource):
    class Meta:
        model = Member
        import_id_fields = ('phone_number', 'email')
        exclude = ('id', 'created_at', 'updated_at', 'created_by')
        skip_unchanged = True
        report_skipped = True
        
    def before_import_row(self, row, **kwargs):
        # Add any preprocessing here
        pass

@admin.register(Member)
class MemberAdmin(ImportExportModelAdmin):
    resource_class = MemberResource
    
    list_display = ('full_name_display', 'phone_number', 'email', 'status', 'age', 'date_joined', 'photo_thumbnail')
    list_filter = ('status', 'gender', 'department', 'date_joined')
    search_fields = ('first_name', 'last_name', 'middle_name', 'phone_number', 'email', 'address')
    ordering = ('last_name', 'first_name')
    
    fieldsets = (
        ('Personal Information', {
            'fields': (
                ('first_name', 'middle_name', 'last_name'),
                ('date_of_birth', 'gender'),
                ('photo', 'photo_preview'),
            )
        }),
        ('Contact Information', {
            'fields': (
                'email',
                ('phone_number', 'alternate_phone'),
                ('address', 'city', 'state', 'postal_code'),
            )
        }),
        ('Church Information', {
            'fields': (
                ('date_joined', 'baptism_date'),
                'status',
                'department',
                'spiritual_gifts',
            )
        }),
        ('Emergency Contact', {
            'fields': (
                ('emergency_contact_name', 'emergency_contact_phone'),
                'emergency_contact_relationship',
            )
        }),
        ('Additional Information', {
            'fields': (
                'occupation',
                'school',
                'talents',
                'notes',
            ),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ('photo_preview', 'created_at', 'updated_at', 'created_by')
    
    def full_name_display(self, obj):
        return f"{obj.last_name}, {obj.first_name} {obj.middle_name or ''}".strip()
    full_name_display.short_description = 'Full Name'
    
    def photo_thumbnail(self, obj):
        if obj.photo:
            return format_html('<img src="{}" width="50" height="50" style="border-radius: 50%;" />', obj.photo.url)
        # Show initials in a styled circle if no photo
        return format_html(
            '<div style="width: 50px; height: 50px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 50%; color: white; display: flex; align-items: center; justify-content: center; font-weight: bold;">{}</div>',
            obj.member_initials
        )
    photo_thumbnail.short_description = 'Photo'
    
    def photo_preview(self, obj):
        if obj.photo:
            return format_html('<img src="{}" width="150" height="150" style="border-radius: 10px;" />', obj.photo.url)
        # Show initials in a styled circle for preview
        return format_html(
            '<div style="width: 150px; height: 150px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; color: white; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 2.5rem;">{}</div>',
            obj.member_initials
        )
    photo_preview.short_description = 'Photo Preview'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(created_by=request.user)
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def view_on_site(self, obj):
        return reverse('member_detail', kwargs={'pk': obj.pk})

@admin.register(Family)
class FamilyAdmin(admin.ModelAdmin):
    list_display = ('member', 'relationship', 'relative', 'is_primary')
    list_filter = ('relationship', 'is_primary')
    search_fields = ('member__first_name', 'member__last_name', 'relative__first_name', 'relative__last_name')
    autocomplete_fields = ['member', 'relative']

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('member', 'service_date', 'service_type', 'attended', 'check_in_time')
    list_filter = ('service_type', 'attended', 'service_date')
    search_fields = ('member__first_name', 'member__last_name')
    date_hierarchy = 'service_date'
    autocomplete_fields = ['member']