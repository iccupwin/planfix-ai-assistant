import logging
from typing import Dict, List, Any, Optional
from django.utils import timezone
from django.contrib.auth import get_user_model
from ..models import PromptTemplate, UserPromptHistory
from vector_db.services.search_service import get_search_service

User = get_user_model()
logger = logging.getLogger(__name__)

class PromptService:
    """
    Сервис для формирования и обработки промптов для Claude AI
    """
    def __init__(self):
        self.search_service = get_search_service()
    
    def get_system_prompt(self) -> str:
        """
        Получение системного промпта для Claude AI
        
        Returns:
            str: Системный промпт
        """
        try:
            system_template = PromptTemplate.objects.filter(
                name='system_prompt',
                is_system=True,
                is_active=True
            ).first()
            
            if system_template:
                return system_template.template
            
            # Если шаблон не найден, используем значение по умолчанию
            return """Ты — ИИ-ассистент с доступом к данным из Planfix. Твоя задача — помогать пользователям находить информацию из их рабочего пространства и отвечать на вопросы на основе этих данных.

Используй предоставленный контекст для ответов на вопросы. Если информации недостаточно, сообщи об этом пользователю. Не выдумывай факты и не делай предположений.

При ответе на вопросы:
1. Учитывай все релевантные данные из контекста
2. Структурируй ответ логически, используя маркированные списки при необходимости
3. Если ответ содержит информацию из проектов или задач, указывай их названия и ID
4. Если пользователь запрашивает конкретную информацию о задаче, проекте или сотруднике, предоставь детали
5. При отсутствии информации в контексте, предложи выполнить поиск по другим параметрам

Ты должен отвечать только на русском языке, даже если пользователь пишет на другом языке."""
        except Exception as e:
            logger.error(f"Error getting system prompt: {e}")
            return ""
    
    def format_context_for_prompt(self, query: str, top_k: int = 5) -> str:
        """
        Форматирование контекста из результатов поиска для промпта
        
        Args:
            query: Поисковый запрос
            top_k: Количество результатов для включения в контекст
            
        Returns:
            str: Отформатированный контекст
        """
        try:
            # Выполнение семантического поиска
            search_results = self.search_service.search(query, top_k=top_k)
            
            if not search_results or not search_results.get('results'):
                return "Контекст: По вашему запросу не найдено релевантной информации."
            
            # Формирование контекста
            context_parts = ["Контекст:"]
            
            # Обработка проектов
            if 'project' in search_results['results']:
                context_parts.append("Проекты:")
                for i, result in enumerate(search_results['results']['project'], 1):
                    project = result.get('project', {})
                    context_parts.append(f"{i}. {project.get('name')} (ID: {project.get('planfix_id')})")
                    if project.get('description'):
                        context_parts.append(f"   Описание: {project.get('description')}")
                    context_parts.append(f"   Статус: {project.get('status')}")
                    context_parts.append("")
            
            # Обработка задач
            if 'task' in search_results['results']:
                context_parts.append("Задачи:")
                for i, result in enumerate(search_results['results']['task'], 1):
                    task = result.get('task', {})
                    context_parts.append(f"{i}. {task.get('name')} (ID: {task.get('planfix_id')})")
                    if task.get('description'):
                        context_parts.append(f"   Описание: {task.get('description')}")
                    context_parts.append(f"   Статус: {task.get('status')}")
                    context_parts.append(f"   Приоритет: {task.get('priority')}")
                    
                    if task.get('project'):
                        context_parts.append(f"   Проект: {task.get('project', {}).get('name')} (ID: {task.get('project', {}).get('planfix_id')})")
                    
                    if task.get('assignee'):
                        context_parts.append(f"   Исполнитель: {task.get('assignee', {}).get('name')}")
                    
                    if task.get('due_date'):
                        context_parts.append(f"   Срок: {task.get('due_date')}")
                    
                    context_parts.append("")
            
            # Обработка сотрудников
            if 'employee' in search_results['results']:
                context_parts.append("Сотрудники:")
                for i, result in enumerate(search_results['results']['employee'], 1):
                    employee = result.get('employee', {})
                    context_parts.append(f"{i}. {employee.get('name')} (ID: {employee.get('planfix_id')})")
                    if employee.get('email'):
                        context_parts.append(f"   Email: {employee.get('email')}")
                    if employee.get('position'):
                        context_parts.append(f"   Должность: {employee.get('position')}")
                    context_parts.append("")
            
            # Обработка комментариев
            if 'comment' in search_results['results']:
                context_parts.append("Комментарии:")
                for i, result in enumerate(search_results['results']['comment'], 1):
                    comment = result.get('comment', {})
                    task_name = comment.get('task', {}).get('name', 'Неизвестная задача')
                    author_name = comment.get('author', {}).get('name', 'Неизвестный автор')
                    context_parts.append(f"{i}. Комментарий к задаче \"{task_name}\" от {author_name}:")
                    context_parts.append(f"   {comment.get('text')}")
                    context_parts.append("")
            
            # Обработка документов
            if 'document' in search_results['results']:
                context_parts.append("Документы:")
                for i, result in enumerate(search_results['results']['document'], 1):
                    document = result.get('document', {})
                    context_parts.append(f"{i}. {document.get('name')} (ID: {document.get('planfix_id')})")
                    if document.get('description'):
                        context_parts.append(f"   Описание: {document.get('description')}")
                    if document.get('project'):
                        context_parts.append(f"   Проект: {document.get('project', {}).get('name')}")
                    context_parts.append("")
            
            # Обработка содержимого документов
            if 'document_content' in search_results['results']:
                context_parts.append("Содержимое документов:")
                for i, result in enumerate(search_results['results']['document_content'], 1):
                    document = result.get('document_content', {})
                    context_parts.append(f"{i}. {document.get('name')} (ID: {document.get('planfix_id')})")
                    if document.get('content_preview'):
                        context_parts.append(f"   Фрагмент содержимого: {document.get('content_preview')}")
                    context_parts.append("")
            
            return "\n".join(context_parts)
        except Exception as e:
            logger.error(f"Error formatting context for prompt: {e}")
            return "Контекст: Произошла ошибка при получении контекста."
    
    def create_prompt_with_context(self, query: str, user_id: Optional[int] = None) -> str:
        """
        Создание промпта с контекстом из результатов поиска
        
        Args:
            query: Запрос пользователя
            user_id: ID пользователя
            
        Returns:
            str: Промпт с контекстом
        """
        # Получение контекста
        context = self.format_context_for_prompt(query)
        
        # Получение истории запросов пользователя, если указан ID
        user_history = ""
        if user_id:
            try:
                history_entries = UserPromptHistory.objects.filter(
                    user_id=user_id,
                    is_useful=True
                ).order_by('-created_at')[:5]
                
                if history_entries:
                    user_history = "История запросов пользователя:\n"
                    for entry in history_entries:
                        user_history += f"- Запрос: {entry.prompt}\n"
                        user_history += f"  Ответ: {entry.response[:100]}...\n\n"
            except Exception as e:
                logger.error(f"Error getting user history: {e}")
        
        # Формирование полного промпта
        full_prompt = f"{context}\n\n{user_history}\n\nЗапрос пользователя: {query}"
        return full_prompt
    
    def save_prompt_history(self, user_id: int, prompt: str, response: str, is_useful: bool = True) -> None:
        """
        Сохранение истории запросов пользователя
        
        Args:
            user_id: ID пользователя
            prompt: Запрос пользователя
            response: Ответ на запрос
            is_useful: Был ли ответ полезен
        """
        try:
            UserPromptHistory.objects.create(
                user_id=user_id,
                prompt=prompt,
                response=response,
                is_useful=is_useful
            )
        except Exception as e:
            logger.error(f"Error saving prompt history: {e}")


# Инициализация сервиса
_prompt_service = None

def get_prompt_service() -> PromptService:
    """
    Получение экземпляра сервиса промптов
    
    Returns:
        PromptService: Экземпляр сервиса
    """
    global _prompt_service
    if _prompt_service is None:
        _prompt_service = PromptService()
    return _prompt_service