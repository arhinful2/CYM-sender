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
            {
                'name': 'Follow-up - Missed Event',
                'template_type': 'individual',
                'subject': 'We missed you at {event_name}',
                'content': 'Hi {name},\n\nWe noticed you couldn\'t make it to {event_name}. We missed having you there!\n\nIf there\'s anything we can do to support you or if you have any questions about upcoming events, please let us know.\n\nWe hope to see you at the next gathering!\n\nIn Christ,\nYouth Ministry',
                'category': 'Follow-up',
                'description': 'Follow-up message for members who miss events',     
            },
            {
                'name': 'Encouragement - Midweek Check-in',
                'template_type': 'individual',
                'subject': 'Just checking in, {name}',
                'content': 'Hi {name},\n\nJust wanted to check in and see how you\'re doing this week. Remember, you\'re not alone, and we\'re here for you!\n\nIf you need anything or just want to talk, feel free to reach out.\n\nKeep shining your light!\n\nBlessings,\nYouth Ministry Team',
                'category': 'Encouragement',
                'description': 'Midweek check-in message to encourage members',
            },
            {
                'name': 'Event Reminder - Outreach',
                'template_type': 'broadcast',
                'subject': 'Join us for Outreach this Saturday!',
                'content': 'Hi everyone,\n\nWe\'re excited about our upcoming outreach event this Saturday at 10 AM! It\'s a great opportunity to serve our community and share God\'s love.\n\n📍 Location: {location}\n🕐 Time: 10 AM - 1 PM\n👥 Contact: {contact_person}\n💰 Cost: Free\n\nPlease bring: {items_to_bring}\n\nLet\'s make a difference together! See you there!\n\nIn His service,\nYouth Ministry Team',
                'category': 'Event',
                'description': 'Reminder for upcoming outreach events',
            },
            {
                'name': 'Thank You - Volunteer Appreciation',
                'template_type': 'broadcast',
                'subject': 'Thank you for volunteering!',
                'content': 'Dear {name},\n\nWe want to extend a heartfelt thank you for volunteering your time and talents to our youth ministry. Your dedication and service make a huge impact on our community!\n\nWe appreciate all that you do to support our events, activities, and the spiritual growth of our youth.\n\nThank you for being a blessing to us all!\n\nIn gratitude,\nYouth Ministry Team',
                'category': 'Appreciation',
                'description': 'Message to thank volunteers for their service',
            },
            {
                'name': 'Thank You - Member Appreciation',
                'template_type': 'broadcast',
                'subject': 'Thank you for being part of our community!',
                'content': 'Dear {name},\n\nWe want to take a moment to thank you for being a valued member of our youth ministry community. Your presence, participation, and faith enrich our group in so many ways!\n\nWe\'re grateful for the unique gifts and perspectives you bring to our fellowship. Thank you for being part of our journey together in faith.\n\nBlessings,\nYouth Ministry Team',
                'category': 'Appreciation',
                'description': 'Message to thank members for being part of the community',
            },
            {   'name': 'Thank You - Attendance Appreciation',
                'template_type': 'broadcast',
                'subject': 'Thank you for coming to church today',
                'content': 'Dear {name},\n\nThank you for joining us at church today! We hope you had a meaningful and uplifting experience. Your presence is a blessing to our community, and we\'re grateful to have you with us.\n\nIf you have any questions about our youth ministry or want to get involved, please don\'t hesitate to reach out. We\'d love to connect with you!\n\nBlessings,\nYouth Ministry Team',
                'category': 'Appreciation',
                'description': 'Message to thank members for attending church',
            },
            {   'name': 'Church cleaning',
                'template_type': 'broadcast',
                'subject': 'Church Cleaning Reminder',
                'content': 'Dear {name},\n\nJust a friendly reminder that we have a church cleaning session this Saturday at 9 AM. We\'ll be meeting in the fellowship hall to get everything ready for the upcoming services.\n\nPlease bring your own cleaning supplies if you have them, and don\'t forget to wear comfortable clothes!\n\nLooking forward to seeing you there!\n\nBlessings,\nYouth Ministry Team',
                'category': 'Event',
                'description': 'Reminder for church cleaning sessions',
            },
            {
                'name': 'Dues Reminder',
                'template_type': 'individual',
                'subject': 'Dues Reminder',
                'content': 'Dear {name},\n\nThis is a friendly reminder that your dues for this month are due. Please make sure to submit your payment by the end of the week to stay active in our youth ministry activities.\n\nIf you have any questions about the payment process or need assistance, please don\'t hesitate to reach out to us via church website:https://youth-website-delta.vercel.app/ or 0545037986\n\nThank you for your support!\n\nBlessings,\nYouth Ministry Team',
                'category': 'Reminder',
                'description': 'Dues reminder for members',
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
