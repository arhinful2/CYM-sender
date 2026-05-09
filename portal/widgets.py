from django.db.models import Count, Q
from datetime import date, timedelta
from members.models import Member
from messaging.models import Message
from events.models import Event

class DashboardWidgets:
    @staticmethod
    def get_member_stats():
        """
        Get member statistics for dashboard
        """
        total = Member.objects.count()
        active = Member.objects.filter(status='active').count()
        new_this_month = Member.objects.filter(
            date_joined__month=date.today().month,
            date_joined__year=date.today().year
        ).count()
        
        # Age distribution
        under_18 = Member.objects.filter(
            date_of_birth__gte=date.today() - timedelta(days=18*365)
        ).count()
        
        adults = Member.objects.filter(
            date_of_birth__lt=date.today() - timedelta(days=18*365),
            date_of_birth__gte=date.today() - timedelta(days=40*365)
        ).count()
        
        seniors = Member.objects.filter(
            date_of_birth__lt=date.today() - timedelta(days=40*365)
        ).count()
        
        return {
            'total': total,
            'active': active,
            'new_this_month': new_this_month,
            'age_distribution': {
                'youth': under_18,
                'adults': adults,
                'seniors': seniors
            }
        }
    
    @staticmethod
    def get_message_stats():
        """
        Get messaging statistics
        """
        total_messages = Message.objects.count()
        broadcast_messages = Message.objects.filter(is_broadcast=True).count()
        
        # Recent activity
        last_7_days = date.today() - timedelta(days=7)
        recent_messages = Message.objects.filter(
            created_at__gte=last_7_days
        ).count()
        
        # Response rate
        messages_with_responses = Message.objects.filter(
            responses__isnull=False
        ).distinct().count()
        
        response_rate = (messages_with_responses / total_messages * 100) if total_messages > 0 else 0
        
        return {
            'total_messages': total_messages,
            'broadcast_messages': broadcast_messages,
            'recent_messages': recent_messages,
            'response_rate': round(response_rate, 1)
        }
    
    @staticmethod
    def get_upcoming_events():
        """
        Get upcoming events
        """
        today = date.today()
        next_week = today + timedelta(days=7)
        
        events = Event.objects.filter(
            start_date__date__gte=today,
            start_date__date__lte=next_week,
            is_cancelled=False
        ).order_by('start_date')[:5]
        
        return events
    
    @staticmethod
    def get_birthday_reminders():
        """
        Get upcoming birthdays
        """
        today = date.today()
        next_month = today + timedelta(days=30)
        
        birthdays = []
        
        # Get all members
        members = Member.objects.all()
        
        for member in members:
            days_until = member.days_until_birthday
            age = member.age  # age is now a property, not a method
            if age is not None and 0 <= days_until <= 30:
                birthdays.append({
                    'member': member,
                    'days_until': days_until,
                    'age': age + 1 if days_until == 0 else age
                })
        
        # Sort by days until birthday
        birthdays.sort(key=lambda x: x['days_until'])
        
        return birthdays[:5]
    
    @staticmethod
    def get_recent_activity():
        """
        Get recent system activity
        """
        from messaging.models import MessageResponse
        from members.models import Attendance
        
        last_week = date.today() - timedelta(days=7)
        
        activities = []
        
        # New members
        new_members = Member.objects.filter(
            created_at__date__gte=last_week
        ).count()
        if new_members:
            activities.append(f"{new_members} new member(s) joined")
        
        # Message responses
        responses = MessageResponse.objects.filter(
            created_at__date__gte=last_week
        ).count()
        if responses:
            activities.append(f"{responses} message response(s) received")
        
        # Attendance
        attendance_count = Attendance.objects.filter(
            service_date__gte=last_week
        ).count()
        if attendance_count:
            activities.append(f"{attendance_count} attendance record(s) added")
        
        return activities