"""
Management command to create sample message templates for quick reference.
Usage: python manage.py create_sample_templates
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from messaging.models import MessageTemplate


class Command(BaseCommand):
    help = 'Create sample message templates for common church youth communications'

    def handle(self, *args, **options):
        # Get or create a default admin user for templates
        admin_user = User.objects.filter(is_staff=True).first() or User.objects.first()

        templates_data = [
            # Broadcast Templates
            {
                'name': 'Service Reminder - Sunday',
                'template_type': 'broadcast',
                'subject': 'Don\'t forget: Service this Sunday!',
                'content': 'Hi {name},\n\nJust a friendly reminder that we have service this Sunday at 9:00 AM.\n\nWe look forward to seeing you there!\n\nBlessings,\nYouth Ministry',
                'category': 'Reminder',
                'description': 'Weekly Sunday service reminder for all members',
            },
            {
                'name': 'Youth Meeting Announcement',
                'template_type': 'broadcast',
                'subject': 'Youth Meeting - {date}',
                'content': 'Hello everyone,\n\nWe\'re excited to announce our upcoming youth meeting!\n\nDate: {date}\nTime: 6:00 PM\nLocation: Church Youth Center\n\nTopics: Fellowship, Games, and Refreshments\n\nSee you there!\n\nIn Christ,\nYouth Team',
                'category': 'Event',
                'description': 'Announcement for upcoming youth meetings and gatherings',
            },
            {
                'name': 'Attendance Check-in',
                'template_type': 'broadcast',
                'subject': 'We missed you at today\'s service',
                'content': 'Hi {name},\n\nWe noticed you weren\'t at today\'s service. We missed having you with us!\n\nWe\'d love to see you at our next gathering. If there\'s anything preventing you from attending, please reach out to us.\n\nGod bless,\nYouth Ministry',
                'category': 'Reminder',
                'description': 'Follow-up message for members who miss services',
            },
            {
                'name': 'Event Cancellation Notice',
                'template_type': 'broadcast',
                'subject': 'Event Update: {event_name} Rescheduled',
                'content': 'Dear Members,\n\nDue to unforeseen circumstances, {event_name} has been rescheduled.\n\nNew Date: {new_date}\nNew Time: {new_time}\n\nWe apologize for any inconvenience. Thank you for your understanding.\n\nBlessings,\nYouth Leadership',
                'category': 'Announcement',
                'description': 'Notification of event cancellations or rescheduling',
            },
            {
                'name': 'Volunteer Request',
                'template_type': 'broadcast',
                'subject': 'We need your help!',
                'content': 'Hello {name},\n\nWe\'re looking for volunteers to help with our upcoming youth event. Your help would make a huge difference!\n\nWhat we need: {volunteer_role}\nWhen: {date} at {time}\nDuration: {duration}\n\nIf you\'re interested, please reply to this message or contact us directly.\n\nThank you for your service!\n\nIn His service,\nYouth Team',
                'category': 'Request',
                'description': 'Call for volunteers for events and activities',
            },
            {
                'name': 'Birthday Greeting',
                'template_type': 'individual',
                'subject': 'Happy Birthday {name}!',
                'content': 'Happy Birthday {name}!\n\nWe hope you have a wonderful day filled with blessings and joy.\n\nMay God continue to guide and bless you in the year ahead.\n\nCelebrating with you,\nYouth Ministry Family',
                'category': 'Greeting',
                'description': 'Birthday greetings for individual members',
            },
            {
                'name': 'Prayer Request Acknowledgment',
                'template_type': 'individual',
                'subject': 'Your prayer request has been shared',
                'content': 'Hi {name},\n\nThank you for sharing your prayer request with us. We want you to know that we are praying for you.\n\nYour request has been shared with our prayer team, and we will continue to lift you up in prayer.\n\nIn prayer and faith,\nYouth Prayer Team',
                'category': 'Support',
                'description': 'Acknowledgment of prayer requests from members',
            },
            {
                'name': 'SMS - Quick Event Reminder',
                'template_type': 'sms',
                'subject': '',
                'content': 'Hey {name}! Don\'t forget about our youth meeting tomorrow at 6 PM. See you there! 🙏',
                'category': 'Reminder',
                'description': 'Short SMS reminder for events (max 160 chars)',
            },
            {
                'name': 'SMS - Service Attendance Reminder',
                'template_type': 'sms',
                'subject': '',
                'content': 'Service is this Sunday at 9 AM. We\'d love to see you! See you there! 😊',
                'category': 'Reminder',
                'description': 'Quick SMS for Sunday service reminder',
            },
            {
                'name': 'Email - Weekly Newsletter',
                'template_type': 'email',
                'subject': 'Youth Ministry Weekly Update',
                'content': 'Hi {name},\n\nHere\'s what\'s happening in our youth ministry this week:\n\n📅 Upcoming Events:\n- Youth Meeting: Wednesday 6 PM\n- Service: Sunday 9 AM\n- Outreach: Saturday 10 AM\n\n🙏 Prayer Focus:\nLet\'s pray for unity and growth in our youth group.\n\n💡 Verse of the Week:\n"I can do all things through Christ who strengthens me." - Philippians 4:13\n\nBlessings,\nYouth Ministry Team',
                'category': 'Newsletter',
                'description': 'Weekly newsletter with updates and spiritual content',
            },
            {
                'name': 'Group Message - Activity Details',
                'template_type': 'group',
                'subject': 'Details: {activity_name}',
                'content': 'Hi everyone,\n\nExcited about {activity_name}? Here are the details:\n\n📍 Location: {location}\n🕐 Time: {time}\n👥 Contact: {contact_person}\n💰 Cost: {cost}\n\nPlease bring: {items_to_bring}\n\nIf you have questions, reach out!\n\nSee you soon!',
                'category': 'Event',
                'description': 'Detailed information about group activities',
            },
            {
                'name': 'Announcement - New Member Welcome',
                'template_type': 'broadcast',
                'subject': 'Welcome to our Youth Ministry!',
                'content': 'Welcome {name}!\n\nWe\'re thrilled to have you join our youth ministry family!\n\nHere\'s what you can expect:\n- Meaningful fellowship and worship\n- Fun activities and events\n- Biblical teaching and spiritual growth\n- A community that cares about you\n\nOur next gathering is {date} at {time}. We can\'t wait to meet you!\n\nIf you have any questions, don\'t hesitate to reach out.\n\nBlessed to have you with us,\nYouth Ministry Team',
                'category': 'Welcome',
                'description': 'Welcome message for new members',
            },
        ]

        created_count = 0
        skipped_count = 0

        for template_data in templates_data:
            # Check if template already exists
            if MessageTemplate.objects.filter(name=template_data['name']).exists():
                skipped_count += 1
                self.stdout.write(
                    self.style.WARNING(f"Skipped: {template_data['name']} (already exists)")
                )
                continue

            # Create template
            template = MessageTemplate.objects.create(
                name=template_data['name'],
                template_type=template_data['template_type'],
                subject=template_data['subject'],
                content=template_data['content'],
                category=template_data['category'],
                description=template_data['description'],
                created_by=admin_user,
                is_active=True,
            )
            created_count += 1
            self.stdout.write(
                self.style.SUCCESS(f"✓ Created: {template_data['name']}")
            )

        # Summary
        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.SUCCESS(f"Created: {created_count} templates"))
        self.stdout.write(self.style.WARNING(f"Skipped: {skipped_count} templates"))
        self.stdout.write("="*50)
        self.stdout.write(
            self.style.SUCCESS("\n✓ Sample templates are ready to use!")
        )
        self.stdout.write(
            self.style.WARNING(
                "\nYou can now:\n"
                "1. Go to Admin → Message Templates\n"
                "2. Select a template in Compose Message form\n"
                "3. Edit content as needed and send"
            )
        )
