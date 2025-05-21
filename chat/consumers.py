import json
import logging
from typing import Dict, Any, Optional
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .services.chat_service import get_chat_service

User = get_user_model()
logger = logging.getLogger(__name__)

class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket потребитель для обработки сообщений чата в реальном времени
    """
    
    async def connect(self):
        """
        Обработчик подключения к WebSocket
        """
        # Получение ID чата из URL
        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        self.user = self.scope['user']
        
        # Проверка аутентификации пользователя
        if self.user.is_anonymous:
            await self.close(code=4001)
            return
        
        # Проверка доступа к чату
        if not await self.check_chat_access():
            await self.close(code=4003)
            return
        
        # Создание группы для чата
        self.chat_group_name = f'chat_{self.chat_id}'
        
        # Подключение к группе
        await self.channel_layer.group_add(
            self.chat_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        """
        Обработчик отключения от WebSocket
        
        Args:
            close_code: Код закрытия соединения
        """
        # Отключение от группы
        await self.channel_layer.group_discard(
            self.chat_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """
        Обработчик получения сообщения от клиента
        
        Args:
            text_data: Текст сообщения в формате JSON
        """
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')
            
            # Обработка различных типов сообщений
            if message_type == 'user_message':
                await self.handle_user_message(text_data_json)
            elif message_type == 'typing':
                await self.handle_typing(text_data_json)
            elif message_type == 'feedback':
                await self.handle_feedback(text_data_json)
            else:
                logger.warning(f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError:
            logger.error("Invalid JSON format")
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            
            # Отправка сообщения об ошибке клиенту
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f"Error processing message: {str(e)}"
            }))
    
    async def handle_user_message(self, data):
        """
        Обработка сообщения пользователя
        
        Args:
            data: Данные сообщения
        """
        message_content = data.get('content', '')
        message_id = data.get('id', '')  # ID сообщения от клиента
        
        if not message_content:
            return
        
        # Отправка уведомления о получении сообщения
        await self.send(text_data=json.dumps({
            'type': 'message_received',
            'id': message_id
        }))
        
        # Отправка уведомления о начале генерации ответа
        await self.channel_layer.group_send(
            self.chat_group_name,
            {
                'type': 'assistant_typing',
                'is_typing': True
            }
        )
        
        # Добавление сообщения пользователя и генерация ответа
        assistant_message, metadata = await self.generate_response(message_content)
        
        # Отправка ответа ассистента
        if assistant_message:
            await self.channel_layer.group_send(
                self.chat_group_name,
                {
                    'type': 'chat_message',
                    'message': {
                        'id': str(assistant_message.id),
                        'role': 'assistant',
                        'content': assistant_message.content,
                        'created_at': assistant_message.created_at.isoformat()
                    },
                    'metadata': metadata
                }
            )
        else:
            # Отправка сообщения об ошибке
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': "Failed to generate response"
            }))
        
        # Отправка уведомления о завершении генерации ответа
        await self.channel_layer.group_send(
            self.chat_group_name,
            {
                'type': 'assistant_typing',
                'is_typing': False
            }
        )
    
    async def handle_typing(self, data):
        """
        Обработка события набора текста
        
        Args:
            data: Данные события
        """
        is_typing = data.get('is_typing', False)
        
        # Отправка уведомления о наборе текста всем участникам чата
        await self.channel_layer.group_send(
            self.chat_group_name,
            {
                'type': 'user_typing',
                'user_id': self.user.id,
                'is_typing': is_typing
            }
        )
    
    async def handle_feedback(self, data):
        """
        Обработка обратной связи по сообщению
        
        Args:
            data: Данные обратной связи
        """
        message_id = data.get('message_id')
        rating = data.get('rating')
        comment = data.get('comment', '')
        
        if not message_id or not rating:
            return
        
        # Добавление обратной связи
        success = await self.add_feedback(message_id, rating, comment)
        
        # Отправка уведомления о результате
        await self.send(text_data=json.dumps({
            'type': 'feedback_result',
            'success': success,
            'message_id': message_id
        }))
    
    async def chat_message(self, event):
        """
        Обработчик события сообщения в чате
        
        Args:
            event: Данные события
        """
        message = event['message']
        metadata = event.get('metadata', {})
        
        # Отправка сообщения клиенту
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': message,
            'metadata': metadata
        }))
    
    async def user_typing(self, event):
        """
        Обработчик события набора текста пользователем
        
        Args:
            event: Данные события
        """
        user_id = event['user_id']
        is_typing = event['is_typing']
        
        # Отправка уведомления о наборе текста клиенту
        await self.send(text_data=json.dumps({
            'type': 'user_typing',
            'user_id': user_id,
            'is_typing': is_typing
        }))
    
    async def assistant_typing(self, event):
        """
        Обработчик события набора текста ассистентом
        
        Args:
            event: Данные события
        """
        is_typing = event['is_typing']
        
        # Отправка уведомления о наборе текста клиенту
        await self.send(text_data=json.dumps({
            'type': 'assistant_typing',
            'is_typing': is_typing
        }))
    
    @database_sync_to_async
    def check_chat_access(self) -> bool:
        """
        Проверка доступа пользователя к чату
        
        Returns:
            bool: Имеет ли пользователь доступ к чату
        """
        chat_service = get_chat_service()
        chat = chat_service.get_chat(self.chat_id, self.user.id)
        return chat is not None
    
    @database_sync_to_async
    def generate_response(self, message_content: str) -> tuple:
        """
        Генерация ответа ассистента
        
        Args:
            message_content: Содержимое сообщения пользователя
            
        Returns:
            tuple: Сообщение ассистента и метаданные
        """
        chat_service = get_chat_service()
        return chat_service.generate_response(self.chat_id, self.user.id, message_content)
    
    @database_sync_to_async
    def add_feedback(self, message_id: str, rating: int, comment: str) -> bool:
        """
        Добавление обратной связи по сообщению
        
        Args:
            message_id: ID сообщения
            rating: Оценка
            comment: Комментарий
            
        Returns:
            bool: Успешно ли добавлена обратная связь
        """
        chat_service = get_chat_service()
        return chat_service.add_feedback(message_id, self.user.id, rating, comment)