import re
import requests
from django.conf import settings
from django.template.loader import render_to_string
try:
    from twilio.rest import Client
    _HAS_TWILIO = True
except Exception:
    Client = None
    _HAS_TWILIO = False

try:
    import africastalking
    _HAS_AFRICASTALKING = True
except Exception:
    africastalking = None
    _HAS_AFRICASTALKING = False

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class SMSService:
    def __init__(self):
        # Initialize SMS services
        self.twilio_client = None
        if _HAS_TWILIO and getattr(settings, 'TWILIO_ACCOUNT_SID', None):
            try:
                self.twilio_client = Client(
                    settings.TWILIO_ACCOUNT_SID,
                    settings.TWILIO_AUTH_TOKEN
                )
            except Exception:
                self.twilio_client = None

        self.africastalking_client = None
        if _HAS_AFRICASTALKING and getattr(settings, 'AFRICASTALKING_USERNAME', None):
            try:
                africastalking.initialize(
                    settings.AFRICASTALKING_USERNAME,
                    settings.AFRICASTALKING_API_KEY
                )
                self.africastalking_client = africastalking.SMS
            except Exception:
                self.africastalking_client = None

    def send_sms(self, phone_number, message, provider='twilio'):
        """
        Send SMS using configured provider
        """
        try:
            if provider == 'twilio' and self.twilio_client:
                message = self.twilio_client.messages.create(
                    body=message,
                    from_=settings.TWILIO_PHONE_NUMBER,
                    to=phone_number
                )
                return {'success': True, 'message_id': message.sid}

            elif provider == 'africastalking' and self.africastalking_client:
                response = self.africastalking_client.send(
                    message,
                    [phone_number]
                )
                return {'success': True, 'message_id': response['SMSMessageData']['Message']['id']}

            else:
                # Fallback to local logging
                print(f"SMS to {phone_number}: {message}")
                return {'success': True, 'message_id': 'local_log'}

        except Exception as e:
            return {'success': False, 'error': str(e)}


class EmailService:
    def send_email(self, to_email, subject, template_name, context):
        """
        Send templated email
        """
        try:
            html_message = render_to_string(
                f'emails/{template_name}.html', context)
            plain_message = render_to_string(
                f'emails/{template_name}.txt', context)

            result = MessageService.send_email(
                to_email,
                subject,
                plain_message,
                html_message,
            )
            return result.get('success', False)
        except Exception as e:
            print(f"Email error: {e}")
            return False


class BulkMessaging:
    def __init__(self):
        self.sms_service = SMSService()
        self.email_service = EmailService()

    def send_bulk_sms(self, members, message, provider='twilio'):
        """
        Send SMS to multiple members
        """
        results = []
        for member in members:
            if member.phone_number:
                result = self.sms_service.send_sms(
                    str(member.phone_number),
                    message,
                    provider
                )
                results.append({
                    'member': member,
                    'success': result['success'],
                    'message_id': result.get('message_id'),
                    'error': result.get('error')
                })
        return results

    def send_bulk_email(self, members, subject, template_name, context_vars=None):
        """
        Send email to multiple members
        """
        results = []
        for member in members:
            if member.email:
                context = context_vars.copy() if context_vars else {}
                context['member'] = member

                success = self.email_service.send_email(
                    member.email,
                    subject,
                    template_name,
                    context
                )
                results.append({
                    'member': member,
                    'success': success
                })
        return results


