import os
import zipfile
import json
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core import serializers
from members.models import Member, Attendance
from messaging.models import Message, MessageResponse

class Command(BaseCommand):
    help = 'Create backup of all system data'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--backup-dir',
            type=str,
            help='Directory to save backup files',
            default='backups'
        )
    
    def handle(self, *args, **options):
        backup_dir = options['backup_dir']
        
        # Create backup directory if it doesn't exist
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(backup_dir, f'backup_{timestamp}.zip')
        
        self.stdout.write(f'Creating backup: {backup_file}')
        
        with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Backup members
            members_data = serializers.serialize('json', Member.objects.all())
            zipf.writestr('members.json', members_data)
            
            # Backup messages
            messages_data = serializers.serialize('json', Message.objects.all())
            zipf.writestr('messages.json', messages_data)
            
            # Backup message responses
            responses_data = serializers.serialize('json', MessageResponse.objects.all())
            zipf.writestr('message_responses.json', responses_data)
            
            # Backup attendance
            attendance_data = serializers.serialize('json', Attendance.objects.all())
            zipf.writestr('attendance.json', attendance_data)
            
            # Backup media files
            media_dir = settings.MEDIA_ROOT
            for root, dirs, files in os.walk(media_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, settings.BASE_DIR)
                    zipf.write(file_path, arcname)
            
            # Create backup info
            backup_info = {
                'timestamp': timestamp,
                'total_members': Member.objects.count(),
                'total_messages': Message.objects.count(),
                'total_responses': MessageResponse.objects.count(),
                'total_attendance': Attendance.objects.count(),
                'database': settings.DATABASES['default']['NAME']
            }
            
            zipf.writestr('backup_info.json', json.dumps(backup_info, indent=2))
        
        self.stdout.write(self.style.SUCCESS(f'Backup created successfully: {backup_file}'))
        
        # Cleanup old backups (keep last 30 days)
        self.cleanup_old_backups(backup_dir)
    
    def cleanup_old_backups(self, backup_dir, days_to_keep=30):
        import time
        cutoff = time.time() - (days_to_keep * 86400)
        
        for filename in os.listdir(backup_dir):
            filepath = os.path.join(backup_dir, filename)
            if os.path.getctime(filepath) < cutoff:
                os.remove(filepath)
                self.stdout.write(f'Removed old backup: {filename}')