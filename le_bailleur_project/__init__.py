from __future__ import absolute_import, unicode_literals  
import os  
from celery import Celery  

# Set the default Django settings module for the 'celery' program  
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'le_bailleur_project.settings')  

# Create a Celery application instance  
app = Celery('le_bailleur_project')  

# Load Django settings into the app  
app.config_from_object('django.conf:settings', namespace='CELERY')  

# Automatically discover tasks from all registered Django apps  
app.autodiscover_tasks()  