#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        from django.core.management import execute_from_command_line
        
        # Check if DB_SYNC is enabled and we are running the server
        if os.environ.get('DB_SYNC') == 'true' and 'runserver' in sys.argv:
            print("🛠️  DB_SYNC is ENABLED. Checking for missing tables...")
            try:
                import django
                django.setup()
                from django.core.management import call_command
                call_command('migrate')
                print("✅ Database check complete (new tables created if they were missing)")
            except Exception as e:
                print(f"❌ Database sync failed: {str(e)}")
                # Depending on requirements, might want to exit here
                # sys.exit(1)
        
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
