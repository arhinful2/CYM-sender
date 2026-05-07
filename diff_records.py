from django.apps import apps
import os
import django
import json
import datetime
import decimal
import uuid
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'church_youth_system.settings')
django.setup()

# Load counts comparison to find mismatched models
counts_path = 'counts_comparison_utf8.json'
mismatch_models = []
if os.path.exists(counts_path):
    # Use utf-8-sig to tolerate BOM if present
    with open(counts_path, 'r', encoding='utf-8-sig') as fh:
        counts = json.load(fh)
    for app_label, models in counts.items():
        for m in models:
            sqlite_count = m.get('sqlite')
            default_count = m.get('default')
            if sqlite_count != default_count:
                mismatch_models.append((app_label, m['model']))

# Ensure critical models included
critical = [('members', 'member'), ('messaging', 'message')]
for c in critical:
    if c not in mismatch_models:
        mismatch_models.append(c)

out = {}


def _normalize(v):
    if isinstance(v, (bytes, bytearray)):
        try:
            return v.decode('utf-8', errors='replace')
        except Exception:
            return repr(v)
    if isinstance(v, (datetime.datetime, datetime.date, datetime.time)):
        return v.isoformat()
    if isinstance(v, decimal.Decimal):
        return float(v)
    if isinstance(v, uuid.UUID):
        return str(v)
    return v


for app_label, model_name in mismatch_models:
    key = f"{app_label}.{model_name}"
    out[key] = {'missing_in_default': [],
                'missing_in_sqlite': [], 'field_diffs': []}
    try:
        Model = apps.get_model(app_label, model_name)
    except LookupError as e:
        out[key]['error'] = str(e)
        continue

    # get PK lists
    sqlite_pks = list(Model.objects.using(
        'sqlite').values_list('pk', flat=True))
    default_pks = list(Model.objects.using(
        'default').values_list('pk', flat=True))

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
            s_val = _normalize(s_obj.get(field))
            d_val = _normalize(d_obj.get(field))
            if s_val != d_val:
                diffs[field] = {'sqlite': s_val, 'default': d_val}
        if diffs:
            out[key]['field_diffs'].append({'pk': pk, 'diffs': diffs})

# Save report
# Normalize PKs and any remaining values to JSON-serializable types
for key, val in out.items():
    val['missing_in_default'] = [_normalize(
        x) for x in val.get('missing_in_default', [])]
    val['missing_in_sqlite'] = [_normalize(
        x) for x in val.get('missing_in_sqlite', [])]
    for item in val.get('field_diffs', []):
        item['pk'] = _normalize(item.get('pk'))
        # diffs already normalized

with open('diffs_report.json', 'w', encoding='utf-8') as f:
    json.dump(out, f, indent=2, ensure_ascii=False)
print('Wrote diffs_report.json')
