import requests
<<<<<<< HEAD
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

=======
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from twilio.rest import Client
import africastalking
>>>>>>> 3fbaf2d992c87deb75b608a23df462882d9c6986
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


<<<<<<< HEAD
=======

>>>>>>> 3fbaf2d992c87deb75b608a23df462882d9c6986
class SMSService:
    def __init__(self):
        # Initialize SMS services
        self.twilio_client = None
<<<<<<< HEAD
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

=======
        self.africastalking_client = None
        
        # Twilio Configuration
        if hasattr(settings, 'TWILIO_ACCOUNT_SID'):
            self.twilio_client = Client(
                settings.TWILIO_ACCOUNT_SID,
                settings.TWILIO_AUTH_TOKEN
            )
        
        # Africa's Talking Configuration
        if hasattr(settings, 'AFRICASTALKING_USERNAME'):
            africastalking.initialize(
                settings.AFRICASTALKING_USERNAME,
                settings.AFRICASTALKING_API_KEY
            )
            self.africastalking_client = africastalking.SMS
    
>>>>>>> 3fbaf2d992c87deb75b608a23df462882d9c6986
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
<<<<<<< HEAD

=======
            
>>>>>>> 3fbaf2d992c87deb75b608a23df462882d9c6986
            elif provider == 'africastalking' and self.africastalking_client:
                response = self.africastalking_client.send(
                    message,
                    [phone_number]
                )
                return {'success': True, 'message_id': response['SMSMessageData']['Message']['id']}
<<<<<<< HEAD

=======
            
>>>>>>> 3fbaf2d992c87deb75b608a23df462882d9c6986
            else:
                # Fallback to local logging
                print(f"SMS to {phone_number}: {message}")
                return {'success': True, 'message_id': 'local_log'}
<<<<<<< HEAD

        except Exception as e:
            return {'success': False, 'error': str(e)}


=======
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

>>>>>>> 3fbaf2d992c87deb75b608a23df462882d9c6986
class EmailService:
    def send_email(self, to_email, subject, template_name, context):
        """
        Send templated email
        """
        try:
<<<<<<< HEAD
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
=======
            html_message = render_to_string(f'emails/{template_name}.html', context)
            plain_message = render_to_string(f'emails/{template_name}.txt', context)
            
            send_mail(
                subject=subject,
                message=plain_message,
                html_message=html_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[to_email],
                fail_silently=False,
            )
            return True
>>>>>>> 3fbaf2d992c87deb75b608a23df462882d9c6986
        except Exception as e:
            print(f"Email error: {e}")
            return False

<<<<<<< HEAD

=======
>>>>>>> 3fbaf2d992c87deb75b608a23df462882d9c6986
class BulkMessaging:
    def __init__(self):
        self.sms_service = SMSService()
        self.email_service = EmailService()
<<<<<<< HEAD

=======
    
>>>>>>> 3fbaf2d992c87deb75b608a23df462882d9c6986
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
<<<<<<< HEAD

=======
    
>>>>>>> 3fbaf2d992c87deb75b608a23df462882d9c6986
    def send_bulk_email(self, members, subject, template_name, context_vars=None):
        """
        Send email to multiple members
        """
        results = []
        for member in members:
            if member.email:
                context = context_vars.copy() if context_vars else {}
                context['member'] = member
<<<<<<< HEAD

=======
                
>>>>>>> 3fbaf2d992c87deb75b608a23df462882d9c6986
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
<<<<<<< HEAD

=======
    
    
>>>>>>> 3fbaf2d992c87deb75b608a23df462882d9c6986

class MessageService:
    @staticmethod
    def send_sms(phone_number, message):
        """Send SMS using configured provider"""
        from .models import SMSConfiguration
<<<<<<< HEAD

        config = SMSConfiguration.objects.filter(is_active=True).first()

        if not config:
            return {'success': False, 'error': 'No SMS configuration found'}

=======
        
        config = SMSConfiguration.objects.filter(is_active=True).first()
        
        if not config:
            return {'success': False, 'error': 'No SMS configuration found'}
        
>>>>>>> 3fbaf2d992c87deb75b608a23df462882d9c6986
        try:
            if config.provider == 'twilio' and config.twilio_account_sid:
                # Twilio implementation
                from twilio.rest import Client
<<<<<<< HEAD
                client = Client(config.twilio_account_sid,
                                config.twilio_auth_token)

=======
                client = Client(config.twilio_account_sid, config.twilio_auth_token)
                
>>>>>>> 3fbaf2d992c87deb75b608a23df462882d9c6986
                twilio_message = client.messages.create(
                    body=message,
                    from_=config.twilio_phone_number,
                    to=phone_number
                )
                return {'success': True, 'message_id': twilio_message.sid}
<<<<<<< HEAD

=======
            
>>>>>>> 3fbaf2d992c87deb75b608a23df462882d9c6986
            elif config.provider == 'africastalking' and config.africastalking_username:
                # Africa's Talking implementation
                import africastalking
                africastalking.initialize(
                    config.africastalking_username,
                    config.africastalking_api_key
                )
                sms = africastalking.SMS
