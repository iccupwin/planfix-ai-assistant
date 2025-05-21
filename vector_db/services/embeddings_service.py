import logging
import numpy as np
import requests
from typing import Optional, List, Dict, Any
from django.conf import settings
from ..models import VectorEntry

logger = logging.getLogger(__name__)

class EmbeddingsService:
    """
    Сервис для генерации векторных эмбеддингов с использованием API Claude AI
    """
    def __init__(self, api_key=None, api_url=None, model=None):
        self.api_key = api_key or settings.CLAUDE_API_KEY
        self.api_url = api_url or settings.CLAUDE_API_URL.rstrip('/') + '/embeddings'
        self.model = model or settings.CLAUDE_MODEL
        
        self.headers = {
            'Content-Type': 'application/json',
            'x-api-key': self.api_key,
            'anthropic-version': '2023-06-01'
        }
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Генерация векторного эмбеддинга для текста
        
        Args:
            text: Текст для векторизации
            
        Returns:
            Optional[List[float]]: Векторное представление текста или None в случае ошибки
        """
        if not text:
            logger.warning("Empty text provided for embedding generation")
            return None
        
        # Обрезаем текст до максимальной длины (8000 токенов примерно 32000 символов)
        if len(text) > 32000:
            logger.warning(f"Text too long ({len(text)} chars), truncating to 32000 chars")
            text = text[:32000]
        
        try:
            payload = {
                'model': self.model,
                'input': text,
                'encoding_format': 'float'
            }
            
            response = requests.post(self.api_url, json=payload, headers=self.headers)
            response.raise_for_status()
            
            result = response.json()
            embedding = result.get('data', [{}])[0].get('embedding')
            
            if not embedding:
                logger.error(f"Failed to get embedding: {result}")
                return None
            
            return embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None
    
    def batch_generate_embeddings(self, texts: List[str]) -> List[Optional[List[float]]]:
        """
        Генерация векторных эмбеддингов для списка текстов
        
        Args:
            texts: Список текстов для векторизации
            
        Returns:
            List[Optional[List[float]]]: Список векторных представлений текстов
        """
        return [self.generate_embedding(text) for text in texts]


# Инициализация сервиса
_embeddings_service = None

def get_embeddings_service() -> EmbeddingsService:
    """
    Получение экземпляра сервиса эмбеддингов
    
    Returns:
        EmbeddingsService: Экземпляр сервиса
    """
    global _embeddings_service
    if _embeddings_service is None:
        _embeddings_service = EmbeddingsService()
    return _embeddings_service


def generate_embeddings(text: str) -> Optional[List[float]]:
    """
    Генерация векторного эмбеддинга для текста
    
    Args:
        text: Текст для векторизации
        
    Returns:
        Optional[List[float]]: Векторное представление текста или None в случае ошибки
    """
    service = get_embeddings_service()
    return service.generate_embedding(text)


def generate_batch_embeddings(texts: List[str]) -> List[Optional[List[float]]]:
    """
    Генерация векторных эмбеддингов для списка текстов
    
    Args:
        texts: Список текстов для векторизации
        
    Returns:
        List[Optional[List[float]]]: Список векторных представлений текстов
    """
    service = get_embeddings_service()
    return service.batch_generate_embeddings(texts)


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Вычисление косинусного сходства между двумя векторами
    
    Args:
        vec1: Первый вектор
        vec2: Второй вектор
        
    Returns:
        float: Косинусное сходство (от -1 до 1)
    """
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    
    return dot_product / (norm1 * norm2)