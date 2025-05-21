import logging
import json
from typing import Dict, List, Any, Optional, Tuple
from django.utils import timezone
from django.db.models import Prefetch, Q
from django.contrib.auth import get_user_model
from ..models import Chat, Message, ChatContext, ChatFeedback
from claude_integration.services.claude_client import get_claude_client
from claude_integration.services.prompt_service import get_prompt_service
from vector_db.services.search_service import get_search_service

User = get_user_model()
logger = logging.getLogger(__name__)

class ChatService:
    """
    Сервис для работы с чатами и сообщениями
    """
    def __init__(self):
        self.claude_client = get_claude_client()
        self.prompt_service = get_prompt_service()
        self.search_service = get_search_service()
    
    def create_chat(self, user_id: int, title: str = None) -> Chat:
        """
        Создание нового чата
        
        Args:
            user_id: ID пользователя
            title: Название чата (опционально)
            
        Returns:
            Chat: Созданный чат
        """
        try:
            if not title:
                title = f"Новый чат от {timezone.now().strftime('%d.%m.%Y %H:%M')}"
            
            # Создание чата
            chat = Chat.objects.create(
                user_id=user_id,
                title=title
            )
            
            # Создание пустого контекста
            ChatContext.objects.create(
                chat=chat
            )
            
            # Добавление системного сообщения
            system_prompt = self.prompt_service.get_system_prompt()
            if system_prompt:
                Message.objects.create(
                    chat=chat,
                    role='system',
                    content=system_prompt
                )
            
            return chat
        except Exception as e:
            logger.error(f"Error creating chat: {e}")
            raise
    
    def get_chat(self, chat_id: str, user_id: int) -> Optional[Chat]:
        """
        Получение чата по ID
        
        Args:
            chat_id: ID чата
            user_id: ID пользователя
            
        Returns:
            Optional[Chat]: Чат или None, если чат не найден или не принадлежит пользователю
        """
        try:
            return Chat.objects.get(id=chat_id, user_id=user_id)
        except Chat.DoesNotExist:
            logger.warning(f"Chat {chat_id} not found for user {user_id}")
            return None
        except Exception as e:
            logger.error(f"Error getting chat: {e}")
            return None
    
    def get_user_chats(self, user_id: int) -> List[Chat]:
        """
        Получение списка чатов пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            List[Chat]: Список чатов
        """
        try:
            return list(Chat.objects.filter(user_id=user_id, is_active=True).order_by('-updated_at'))
        except Exception as e:
            logger.error(f"Error getting user chats: {e}")
            return []
    
    def update_chat_title(self, chat_id: str, user_id: int, new_title: str) -> bool:
        """
        Обновление названия чата
        
        Args:
            chat_id: ID чата
            user_id: ID пользователя
            new_title: Новое название
            
        Returns:
            bool: Успешно ли обновлено название
        """
        try:
            chat = self.get_chat(chat_id, user_id)
            if not chat:
                return False
            
            chat.title = new_title
            chat.save(update_fields=['title', 'updated_at'])
            return True
        except Exception as e:
            logger.error(f"Error updating chat title: {e}")
            return False
    
    def delete_chat(self, chat_id: str, user_id: int) -> bool:
        """
        Удаление чата (установка флага is_active=False)
        
        Args:
            chat_id: ID чата
            user_id: ID пользователя
            
        Returns:
            bool: Успешно ли удален чат
        """
        try:
            chat = self.get_chat(chat_id, user_id)
            if not chat:
                return False
            
            chat.is_active = False
            chat.save(update_fields=['is_active', 'updated_at'])
            return True
        except Exception as e:
            logger.error(f"Error deleting chat: {e}")
            return False
    
    def get_chat_messages(self, chat_id: str, user_id: int) -> List[Dict[str, Any]]:
        """
        Получение сообщений чата
        
        Args:
            chat_id: ID чата
            user_id: ID пользователя
            
        Returns:
            List[Dict[str, Any]]: Список сообщений
        """
        try:
            chat = self.get_chat(chat_id, user_id)
            if not chat:
                return []
            
            messages = Message.objects.filter(chat=chat).exclude(role='system').order_by('created_at')
            
            # Преобразование в формат для клиента
            result = []
            for message in messages:
                result.append({
                    'id': str(message.id),
                    'role': message.role,
                    'content': message.content,
                    'created_at': message.created_at.isoformat()
                })
            
            return result
        except Exception as e:
            logger.error(f"Error getting chat messages: {e}")
            return []
    
    def add_message(self, chat_id: str, user_id: int, content: str, role: str = 'user') -> Optional[Message]:
        """
        Добавление сообщения в чат
        
        Args:
            chat_id: ID чата
            user_id: ID пользователя
            content: Содержимое сообщения
            role: Роль отправителя ('user' или 'assistant')
            
        Returns:
            Optional[Message]: Добавленное сообщение или None в случае ошибки
        """
        try:
            chat = self.get_chat(chat_id, user_id)
            if not chat:
                return None
            
            message = Message.objects.create(
                chat=chat,
                role=role,
                content=content
            )
            
            # Обновление времени последнего изменения чата
            chat.updated_at = timezone.now()
            chat.save(update_fields=['updated_at'])
            
            return message
        except Exception as e:
            logger.error(f"Error adding message: {e}")
            return None
    
    def generate_response(self, chat_id: str, user_id: int, user_message: str) -> Tuple[Optional[Message], Dict[str, Any]]:
        """
        Генерация ответа ассистента на сообщение пользователя
        
        Args:
            chat_id: ID чата
            user_id: ID пользователя
            user_message: Сообщение пользователя
            
        Returns:
            Tuple[Optional[Message], Dict[str, Any]]: Ответ ассистента и метаданные или (None, {}) в случае ошибки
        """
        try:
            chat = self.get_chat(chat_id, user_id)
            if not chat:
                return None, {}
            
            # Добавление сообщения пользователя
            user_msg = self.add_message(chat_id, user_id, user_message, role='user')
            if not user_msg:
                raise Exception("Failed to add user message")
            
            # Поиск релевантного контекста
            search_results = self.search_service.search(user_message, top_k=5)
            
            # Обновление контекста чата
            chat_context, _ = ChatContext.objects.get_or_create(chat=chat)
            chat_context.search_results = search_results
            chat_context.save()
            
            # Получение системного промпта
            system_prompt = self.prompt_service.get_system_prompt()
            
            # Формирование контекста из результатов поиска
            context_from_search = self.prompt_service.format_context_for_prompt(user_message)
            
            # Получение истории сообщений чата для контекста
            messages = []
            
            # Добавляем только последние 10 сообщений для ограничения размера контекста
            chat_messages = Message.objects.filter(chat=chat).exclude(role='system').order_by('-created_at')[:10]
            chat_messages = sorted(chat_messages, key=lambda x: x.created_at)
            
            for msg in chat_messages:
                messages.append({
                    'role': msg.role,
                    'content': msg.content
                })
            
            # Добавление контекста к последнему сообщению пользователя
            if messages and messages[-1]['role'] == 'user':
                messages[-1]['content'] = f"{context_from_search}\n\nЗапрос пользователя: {messages[-1]['content']}"
            
            # Генерация ответа
            response_text, metadata = self.claude_client.generate_chat_response(
                user_id=user_id,
                messages=messages,
                system_prompt=system_prompt
            )
            
            # Добавление ответа ассистента
            assistant_msg = self.add_message(chat_id, user_id, response_text, role='assistant')
            
            # Сохранение истории промптов для персонализации
            self.prompt_service.save_prompt_history(
                user_id=user_id,
                prompt=user_message,
                response=response_text
            )
            
            return assistant_msg, metadata
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return None, {'error': str(e)}
    
    def add_feedback(self, message_id: str, user_id: int, rating: int, comment: str = None) -> bool:
        """
        Добавление обратной связи по сообщению ассистента
        
        Args:
            message_id: ID сообщения
            user_id: ID пользователя
            rating: Оценка (от 1 до 5)
            comment: Комментарий (опционально)
            
        Returns:
            bool: Успешно ли добавлена обратная связь
        """
        try:
            message = Message.objects.get(id=message_id, chat__user_id=user_id, role='assistant')
            
            feedback, created = ChatFeedback.objects.update_or_create(
                message=message,
                defaults={
                    'rating': rating,
                    'comment': comment
                }
            )
            
            return True
        except Message.DoesNotExist:
            logger.warning(f"Message {message_id} not found for user {user_id}")
            return False
        except Exception as e:
            logger.error(f"Error adding feedback: {e}")
            return False
    
    def search_in_chats(self, user_id: int, query: str) -> List[Dict[str, Any]]:
        """
        Поиск по чатам пользователя
        
        Args:
            user_id: ID пользователя
            query: Поисковый запрос
            
        Returns:
            List[Dict[str, Any]]: Результаты поиска
        """
        try:
            # Поиск чатов по названию
            chats_by_title = Chat.objects.filter(
                user_id=user_id,
                is_active=True,
                title__icontains=query
            )
            
            # Поиск сообщений по содержимому
            messages = Message.objects.filter(
                chat__user_id=user_id,
                chat__is_active=True,
                content__icontains=query
            ).select_related('chat')
            
            # Получение уникальных ID чатов из результатов поиска сообщений
            chat_ids_from_messages = set(message.chat.id for message in messages)
            
            # Получение чатов с сообщениями, содержащими запрос
            chats_by_messages = Chat.objects.filter(
                id__in=chat_ids_from_messages,
                user_id=user_id,
                is_active=True
            )
            
            # Объединение результатов
            chats = list(chats_by_title) + list(chats_by_messages)
            chats = list({chat.id: chat for chat in chats}.values())  # Удаление дубликатов
            
            # Преобразование в формат для клиента
            results = []
            for chat in chats:
                relevant_messages = [
                    {
                        'id': str(msg.id),
                        'role': msg.role,
                        'content': msg.content,
                        'created_at': msg.created_at.isoformat()
                    }
                    for msg in messages if msg.chat.id == chat.id
                ]
                
                results.append({
                    'id': str(chat.id),
                    'title': chat.title,
                    'created_at': chat.created_at.isoformat(),
                    'updated_at': chat.updated_at.isoformat(),
                    'matches': [
                        {
                            'type': 'title' if chat in chats_by_title else 'message',
                            'content': chat.title if chat in chats_by_title else None,
                            'messages': relevant_messages
                        }
                    ]
                })
            
            return results
        except Exception as e:
            logger.error(f"Error searching in chats: {e}")
            return []


# Инициализация сервиса
_chat_service = None

def get_chat_service() -> ChatService:
    """
    Получение экземпляра сервиса чатов
    
    Returns:
        ChatService: Экземпляр сервиса
    """
    global _chat_service
    if _chat_service is None:
        _chat_service = ChatService()
    return _chat_service