class MessageService:
    @staticmethod
    def send_sms(phone_number, message):
        """Send SMS using configured provider"""
        from .models import SMSConfiguration

        try:
            config = SMSConfiguration.objects.filter(is_active=True).first()
        except Exception as db_error:
            # If database isn't ready (cold start), gracefully fail with diagnostic info
            return {'success': False, 'error': f'Database connection issue: {str(db_error)[:100]}'}

        if not config:
            return {'success': False, 'error': 'No SMS configuration found'}

        try:
            if config.provider == 'twilio' and config.twilio_account_sid:
                # Twilio implementation
                from twilio.rest import Client
                client = Client(config.twilio_account_sid,
                                config.twilio_auth_token)

                twilio_message = client.messages.create(
                    body=message,
                    from_=config.twilio_phone_number,
                    to=phone_number
                )
                return {'success': True, 'message_id': twilio_message.sid}

            elif config.provider == 'africastalking' and config.africastalking_username:
                # Africa's Talking implementation
                import africastalking
                africastalking.initialize(
                    config.africastalking_username,
                    config.africastalking_api_key
                )
                sms = africastalking.SMS

                response = sms.send(
                    message,
                    [phone_number],
                    config.africastalking_sender_id or config.default_sender_name
                )
                return {'success': True, 'message_id': response['SMSMessageData']['Message']['id']}

            elif config.provider == 'arkesel' and config.arkesel_api_key:
                # Arkesel has multiple API variants in the wild. We try compatible patterns safely.
                api_key = re.sub(r'\s+', '', config.arkesel_api_key or '')
                sender_id = (config.arkesel_sender_id or
                             config.default_sender_name or '').strip()
                api_url = (config.arkesel_api_url or
                           'https://sms.arkesel.com/sms/api').strip()

                # Build fallback attempts for known Arkesel auth/payload variants.
                attempts = []
                for key_name in ('api_key', 'apikey', 'api-key'):
                    attempts.append({
                        'label': f'v1_get_{key_name}',
                        'method': 'GET',
                        'url': api_url,
                        'params': {
                            'action': 'send-sms',
                            key_name: api_key,
                            'to': phone_number,
                            'from': sender_id,
                            'sms': message,
                        },
                    })
                    attempts.append({
                        'label': f'v1_post_{key_name}',
                        'method': 'POST',
                        'url': api_url,
                        'data': {
                            'action': 'send-sms',
                            key_name: api_key,
                            'to': phone_number,
                            'from': sender_id,
                            'sms': message,
                        },
                    })

                v2_url = api_url if '/api/v2/' in api_url else 'https://sms.arkesel.com/api/v2/sms/send'
                for header_key in ('api-key', 'api_key', 'apikey', 'API-KEY'):
                    attempts.append({
                        'label': f'v2_post_{header_key}',
                        'method': 'POST',
                        'url': v2_url,
                        'headers': {
                            header_key: api_key,
                            'Authorization': f'Bearer {api_key}',
                            'Content-Type': 'application/json',
                        },
                        'json': {
                            'sender': sender_id,
                            'message': message,
                            'recipients': [phone_number],
                            'to': [phone_number],
                        },
                    })

                last_error = 'Unknown error from Arkesel'

                for attempt in attempts:
                    try:
                        response = requests.request(
                            attempt['method'],
                            attempt['url'],
                            params=attempt.get('params'),
                            data=attempt.get('data'),
                            json=attempt.get('json'),
                            headers=attempt.get('headers'),
                            timeout=30,
                        )

                        response_data = None
                        try:
                            response_data = response.json()
                        except ValueError:
                            response_data = None

                        # Success patterns for Arkesel v1/v2 and common compatible responses.
                        if response.ok:
                            if isinstance(response_data, dict):
                                code = str(response_data.get('code', '')).lower()
                                status = str(response_data.get('status', '')).lower()
                                message_text = str(
                                    response_data.get('message', '')).lower()
                                if (
                                    code in {'ok', 'success'}
                                    or status in {'ok', 'success', 'true'}
                                    or 'success' in message_text
                                ):
                                    message_id = (
                                        response_data.get('message_id')
                                        or response_data.get('id')
                                        or (response_data.get('data') or {}).get('id')
                                        or f"arkesel_{attempt['label']}"
                                    )
                                    return {'success': True, 'message_id': str(message_id)}
                            else:
                                response_text = (response.text or '').lower()
                                if 'success' in response_text:
                                    return {'success': True, 'message_id': f"arkesel_{attempt['label']}"}

                            # If request is HTTP-successful but format is unknown, treat as sent.
                            return {'success': True, 'message_id': f"arkesel_{attempt['label']}"}

                        if isinstance(response_data, dict):
                            last_error = response_data.get(
                                'message', f"HTTP {response.status_code}")
                        else:
                            last_error = f"HTTP {response.status_code}: {(response.text or '').strip()[:140]}"

                    except requests.exceptions.RequestException as exc:
                        last_error = str(exc)

                return {'success': False, 'error': last_error}

            else:
                # Manual/Log only
                print(f"[SMS LOG] To: {phone_number}, Message: {message}")
                return {'success': True, 'message_id': 'logged', 'note': 'SMS logged but not sent (manual mode)'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    @staticmethod
    def send_email(to_email, subject, message, html_message=None):
        """Send email using configured SMTP"""
        from .models import EmailConfiguration

        config = EmailConfiguration.objects.filter(is_active=True).first()

        if not config:
            return {'success': False, 'error': 'No email configuration found'}

        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{config.from_name} <{config.from_email}>"
            msg['To'] = to_email

            # Attach plain text
            part1 = MIMEText(message, 'plain')
            msg.attach(part1)

            # Attach HTML if provided
            if html_message:
                part2 = MIMEText(html_message, 'html')
                msg.attach(part2)

            # Connect and send
            if config.use_ssl:
                server = smtplib.SMTP_SSL(config.smtp_host, config.smtp_port)
            else:
                server = smtplib.SMTP(config.smtp_host, config.smtp_port)
                if config.use_tls:
                    server.starttls()

            if config.smtp_username and config.smtp_password:
                server.login(config.smtp_username, config.smtp_password)

            server.send_message(msg)
            server.quit()

            return {'success': True}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    @staticmethod
    def send_bulk_sms(phone_numbers, message):
        """Send SMS to multiple numbers"""
        results = []
        for phone in phone_numbers:
            result = MessageService.send_sms(phone, message)
            results.append({
                'phone': phone,
                'success': result['success'],
                'error': result.get('error'),
                'message_id': result.get('message_id')
            })
        return results

    @staticmethod
    def send_bulk_emails(emails, subject, message, html_message=None):
        """Send email to multiple addresses"""
        results = []
        for email in emails:
            result = MessageService.send_email(
                email, subject, message, html_message)
            results.append({
                'email': email,
                'success': result['success'],
                'error': result.get('error')
            })
        return results
