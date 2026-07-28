import csv
import os
from django.core.management.base import BaseCommand
from members.models import Member
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Import members from CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to CSV file')
        parser.add_argument('--user', type=int, help='User ID for created_by field')

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        user_id = options.get('user')
        
        if user_id:
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'User with ID {user_id} does not exist'))
                return
        else:
            user = User.objects.first()
        
        if not os.path.exists(csv_file):
            self.stdout.write(self.style.ERROR(f'File {csv_file} does not exist'))
            return
        
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            count = 0
            
            for row in reader:
                try:
                    member, created = Member.objects.update_or_create(
                        email=row['email'],
                        defaults={
                            'first_name': row.get('first_name', ''),
                            'last_name': row.get('last_name', ''),
                            'phone_number': row.get('phone_number', ''),
                            'created_by': user,
                        }
                    )
                    
                    if created:
                        count += 1
                        self.stdout.write(f'Created: {member.full_name()}')
                    
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error importing row: {e}'))
        
        self.stdout.write(self.style.SUCCESS(f'Successfully imported {count} members'))