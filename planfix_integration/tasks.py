from celery import shared_task
import logging
from django.utils import timezone
from django.conf import settings
from .services.sync_service import PlanfixSyncService
from .models import SyncLog

logger = logging.getLogger(__name__)

@shared_task
def sync_all_planfix_data():
    """
    Celery задача для полной синхронизации всех данных из Planfix
    """
    logger.info("Starting full Planfix sync task")
    
    try:
        sync_service = PlanfixSyncService()
        results = sync_service.sync_all()
        
        # Логирование успешной синхронизации
        SyncLog.objects.create(
            entity_type='all',
            status='success',
            message=f"Full sync completed: {results}"
        )
        
        return results
    except Exception as e:
        logger.error(f"Error in full Planfix sync task: {e}")
        
        # Логирование ошибки синхронизации
        SyncLog.objects.create(
            entity_type='all',
            status='error',
            message=str(e)
        )
        
        # Пробрасываем исключение дальше для обработки Celery
        raise


@shared_task
def sync_projects():
    """
    Celery задача для синхронизации проектов из Planfix
    """
    logger.info("Starting Planfix projects sync task")
    
    try:
        sync_service = PlanfixSyncService()
        results = sync_service.sync_projects()
        
        # Логирование успешной синхронизации
        SyncLog.objects.create(
            entity_type='projects',
            status='success',
            message=f"Projects sync completed: {results}"
        )
        
        return results
    except Exception as e:
        logger.error(f"Error in Planfix projects sync task: {e}")
        
        # Логирование ошибки синхронизации
        SyncLog.objects.create(
            entity_type='projects',
            status='error',
            message=str(e)
        )
        
        # Пробрасываем исключение дальше для обработки Celery
        raise


@shared_task
def sync_tasks():
    """
    Celery задача для синхронизации задач из Planfix
    """
    logger.info("Starting Planfix tasks sync task")
    
    try:
        sync_service = PlanfixSyncService()
        results = sync_service.sync_tasks()
        
        # Логирование успешной синхронизации
        SyncLog.objects.create(
            entity_type='tasks',
            status='success',
            message=f"Tasks sync completed: {results}"
        )
        
        return results
    except Exception as e:
        logger.error(f"Error in Planfix tasks sync task: {e}")
        
        # Логирование ошибки синхронизации
        SyncLog.objects.create(
            entity_type='tasks',
            status='error',
            message=str(e)
        )
        
        # Пробрасываем исключение дальше для обработки Celery
        raise


@shared_task
def sync_employees():
    """
    Celery задача для синхронизации сотрудников из Planfix
    """
    logger.info("Starting Planfix employees sync task")
    
    try:
        sync_service = PlanfixSyncService()
        results = sync_service.sync_employees()
        
        # Логирование успешной синхронизации
        SyncLog.objects.create(
            entity_type='employees',
            status='success',
            message=f"Employees sync completed: {results}"
        )
        
        return results
    except Exception as e:
        logger.error(f"Error in Planfix employees sync task: {e}")
        
        # Логирование ошибки синхронизации
        SyncLog.objects.create(
            entity_type='employees',
            status='error',
            message=str(e)
        )
        
        # Пробрасываем исключение дальше для обработки Celery
        raise


@shared_task
def sync_documents():
    """
    Celery задача для синхронизации документов из Planfix
    """
    logger.info("Starting Planfix documents sync task")
    
    try:
        sync_service = PlanfixSyncService()
        results = sync_service.sync_documents()
        
        # Логирование успешной синхронизации
        SyncLog.objects.create(
            entity_type='documents',
            status='success',
            message=f"Documents sync completed: {results}"
        )
        
        return results
    except Exception as e:
        logger.error(f"Error in Planfix documents sync task: {e}")
        
        # Логирование ошибки синхронизации
        SyncLog.objects.create(
            entity_type='documents',
            status='error',
            message=str(e)
        )
        
        # Пробрасываем исключение дальше для обработки Celery
        raise


@shared_task
def setup_periodic_sync():
    """
    Настройка периодической синхронизации данных
    """
    from django_celery_beat.models import PeriodicTask, IntervalSchedule
    
    # Определяем интервал синхронизации из настроек
    interval_seconds = settings.PLANFIX_SYNC_INTERVAL
    
    # Создаем расписание
    schedule, _ = IntervalSchedule.objects.get_or_create(
        every=interval_seconds,
        period=IntervalSchedule.SECONDS,
    )
    
    # Создаем или обновляем периодическую задачу
    PeriodicTask.objects.update_or_create(
        name='Sync Planfix data',
        defaults={
            'task': 'planfix_integration.tasks.sync_all_planfix_data',
            'interval': schedule,
            'enabled': True,
        }
    )
    
    logger.info(f"Periodic sync setup completed with interval {interval_seconds} seconds")