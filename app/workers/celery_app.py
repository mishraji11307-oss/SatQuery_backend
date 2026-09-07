"""
SatQuery AI - Celery Background Task Broker Configuration
"""
from app.core.config import settings
from app.core.logging import logger

try:
    from celery import Celery
    _HAS_CELERY = True
except ImportError:
    _HAS_CELERY = False

celery_app = None

if _HAS_CELERY:
    try:
        celery_app = Celery(
            "satquery_worker",
            broker=settings.CELERY_BROKER_URL,
            backend=settings.CELERY_RESULT_BACKEND,
            include=["app.workers.analysis_tasks"]
        )
        celery_app.conf.update(
            task_serializer="json",
            accept_content=["json"],
            result_serializer="json",
            timezone="UTC",
            enable_utc=True,
            task_track_started=True,
        )
    except Exception as e:
        logger.warning(f"Celery initialization deferred: {e}")