<<<<<<< HEAD

=======
                
>>>>>>> 3fbaf2d992c87deb75b608a23df462882d9c6986
                response = sms.send(
                    message,
                    [phone_number],
                    config.africastalking_sender_id or config.default_sender_name
                )
                return {'success': True, 'message_id': response['SMSMessageData']['Message']['id']}
<<<<<<< HEAD

            elif config.provider == 'arkesel' and config.arkesel_api_key:
                # Arkesel API implementation (configurable endpoint)
                api_url = config.arkesel_api_url or 'https://sms.arkesel.com/sms/api'
                params = {
                    'action': 'send-sms',
                    'api_key': config.arkesel_api_key.strip(),  # Remove any whitespace
                    'to': phone_number,
                    'from': config.arkesel_sender_id,
                    'sms': message
                }

                try:
                    response = requests.get(api_url, params=params, timeout=30)
                    response.raise_for_status()  # Raise error for non-200 status codes
                    response_data = response.json()

                    # Arkesel v1 returns: {"code":"ok","message":"Successfully Send","balance":"xxx","user":"xxx"}
                    if response_data.get('code') == 'ok':
                        return {'success': True, 'message_id': 'arkesel_' + str(response_data.get('balance', 'sent'))}
                    else:
                        error_msg = response_data.get(
                            'message', 'Unknown error from Arkesel')
                        return {'success': False, 'error': error_msg}
                except requests.exceptions.HTTPError as e:
                    # Handle HTTP errors (4xx, 5xx)
                    error_msg = f"HTTP {e.response.status_code}"
                    try:
                        error_msg += f": {response.json().get('message', response.text[:100])}"
                    except:
                        error_msg += f": {response.text[:100]}"
                    return {'success': False, 'error': error_msg}

=======
            
>>>>>>> 3fbaf2d992c87deb75b608a23df462882d9c6986
            else:
                # Manual/Log only
                print(f"[SMS LOG] To: {phone_number}, Message: {message}")
                return {'success': True, 'message_id': 'logged', 'note': 'SMS logged but not sent (manual mode)'}
<<<<<<< HEAD

        except Exception as e:
            return {'success': False, 'error': str(e)}

=======
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
>>>>>>> 3fbaf2d992c87deb75b608a23df462882d9c6986
    @staticmethod
    def send_email(to_email, subject, message, html_message=None):
        """Send email using configured SMTP"""
        from .models import EmailConfiguration
<<<<<<< HEAD

        config = EmailConfiguration.objects.filter(is_active=True).first()

        if not config:
            return {'success': False, 'error': 'No email configuration found'}

=======
        
        config = EmailConfiguration.objects.filter(is_active=True).first()
        
        if not config:
            return {'success': False, 'error': 'No email configuration found'}
        
>>>>>>> 3fbaf2d992c87deb75b608a23df462882d9c6986
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{config.from_name} <{config.from_email}>"
            msg['To'] = to_email
<<<<<<< HEAD

            # Attach plain text
            part1 = MIMEText(message, 'plain')
            msg.attach(part1)

=======
            
            # Attach plain text
            part1 = MIMEText(message, 'plain')
            msg.attach(part1)
            
>>>>>>> 3fbaf2d992c87deb75b608a23df462882d9c6986
            # Attach HTML if provided
            if html_message:
                part2 = MIMEText(html_message, 'html')
                msg.attach(part2)
<<<<<<< HEAD

=======
            
>>>>>>> 3fbaf2d992c87deb75b608a23df462882d9c6986
            # Connect and send
            if config.use_ssl:
                server = smtplib.SMTP_SSL(config.smtp_host, config.smtp_port)
            else:
                server = smtplib.SMTP(config.smtp_host, config.smtp_port)
                if config.use_tls:
                    server.starttls()
<<<<<<< HEAD

            if config.smtp_username and config.smtp_password:
                server.login(config.smtp_username, config.smtp_password)

            server.send_message(msg)
            server.quit()

            return {'success': True}

        except Exception as e:
            return {'success': False, 'error': str(e)}

=======
            
            if config.smtp_username and config.smtp_password:
                server.login(config.smtp_username, config.smtp_password)
            
            server.send_message(msg)
            server.quit()
            
            return {'success': True}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
>>>>>>> 3fbaf2d992c87deb75b608a23df462882d9c6986
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
<<<<<<< HEAD

=======
    
>>>>>>> 3fbaf2d992c87deb75b608a23df462882d9c6986
    @staticmethod
    def send_bulk_emails(emails, subject, message, html_message=None):
        """Send email to multiple addresses"""
        results = []
        for email in emails:
<<<<<<< HEAD
            result = MessageService.send_email(
                email, subject, message, html_message)
=======
            result = MessageService.send_email(email, subject, message, html_message)
>>>>>>> 3fbaf2d992c87deb75b608a23df462882d9c6986
            results.append({
                'email': email,
                'success': result['success'],
                'error': result.get('error')
            })
<<<<<<< HEAD
        return results
=======
        return results
>>>>>>> 3fbaf2d992c87deb75b608a23df462882d9c6986
