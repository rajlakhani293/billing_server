from django.apps import AppConfig
from django.db import connection
from django.core.management import call_command
from django.apps import apps


class ShopsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.shops'

    def ready(self):
        """
        Check if all tables for all apps exist when the app is ready.
        If any tables don't exist, run migrations to create them.
        """
        try:
            # Get all installed apps that have models
            installed_apps = []
            for app_config in apps.get_app_configs():
                if app_config.models_module:  # Only include apps that have models
                    installed_apps.append(app_config.name)
            
            # Check each app's tables
            with connection.cursor() as cursor:
                for app_name in installed_apps:
                    try:
                        # Get the app's models to determine expected table names
                        app_config = apps.get_app_config(app_name.split('.')[-1])
                        for model in app_config.get_models():
                            table_name = model._meta.db_table
                            
                            # Check if table exists
                            cursor.execute("SHOW TABLES LIKE %s", [table_name])
                            table_exists = cursor.fetchone()
                            
                            if not table_exists:
                                # Run migrations for this app
                                call_command('migrate', app_name, verbosity=0)
                                break  # Skip to next app after running migrations
                    except Exception:
                        # If checking fails for a specific app, try running its migrations
                        try:
                            call_command('migrate', app_name, verbosity=0)
                        except Exception:
                            pass  # Silently continue if migrations fail
                            
        except Exception:
            # If overall process fails, try running all migrations
            try:
                call_command('migrate', verbosity=0)
            except Exception:
                pass  # Silently continue if all migrations fail
