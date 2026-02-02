from celery import Celery
import os

celery_app = Celery(
    'robotcem',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

@celery_app.task(name='generate_design')
def generate_design_task(job_id: str, prompt: str):
    """Background task for design generation"""
    from cem_engine.core import CEMEngine
    from config import CONFIG
    
    engine = CEMEngine(CONFIG['anthropic_api_key'], CONFIG)
    
    # This would be the actual generation logic
    # moved from the API endpoint to run in background
    
    return {'job_id': job_id, 'status': 'completed'}
