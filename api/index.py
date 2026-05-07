import os
import sys
from pathlib import Path

# Ensure project root is importable in Vercel serverless runtime.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'church_youth_system.settings')

from django.core.wsgi import get_wsgi_application  # noqa: E402

app = get_wsgi_application()
