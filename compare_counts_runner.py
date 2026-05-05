from django.apps import apps
import os
import django
import json
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'church_youth_system.settings')
django.setup()

data = {}
for m in apps.get_models():
    l = m._meta.app_label
    name = m._meta.model_name
    try:
        s = m.objects.using('sqlite').count()
    except Exception as e:
        s = f"err:{e}"
    try:
        d = m.objects.using('default').count()
    except Exception as e:
        d = f"err:{e}"
    data.setdefault(l, []).append({'model': name, 'sqlite': s, 'default': d})
print(json.dumps(data, indent=2))
