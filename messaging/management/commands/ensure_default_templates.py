from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from messaging.models import MessageTemplate


class Command(BaseCommand):
    help = 'Ensure default message templates exist in the database (idempotent)'

    def handle(self, *args, **options):
        # Get or create system user
        user, created = User.objects.get_or_create(
            username='system',
            defaults={'email': 'system@church.local', 'is_staff': True}
        )
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Created system user'))

        templates_data = [
            {
                'name': 'Event Cancellation Notice',
                'template_type': 'broadcast',
                'subject': 'Event Cancellation - {event_name}',
                'content': 'Dear members,\n\nWe regret to inform you that {event_name} scheduled for {event_date} has been cancelled.\n\nWe apologize for any inconvenience this may cause. We will inform you of any rescheduled date.\n\nBest regards,\nChurch Youth Team',
                'category': 'events',
            },
            {
                'name': 'Youth Meeting Announcement',
                'template_type': 'broadcast',
                'subject': 'Youth Meeting This {day} - {location}',
                'content': 'Dear youths,\n\nYou are cordially invited to our youth meeting this {day} at {location}.\n\nTime: {time}\nLocation: {location}\nTopic: {topic}\n\nLooking forward to seeing you there!\n\nChurch Youth Team',
                'category': 'meetings',
            },
            {
                'name': 'Attendance Check-in',
                'template_type': 'broadcast',
                'subject': 'Please Confirm Your Attendance',
                'content': 'Hi {name},\n\nWe hope to see you at our upcoming event. Please confirm your attendance by clicking the link or replying to this message.\n\nEvent: {event_name}\nDate: {event_date}\nTime: {event_time}\n\nThank you!',
                'category': 'attendance',
            },
            {
                'name': 'Service Reminder - Sunday',
                'template_type': 'broadcast',
                'subject': 'Don\'t Forget: Sunday Service Tomorrow',
                'content': 'Dear member,\n\nThis is a gentle reminder about our Sunday service tomorrow.\n\nTime: {service_time}\nLocation: {service_location}\nTopic: {sermon_topic}\n\nWe look forward to your presence!\n\nBlessings,\nChurch Youth Team',
                'category': 'services',
            },
            {
                'name': 'Volunteer Request',
                'template_type': 'broadcast',
                'subject': 'Volunteer Opportunity - {activity_type}',
                'content': 'Dear {name},\n\nWe are looking for volunteers for our upcoming {activity_type}.\n\nDate: {event_date}\nTime: {event_time}\nLocation: {location}\nResponsibilities: {responsibilities}\n\nWould you like to volunteer? Please reply to confirm.\n\nThank you for your service!\nChurch Youth Team',
                'category': 'volunteering',
            },
            {
                'name': 'Announcement - New Member Welcome',
                'template_type': 'broadcast',
                'subject': 'Welcome to Our Youth Group!',
                'content': 'Dear {name},\n\nWelcome to our vibrant youth community! We are excited to have you join us.\n\nHere\'s what you need to know:\n- Regular meetings: {meeting_day} at {meeting_time}\n- Location: {location}\n- Contact: {contact_info}\n\nIf you have any questions, don\'t hesitate to reach out.\n\nWarm regards,\nChurch Youth Team',
                'category': 'welcome',
            },
            {
                'name': 'Email - Weekly Newsletter',
                'template_type': 'email',
                'subject': 'Weekly Youth Newsletter - {week_date}',
                'content': '<html><body><h2>Weekly Youth Newsletter</h2><p>Dear members,</p><p>Here\'s what happened this week and what\'s coming up:</p><h3>This Week\'s Highlights:</h3>{highlights}<h3>Upcoming Events:</h3>{upcoming_events}<p>Stay blessed!</p><p>Church Youth Team</p></body></html>',
                'category': 'newsletters',
            },
            {
                'name': 'Group Message - Activity Details',
                'template_type': 'group',
                'subject': 'Activity Details - {activity_name}',
                'content': 'Hi everyone,\n\nHere are the details for our upcoming activity:\n\nActivity: {activity_name}\nDate: {activity_date}\nTime: {activity_time}\nLocation: {location}\nWho to bring: {who_to_bring}\nWhat to bring: {what_to_bring}\nCost (if any): {cost}\n\nLooking forward to seeing you all!\n\nChurch Youth Team',
                'category': 'activities',
            },
            {
                'name': 'Birthday Greeting',
                'template_type': 'individual',
                'subject': 'Happy Birthday {name}! 🎉',
                'content': 'Dear {name},\n\nHappy Birthday! We celebrate you today and thank God for the wonderful person you are!\n\nMay your special day be filled with joy, love, and blessings.\n\nWishing you a blessed year ahead!\n\nWarmest wishes,\nChurch Youth Team',
                'category': 'greetings',
            },
            {
                'name': 'Prayer Request Acknowledgment',
                'template_type': 'individual',
                'subject': 'We\'re Praying For You',
                'content': 'Dear {name},\n\nThank you for sharing your prayer request with us. We want you to know that we are lifting you up in prayer.\n\nYour request: {prayer_request}\n\nRemember that God is with you and cares deeply for your situation. We encourage you to hold on to faith and hope.\n\nPlease keep us updated on how we can continue to support you.\n\nIn God\'s love,\nChurch Youth Team',
                'category': 'prayers',
            },
            {
                'name': 'SMS - Quick Event Reminder',
                'template_type': 'sms',
                'subject': 'Event Reminder',
                'content': 'Hi {name}, reminder: {event_name} is happening {event_date} at {event_time} at {location}. See you there!',
                'category': 'events',
            },
            {
                'name': 'SMS - Service Attendance Reminder',
                'template_type': 'sms',
                'subject': 'Service Reminder',
                'content': 'Hi {name}, don\'t miss our service this {service_day} at {service_time}. {service_location}. We look forward to seeing you!',
                'category': 'services',
            },
        ]

        created_count = 0
        for template_data in templates_data:
            template, created = MessageTemplate.objects.get_or_create(
                name=template_data['name'],
                defaults={
                    'template_type': template_data['template_type'],
                    'subject': template_data['subject'],
                    'content': template_data['content'],
                    'category': template_data['category'],
                    'created_by': user,
                    'is_active': True,
                }
            )
            if created:
                created_count += 1
                self.stdout.write(f'  ✓ Created: {template.name}')
            else:
                self.stdout.write(f'  - Exists: {template.name}')

        self.stdout.write(
            self.style.SUCCESS(f'\n✓ Template setup complete: {created_count} new templates created, {len(templates_data) - created_count} already exist')
        )
