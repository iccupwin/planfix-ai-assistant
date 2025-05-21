from django.db import models
from django.utils.translation import gettext_lazy as _

class PlanfixEntity(models.Model):
    """Базовая абстрактная модель для сущностей Planfix"""
    planfix_id = models.CharField(_('Planfix ID'), max_length=100, unique=True)
    name = models.CharField(_('Name'), max_length=255)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    last_sync = models.DateTimeField(_('Last Sync'), null=True, blank=True)
    
    class Meta:
        abstract = True


class Project(PlanfixEntity):
    """Модель проекта Planfix"""
    description = models.TextField(_('Description'), blank=True, null=True)
    status = models.CharField(_('Status'), max_length=100, blank=True, null=True)
    
    def __str__(self):
        return f"{self.name} (ID: {self.planfix_id})"
    
    class Meta:
        verbose_name = _('Project')
        verbose_name_plural = _('Projects')


class Employee(PlanfixEntity):
    """Модель сотрудника Planfix"""
    email = models.EmailField(_('Email'), blank=True, null=True)
    position = models.CharField(_('Position'), max_length=255, blank=True, null=True)
    
    def __str__(self):
        return f"{self.name} (ID: {self.planfix_id})"
    
    class Meta:
        verbose_name = _('Employee')
        verbose_name_plural = _('Employees')


class Task(PlanfixEntity):
    """Модель задачи Planfix"""
    description = models.TextField(_('Description'), blank=True, null=True)
    status = models.CharField(_('Status'), max_length=100, blank=True, null=True)
    priority = models.CharField(_('Priority'), max_length=50, blank=True, null=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, 
                               related_name='tasks', null=True, blank=True)
    assignee = models.ForeignKey(Employee, on_delete=models.SET_NULL, 
                                related_name='assigned_tasks', null=True, blank=True)
    due_date = models.DateTimeField(_('Due Date'), null=True, blank=True)
    
    def __str__(self):
        return f"{self.name} (ID: {self.planfix_id})"
    
    class Meta:
        verbose_name = _('Task')
        verbose_name_plural = _('Tasks')


class Comment(PlanfixEntity):
    """Модель комментария к задаче Planfix"""
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField(_('Text'))
    author = models.ForeignKey(Employee, on_delete=models.SET_NULL, 
                              related_name='comments', null=True, blank=True)
    
    def __str__(self):
        return f"Comment to Task {self.task.planfix_id}"
    
    class Meta:
        verbose_name = _('Comment')
        verbose_name_plural = _('Comments')


class Document(PlanfixEntity):
    """Модель документа из Planfix"""
    description = models.TextField(_('Description'), blank=True, null=True)
    file_url = models.URLField(_('File URL'), blank=True, null=True)
    file_type = models.CharField(_('File Type'), max_length=100, blank=True, null=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, 
                               related_name='documents', null=True, blank=True)
    content = models.TextField(_('Content'), blank=True, null=True)  # Содержимое документа для векторизации
    
    def __str__(self):
        return f"{self.name} (ID: {self.planfix_id})"
    
    class Meta:
        verbose_name = _('Document')
        verbose_name_plural = _('Documents')


class SyncLog(models.Model):
    """Модель для логирования процесса синхронизации"""
    entity_type = models.CharField(_('Entity Type'), max_length=100)
    entity_id = models.CharField(_('Entity ID'), max_length=100, blank=True, null=True)
    status = models.CharField(_('Status'), max_length=50)
    message = models.TextField(_('Message'), blank=True, null=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    
    def __str__(self):
        return f"{self.entity_type} - {self.status} - {self.created_at}"
    
    class Meta:
        verbose_name = _('Sync Log')
        verbose_name_plural = _('Sync Logs')