# Vercel deployment checklist

- Build command:

  python manage.py migrate --noinput && python manage.py collectstatic --noinput

- Required environment variables in Vercel:
  - `DATABASE_URL`
  - `DJANGO_SECRET_KEY`
  - `ALLOWED_HOSTS`
  - Any SMS, email, or storage provider secrets your app uses

- Why this matters:
  - `messaging/migrations/0007_create_default_templates.py` now seeds the local/hosted database with your message templates.
  - The old Vercel build command referenced `python create_sample_templates.py`, which does not exist at the repo root and can break deployments.

- If you still see a 500 after redeploy:
  - Open the latest Vercel deployment logs.
  - Check for missing env vars or database errors.
  - Confirm the hosted database has all migrations applied.
