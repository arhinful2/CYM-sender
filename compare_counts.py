from django.apps import apps
import json

data = {}
for m in apps.get_models():
    label = m._meta.app_label
    name = m._meta.model_name
    try:
        s = m.objects.using('sqlite').count()
    except Exception as e:
        s = f"err:{e}"
    try:
        d = m.objects.using('default').count()
    except Exception as e:
        d = f"err:{e}"
    data.setdefault(label, []).append(
        {'model': name, 'sqlite': s, 'default': d})
print(json.dumps(data, indent=2))
