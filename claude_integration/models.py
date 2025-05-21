from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

User = get_user_model()

class ClaudeModelConfig(models.Model):
    """
    Модель для хранения информации о модели Claude
    """
    name = models.CharField(_('Model Name'), max_length=255)
    api_id = models.CharField(_('API ID'), max_length=255, unique=True)
    is_active = models.BooleanField(_('Is Active'), default=True)
    description = models.TextField(_('Description'), blank=True, null=True)
    max_tokens = models.IntegerField(_('Max Tokens'), default=100000)
    cost_per_1k_tokens = models.DecimalField(_('Cost per 1K Tokens'), max_digits=8, decimal_places=6, default=0.0)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = _('Claude Model Config')
        verbose_name_plural = _('Claude Model Configs')


class PromptTemplate(models.Model):
    """
    Модель для хранения шаблонов промптов
    """
    name = models.CharField(_('Template Name'), max_length=255)
    description = models.TextField(_('Description'), blank=True, null=True)
    template = models.TextField(_('Template'))
    is_system = models.BooleanField(_('Is System'), default=False)
    is_active = models.BooleanField(_('Is Active'), default=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = _('Prompt Template')
        verbose_name_plural = _('Prompt Templates')


class ClaudeAPIRequest(models.Model):
    """
    Модель для хранения информации о запросах к API Claude
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='claude_requests')
    prompt = models.TextField(_('Prompt'))
    model = models.ForeignKey(ClaudeModelConfig, on_delete=models.SET_NULL, null=True, blank=True)
    temperature = models.FloatField(_('Temperature'), default=0.7)
    max_tokens = models.IntegerField(_('Max Tokens'), default=1000)
    top_p = models.FloatField(_('Top P'), default=0.9)
    status = models.CharField(_('Status'), max_length=50)  # success, error
    error_message = models.TextField(_('Error Message'), blank=True, null=True)
    token_count = models.IntegerField(_('Token Count'), default=0)
    duration_ms = models.IntegerField(_('Duration (ms)'), default=0)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    
    def __str__(self):
        return f"Request by {self.user.email} at {self.created_at}"
    
    class Meta:
        verbose_name = _('Claude API Request')
        verbose_name_plural = _('Claude API Requests')


class ClaudeAPIResponse(models.Model):
    """
    Модель для хранения ответов от API Claude
    """
    request = models.OneToOneField(ClaudeAPIRequest, on_delete=models.CASCADE, related_name='response')
    response_text = models.TextField(_('Response Text'))
    token_count = models.IntegerField(_('Token Count'), default=0)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    
    def __str__(self):
        return f"Response for {self.request}"
    
    class Meta:
        verbose_name = _('Claude API Response')
        verbose_name_plural = _('Claude API Responses')


class UserPromptHistory(models.Model):
    """
    Модель для хранения истории промптов пользователя для персонализации
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='prompt_history')
    prompt = models.TextField(_('Prompt'))
    response = models.TextField(_('Response'))
    is_useful = models.BooleanField(_('Is Useful'), default=True)
    feedback = models.TextField(_('Feedback'), blank=True, null=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    
    def __str__(self):
        return f"Prompt by {self.user.email} at {self.created_at}"
    
    class Meta:
        verbose_name = _('User Prompt History')
        verbose_name_plural = _('User Prompt History')
        ordering = ['-created_at']