import os, django, json
os.environ.setdefault('DJANGO_SETTINGS_MODULE','church_youth_system.settings')
django.setup()
from django.apps import apps

# Load counts comparison to find mismatched models
counts_path = 'counts_comparison_utf8.json'
mismatch_models = []
if os.path.exists(counts_path):
    counts = json.load(open(counts_path, 'r', encoding='utf-8'))
    for app_label, models in counts.items():
        for m in models:
            sqlite_count = m.get('sqlite')
            default_count = m.get('default')
            if sqlite_count != default_count:
                mismatch_models.append((app_label, m['model']))

# Ensure critical models included
critical = [('members','member'), ('messaging','message')]
for c in critical:
    if c not in mismatch_models:
        mismatch_models.append(c)

out = {}

for app_label, model_name in mismatch_models:
    key = f"{app_label}.{model_name}"
    out[key] = {'missing_in_default': [], 'missing_in_sqlite': [], 'field_diffs': []}
    try:
        Model = apps.get_model(app_label, model_name)
    except LookupError as e:
        out[key]['error'] = str(e)
        continue

    # get PK lists
    sqlite_pks = list(Model.objects.using('sqlite').values_list('pk', flat=True))
    default_pks = list(Model.objects.using('default').values_list('pk', flat=True))

    sqlite_set = set(sqlite_pks)
    default_set = set(default_pks)

    for pk in sorted(sqlite_set - default_set):
        out[key]['missing_in_default'].append(pk)
    for pk in sorted(default_set - sqlite_set):
        out[key]['missing_in_sqlite'].append(pk)

    common = sorted(sqlite_set & default_set)
    for pk in common:
        s_obj = Model.objects.using('sqlite').filter(pk=pk).values().first()
        d_obj = Model.objects.using('default').filter(pk=pk).values().first()
        diffs = {}
        if s_obj is None or d_obj is None:
            continue
        for field in sorted(set(list(s_obj.keys()) + list(d_obj.keys()))):
            s_val = s_obj.get(field)
            d_val = d_obj.get(field)
            # Normalize bytes to str, Django returns bytes for binary fields sometimes
            if isinstance(s_val, (bytes, bytearray)):
                try:
                    s_val = s_val.decode('utf-8', errors='replace')
                except:
                    s_val = repr(s_val)
            if isinstance(d_val, (bytes, bytearray)):
                try:
                    d_val = d_val.decode('utf-8', errors='replace')
                except:
                    d_val = repr(d_val)
            if s_val != d_val:
                diffs[field] = {'sqlite': s_val, 'default': d_val}
        if diffs:
            out[key]['field_diffs'].append({'pk': pk, 'diffs': diffs})

# Save report
with open('diffs_report.json', 'w', encoding='utf-8') as f:
    json.dump(out, f, indent=2, ensure_ascii=False)
print('Wrote diffs_report.json')
