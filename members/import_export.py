# members/import_export.py
import csv
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
import pandas as pd

def import_members_from_csv(file_path, user):
    """Import members from CSV with enhanced error handling"""
    results = {
        'success': 0,
        'failed': 0,
        'errors': []
    }
    
    try:
        df = pd.read_csv(file_path)
        
        for index, row in df.iterrows():
            try:
                member = Member(
                    first_name=row.get('first_name', ''),
                    last_name=row.get('last_name', ''),
                    email=row.get('email', ''),
                    phone_number=row.get('phone_number', ''),
                    created_by=user
                )
                
                # Handle photo if provided
                if 'photo_url' in row and row['photo_url']:
                    # Download and save photo
                    # ... implementation ...
                    pass
                
                member.save()
                results['success'] += 1
                
            except Exception as e:
                results['failed'] += 1
                results['errors'].append(f"Row {index+2}: {str(e)}")
    
    except Exception as e:
        results['errors'].append(f"File error: {str(e)}")
    
    return results