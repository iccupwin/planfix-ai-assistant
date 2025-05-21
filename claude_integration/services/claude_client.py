import logging
import requests
import time
import json
from typing import Dict, List, Any, Optional, Tuple
from django.conf import settings
from django.utils import timezone
from ..models import ClaudeAPIRequest, ClaudeAPIResponse, ClaudeModelConfig

logger = logging.getLogger(__name__)

class ClaudeClient:
    """
    Клиент для работы с API Claude AI
    """
    def __init__(self, api_key=None, api_url=None, model=None):
        self.api_key = api_key or settings.CLAUDE_API_KEY
        self.api_url = api_url or settings.CLAUDE_API_URL.rstrip('/') + '/messages'
        self.model = model or settings.CLAUDE_MODEL
        
        self.headers = {
            'Content-Type': 'application/json',
            'x-api-key': self.api_key,
            'anthropic-version': '2023-06-01'
        }
    
    def generate_response(self, user_id: int, prompt: str, system_prompt: str = None, 
                         temperature: float = 0.7, max_tokens: int = 1000, 
                         top_p: float = 0.9) -> Tuple[str, Dict[str, Any]]:
        """
        Генерация ответа на запрос пользователя
        
        Args:
            user_id: ID пользователя
            prompt: Текст запроса
            system_prompt: Системный промпт (инструкции для модели)
            temperature: Температура (от 0 до 1)
            max_tokens: Максимальное количество токенов в ответе
            top_p: Параметр top_p (от 0 до 1)
            
        Returns:
            Tuple[str, Dict[str, Any]]: Ответ модели и метаданные запроса
        """
        start_time = time.time()
        
        # Получение модели из базы данных
        model_config = ClaudeModelConfig.objects.filter(api_id=self.model, is_active=True).first()
        
        # Создание записи о запросе
        api_request = ClaudeAPIRequest.objects.create(
            user_id=user_id,
            prompt=prompt,
            model=model_config,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            status='pending'
        )
        
        try:
            # Подготовка данных для запроса
            payload = {
                'model': self.model,
                'messages': [
                    {'role': 'user', 'content': prompt}
                ],
                'max_tokens': max_tokens,
                'temperature': temperature,
                'top_p': top_p
            }
            
            # Добавление системного промпта, если он указан
            if system_prompt:
                payload['system'] = system_prompt
            
            # Отправка запроса к API
            response = requests.post(self.api_url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            # Обработка ответа
            response_data = response.json()
            response_text = response_data.get('content', [{}])[0].get('text', '')
            
            # Обновление записи о запросе
            end_time = time.time()
            duration_ms = int((end_time - start_time) * 1000)
            
            api_request.status = 'success'
            api_request.token_count = response_data.get('usage', {}).get('input_tokens', 0)
            api_request.duration_ms = duration_ms
            api_request.save()
            
            # Создание записи об ответе
            api_response = ClaudeAPIResponse.objects.create(
                request=api_request,
                response_text=response_text,
                token_count=response_data.get('usage', {}).get('output_tokens', 0)
            )
            
            # Метаданные запроса
            metadata = {
                'request_id': api_request.id,
                'model': self.model,
                'token_count': {
                    'input': response_data.get('usage', {}).get('input_tokens', 0),
                    'output': response_data.get('usage', {}).get('output_tokens', 0),
                    'total': response_data.get('usage', {}).get('total_tokens', 0)
                },
                'duration_ms': duration_ms
            }
            
            return response_text, metadata
        except Exception as e:
            logger.error(f"Error calling Claude API: {e}")
            
            # Обновление записи о запросе в случае ошибки
            api_request.status = 'error'
            api_request.error_message = str(e)
            api_request.save()
            
            return f"Error calling Claude API: {str(e)}", {
                'request_id': api_request.id,
                'error': str(e)
            }
    
    def generate_chat_response(self, user_id: int, messages: List[Dict[str, str]], 
                              system_prompt: str = None, temperature: float = 0.7, 
                              max_tokens: int = 1000, top_p: float = 0.9) -> Tuple[str, Dict[str, Any]]:
        """
        Генерация ответа в режиме чата
        
        Args:
            user_id: ID пользователя
            messages: Список сообщений в формате [{'role': 'user|assistant', 'content': 'text'}]
            system_prompt: Системный промпт (инструкции для модели)
            temperature: Температура (от 0 до 1)
            max_tokens: Максимальное количество токенов в ответе
            top_p: Параметр top_p (от 0 до 1)
            
        Returns:
            Tuple[str, Dict[str, Any]]: Ответ модели и метаданные запроса
        """
        start_time = time.time()
        
        # Получение модели из базы данных
        model_config = ClaudeModelConfig.objects.filter(api_id=self.model, is_active=True).first()
        
        # Объединение всех сообщений в один текст для сохранения в БД
        combined_prompt = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
        
        # Создание записи о запросе
        api_request = ClaudeAPIRequest.objects.create(
            user_id=user_id,
            prompt=combined_prompt,
            model=model_config,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            status='pending'
        )
        
        try:
            # Подготовка данных для запроса
            payload = {
                'model': self.model,
                'messages': messages,
                'max_tokens': max_tokens,
                'temperature': temperature,
                'top_p': top_p
            }
            
            # Добавление системного промпта, если он указан
            if system_prompt:
                payload['system'] = system_prompt
            
            # Отправка запроса к API
            response = requests.post(self.api_url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            # Обработка ответа
            response_data = response.json()
            response_text = response_data.get('content', [{}])[0].get('text', '')
            
            # Обновление записи о запросе
            end_time = time.time()
            duration_ms = int((end_time - start_time) * 1000)
            
            api_request.status = 'success'
            api_request.token_count = response_data.get('usage', {}).get('input_tokens', 0)
            api_request.duration_ms = duration_ms
            api_request.save()
            
            # Создание записи об ответе
            api_response = ClaudeAPIResponse.objects.create(
                request=api_request,
                response_text=response_text,
                token_count=response_data.get('usage', {}).get('output_tokens', 0)
            )
            
            # Метаданные запроса
            metadata = {
                'request_id': api_request.id,
                'model': self.model,
                'token_count': {
                    'input': response_data.get('usage', {}).get('input_tokens', 0),
                    'output': response_data.get('usage', {}).get('output_tokens', 0),
                    'total': response_data.get('usage', {}).get('total_tokens', 0)
                },
                'duration_ms': duration_ms
            }
            
            return response_text, metadata
        except Exception as e:
            logger.error(f"Error calling Claude API in chat mode: {e}")
            
            # Обновление записи о запросе в случае ошибки
            api_request.status = 'error'
            api_request.error_message = str(e)
            api_request.save()
            
            return f"Error calling Claude API: {str(e)}", {
                'request_id': api_request.id,
                'error': str(e)
            }


# Инициализация клиента
_claude_client = None

def get_claude_client() -> ClaudeClient:
    """
    Получение экземпляра клиента Claude
    
    Returns:
        ClaudeClient: Экземпляр клиента
    """
    global _claude_client
    if _claude_client is None:
        _claude_client = ClaudeClient()
    return _claude_client