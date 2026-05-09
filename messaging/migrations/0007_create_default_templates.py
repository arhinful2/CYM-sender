from django.db import migrations


def create_default_templates(apps, schema_editor):
    """Create default message templates on first deploy to hosted environment."""
    MessageTemplate = apps.get_model('messaging', 'MessageTemplate')

    # Only create if they don't exist (idempotent)
    if MessageTemplate.objects.exists():
        return

    # Use the historical User model from the migration apps registry
    User = apps.get_model('auth', 'User')
    # Get or create default user for templates
    user, _ = User.objects.get_or_create(
        username='system',
        defaults={'email': 'system@church.local', 'is_staff': True}
    )

    templates_data = [
        {
            'name': 'Event Cancellation Notice',
            'template_type': 'broadcast',
            'subject': 'Event Cancellation - {event_name}',
            'content': 'Dear members,\n\nWe regret to inform you that {event_name} scheduled for {event_date} has been cancelled.\n\nWe apologize for any inconvenience this may cause. We will inform you of any rescheduled date.\n\nBest regards,\nChurch Youth Team',
            'category': 'events',
            'description': 'Notification when an event is cancelled',
        },
        {
            'name': 'Youth Meeting Announcement',
            'template_type': 'broadcast',
            'subject': 'Youth Meeting This {day} - {location}',
            'content': 'Dear youths,\n\nYou are cordially invited to our youth meeting this {day} at {location}.\n\nTime: {time}\nLocation: {location}\nTopic: {topic}\n\nLooking forward to seeing you there!\n\nChurch Youth Team',
            'category': 'meetings',
            'description': 'Announcement for scheduled youth meetings',
        },
        {
            'name': 'Attendance Check-in',
            'template_type': 'broadcast',
            'subject': 'Please Confirm Your Attendance',
            'content': 'Hi {name},\n\nWe hope to see you at our upcoming event. Please confirm your attendance by clicking the link or replying to this message.\n\nEvent: {event_name}\nDate: {event_date}\nTime: {event_time}\n\nThank you!',
            'category': 'attendance',
            'description': 'Request to confirm attendance for events',
        },
        {
            'name': 'Service Reminder - Sunday',
            'template_type': 'broadcast',
            'subject': 'Don\'t Forget: Sunday Service Tomorrow',
            'content': 'Dear member,\n\nThis is a gentle reminder about our Sunday service tomorrow.\n\nTime: {service_time}\nLocation: {service_location}\nTopic: {sermon_topic}\n\nWe look forward to your presence!\n\nBlessings,\nChurch Youth Team',
            'category': 'services',
            'description': 'Reminder for upcoming Sunday services',
        },
        {
            'name': 'Volunteer Request',
            'template_type': 'broadcast',
            'subject': 'Volunteer Opportunity - {activity_type}',
            'content': 'Dear {name},\n\nWe are looking for volunteers for our upcoming {activity_type}.\n\nDate: {event_date}\nTime: {event_time}\nLocation: {location}\nResponsibilities: {responsibilities}\n\nWould you like to volunteer? Please reply to confirm.\n\nThank you for your service!\nChurch Youth Team',
            'category': 'volunteering',
            'description': 'Request for volunteer participation',
        },
        {
            'name': 'Announcement - New Member Welcome',
            'template_type': 'broadcast',
            'subject': 'Welcome to Our Youth Group!',
            'content': 'Dear {name},\n\nWelcome to our vibrant youth community! We are excited to have you join us.\n\nHere\'s what you need to know:\n- Regular meetings: {meeting_day} at {meeting_time}\n- Location: {location}\n- Contact: {contact_info}\n\nIf you have any questions, don\'t hesitate to reach out.\n\nWarm regards,\nChurch Youth Team',
            'category': 'welcome',
            'description': 'Welcome message for new members',
        },
        {
            'name': 'Email - Weekly Newsletter',
            'template_type': 'email',
            'subject': 'Weekly Youth Newsletter - {week_date}',
            'content': '<html><body><h2>Weekly Youth Newsletter</h2><p>Dear members,</p><p>Here\'s what happened this week and what\'s coming up:</p><h3>This Week\'s Highlights:</h3>{highlights}<h3>Upcoming Events:</h3>{upcoming_events}<p>Stay blessed!</p><p>Church Youth Team</p></body></html>',
            'category': 'newsletters',
            'description': 'Weekly email newsletter for members',
        },
        {
            'name': 'Group Message - Activity Details',
            'template_type': 'group',
            'subject': 'Activity Details - {activity_name}',
            'content': 'Hi everyone,\n\nHere are the details for our upcoming activity:\n\nActivity: {activity_name}\nDate: {activity_date}\nTime: {activity_time}\nLocation: {location}\nWho to bring: {who_to_bring}\nWhat to bring: {what_to_bring}\nCost (if any): {cost}\n\nLooking forward to seeing you all!\n\nChurch Youth Team',
            'category': 'activities',
            'description': 'Share activity details with group members',
        },
        {
            'name': 'Birthday Greeting',
            'template_type': 'individual',
            'subject': 'Happy Birthday {name}! 🎉',
            'content': 'Dear {name},\n\nHappy Birthday! We celebrate you today and thank God for the wonderful person you are!\n\nMay your special day be filled with joy, love, and blessings. \n\nWishing you a blessed year ahead!\n\nWarmest wishes,\nChurch Youth Team',
            'category': 'greetings',
            'description': 'Birthday greeting for members',
        },
        {
            'name': 'Prayer Request Acknowledgment',
            'template_type': 'individual',
            'subject': 'We\'re Praying For You',
            'content': 'Dear {name},\n\nThank you for sharing your prayer request with us. We want you to know that we are lifting you up in prayer.\n\nYour request: {prayer_request}\n\nRemember that God is with you and cares deeply for your situation. We encourage you to hold on to faith and hope.\n\nPlease keep us updated on how we can continue to support you.\n\nIn God\'s love,\nChurch Youth Team',
            'category': 'prayers',
            'description': 'Acknowledgment of received prayer requests',
        },
        {
            'name': 'SMS - Quick Event Reminder',
            'template_type': 'sms',
            'subject': 'Event Reminder',
            'content': 'Hi {name}, reminder: {event_name} is happening {event_date} at {event_time} at {location}. See you there!',
            'category': 'events',
            'description': 'Quick SMS reminder for events',
        },
        {
            'name': 'SMS - Service Attendance Reminder',
            'template_type': 'sms',
            'subject': 'Service Reminder',
            'content': 'Hi {name}, don\'t miss our service this {service_day} at {service_time}. {service_location}. We look forward to seeing you!',
            'category': 'services',
            'description': 'SMS reminder for Sunday services',
        },
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

    # Create templates
    for template_data in templates_data:
        MessageTemplate.objects.get_or_create(
            name=template_data['name'],
            defaults={
                'template_type': template_data['template_type'],
                'subject': template_data['subject'],
                'content': template_data['content'],
                'category': template_data['category'],
                'description': template_data.get('description', ''),
                'created_by': user,
                'is_active': True,
            }
        )


def reverse_default_templates(apps, schema_editor):
    """Remove default templates if migration is reversed."""
    MessageTemplate = apps.get_model('messaging', 'MessageTemplate')
    # Only delete templates created by 'system' user
    try:
        user = apps.get_model('auth', 'User').objects.get(username='system')
        MessageTemplate.objects.filter(created_by=user).delete()
    except:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ('messaging', '0006_messagetemplate'),
    ]

    operations = [
        migrations.RunPython(create_default_templates,
                             reverse_default_templates),
    ]
