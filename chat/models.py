from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()

class Chat(models.Model):
    """
    Модель чата
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chats')
    title = models.CharField(_('Title'), max_length=255)
    is_active = models.BooleanField(_('Is Active'), default=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    
    def __str__(self):
        return f"{self.title} ({self.user.email})"
    
    class Meta:
        verbose_name = _('Chat')
        verbose_name_plural = _('Chats')
        ordering = ['-updated_at']


class Message(models.Model):
    """
    Модель сообщения в чате
    """
    ROLE_CHOICES = (
        ('user', _('User')),
        ('assistant', _('Assistant')),
        ('system', _('System'))
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(_('Role'), max_length=20, choices=ROLE_CHOICES)
    content = models.TextField(_('Content'))
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    
    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."
    
    class Meta:
        verbose_name = _('Message')
        verbose_name_plural = _('Messages')
        ordering = ['created_at']


class ChatContext(models.Model):
    """
    Модель для хранения контекста чата (результаты поиска и т.д.)
    """
    chat = models.OneToOneField(Chat, on_delete=models.CASCADE, related_name='context')
    search_results = models.JSONField(_('Search Results'), default=dict)
    custom_context = models.TextField(_('Custom Context'), blank=True, null=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    
    def __str__(self):
        return f"Context for {self.chat}"
    
    class Meta:
        verbose_name = _('Chat Context')
        verbose_name_plural = _('Chat Contexts')


class ChatFeedback(models.Model):
    """
    Модель для обратной связи по сообщениям ассистента
    """
    RATING_CHOICES = (
        (1, _('Very Poor')),
        (2, _('Poor')),
        (3, _('Average')),
        (4, _('Good')),
        (5, _('Excellent'))
    )
    
    message = models.OneToOneField(Message, on_delete=models.CASCADE, related_name='feedback')
    rating = models.IntegerField(_('Rating'), choices=RATING_CHOICES)
    comment = models.TextField(_('Comment'), blank=True, null=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    
    def __str__(self):
        return f"Feedback for message {self.message.id} - {self.rating}/5"
    
    class Meta:
        verbose_name = _('Chat Feedback')
        verbose_name_plural = _('Chat Feedbacks')