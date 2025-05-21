from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.postgres.fields import ArrayField
import json

class VectorEntry(models.Model):
    """
    Модель для хранения векторных эмбеддингов и связанных метаданных
    """
    entity_type = models.CharField(_('Entity Type'), max_length=100)
    entity_id = models.IntegerField(_('Entity ID'))
    text = models.TextField(_('Text'))
    embedding = ArrayField(
        models.FloatField(),
        size=None,
        verbose_name=_('Embedding Vector')
    )
    metadata = models.JSONField(_('Metadata'), default=dict)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    
    class Meta:
        verbose_name = _('Vector Entry')
        verbose_name_plural = _('Vector Entries')
        unique_together = ('entity_type', 'entity_id')
        indexes = [
            models.Index(fields=['entity_type', 'entity_id']),
        ]
    
    def __str__(self):
        return f"{self.entity_type} - {self.entity_id}"
    
    def get_metadata_display(self):
        """
        Форматированный вывод метаданных
        """
        return json.dumps(self.metadata, ensure_ascii=False, indent=2)


class VectorIndex(models.Model):
    """
    Модель для хранения информации о векторных индексах
    """
    name = models.CharField(_('Index Name'), max_length=255, unique=True)
    index_type = models.CharField(_('Index Type'), max_length=50)  # faiss, milvus, pinecone
    dimension = models.IntegerField(_('Vector Dimension'))
    entity_types = ArrayField(
        models.CharField(max_length=100),
        verbose_name=_('Entity Types'),
        blank=True
    )
    config = models.JSONField(_('Configuration'), default=dict)
    is_active = models.BooleanField(_('Is Active'), default=True)
    last_updated = models.DateTimeField(_('Last Updated'), auto_now=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Vector Index')
        verbose_name_plural = _('Vector Indices')
    
    def __str__(self):
        return f"{self.name} ({self.index_type})"


class SearchLog(models.Model):
    """
    Модель для логирования поисковых запросов
    """
    query = models.TextField(_('Query'))
    user_id = models.IntegerField(_('User ID'), null=True, blank=True)
    results_count = models.IntegerField(_('Results Count'))
    duration_ms = models.IntegerField(_('Duration (ms)'))
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Search Log')
        verbose_name_plural = _('Search Logs')
    
    def __str__(self):
        return f"{self.query} ({self.results_count} results, {self.duration_ms}ms)"