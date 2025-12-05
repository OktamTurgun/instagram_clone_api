import os
from celery import Celery
from celery.schedules import crontab

# Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Celery app
app = Celery('instagram_clone')

# Config from Django settings with CELERY_ prefix
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all installed apps
app.autodiscover_tasks()


# Optional: Periodic tasks (future use - stories cleanup, etc.)
app.conf.beat_schedule = {
    # Example: Delete expired stories every 30 minutes
    # 'delete-expired-stories': {
    #     'task': 'posts.tasks.delete_expired_stories',
    #     'schedule': crontab(minute='*/30'),
    # },
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing"""
    print(f'Request: {self.request!r}')