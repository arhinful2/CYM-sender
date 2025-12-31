import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "church_youth_system.settings")
django.setup()

from django.contrib.auth.models import User

if not User.objects.filter(username="admin").exists():
    User.objects.create_superuser("youth1234", "youth@gmail.com", "youth1234")
    print("Superuser created")
else:
    print("Superuser already exists")
