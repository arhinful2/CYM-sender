import os
import tempfile
from django.conf import settings
from django.core.management import BaseCommand, call_command


class Command(BaseCommand):
    help = 'Copy data from the local SQLite database into the active PostgreSQL database.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--source-db',
            default='sqlite',
            help='Source database alias to export from. Default: sqlite',
        )
        parser.add_argument(
            '--target-db',
            default='default',
            help='Target database alias to load into. Default: default',
        )
        parser.add_argument(
            '--exclude',
            action='append',
            default=['contenttypes', 'auth.permission', 'sessions', 'admin.logentry'],
            help='Model labels to exclude from the transfer. Can be used multiple times.',
        )

    def handle(self, *args, **options):
        source_db = options['source_db']
        target_db = options['target_db']
        excludes = options['exclude'] or []

        if source_db not in settings.DATABASES:
            self.stderr.write(self.style.ERROR(f'Source database alias "{source_db}" is not configured.'))
            return

        if target_db not in settings.DATABASES:
            self.stderr.write(self.style.ERROR(f'Target database alias "{target_db}" is not configured.'))
            return

        source_engine = settings.DATABASES[source_db]['ENGINE']
        target_engine = settings.DATABASES[target_db]['ENGINE']

        if 'sqlite' not in source_engine:
            self.stderr.write(self.style.ERROR(f'Source database "{source_db}" must be SQLite. Current engine: {source_engine}'))
            return

        if 'sqlite' in target_engine:
            self.stderr.write(self.style.ERROR('Target database must be PostgreSQL-like, not SQLite.'))
            return

        self.stdout.write(f'Exporting data from {source_db}...')
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False, encoding='utf-8') as temp_file:
            temp_path = temp_file.name
            call_command(
                'dumpdata',
                database=source_db,
                natural_foreign=True,
                natural_primary=True,
                indent=2,
                exclude=excludes,
                stdout=temp_file,
            )

        try:
            self.stdout.write(f'Loading exported data into {target_db}...')
            call_command('loaddata', temp_path, database=target_db)
            self.stdout.write(self.style.SUCCESS('SQLite data copied into PostgreSQL successfully.'))
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
                self.stdout.write(f'Removed temporary export file: {temp_path}')
