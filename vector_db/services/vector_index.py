import os
import logging
import numpy as np
import faiss
import json
from typing import List, Dict, Any, Optional, Tuple
from django.conf import settings
from django.utils import timezone
from ..models import VectorEntry, VectorIndex, SearchLog
from .embeddings_service import generate_embeddings

logger = logging.getLogger(__name__)

class VectorIndexService:
    """
    Сервис для работы с векторными индексами с использованием FAISS
    """
    def __init__(self, index_name='default', dimension=None):
        self.index_name = index_name
        self.dimension = dimension or settings.VECTOR_DIMENSION
        self.index = None
        self.id_to_entry_map = {}
        
        # Попытка загрузить существующий индекс
        self._load_or_create_index()
    
    def _load_or_create_index(self) -> None:
        """
        Загрузка существующего или создание нового индекса
        """
        try:
            # Попытка получить информацию об индексе из БД
            vector_index, created = VectorIndex.objects.get_or_create(
                name=self.index_name,
                defaults={
                    'index_type': 'faiss',
                    'dimension': self.dimension,
                    'entity_types': [],
                    'config': {'metric': 'cosine'},
                    'is_active': True
                }
            )
            
            # Обновляем размерность, если она была изменена
            if vector_index.dimension != self.dimension:
                vector_index.dimension = self.dimension
                vector_index.save()
            
            # Путь к файлу индекса
            index_file = f"index_{self.index_name}.faiss"
            index_path = os.path.join(settings.BASE_DIR, 'vector_indices', index_file)
            
            # Проверка наличия директории
            index_dir = os.path.dirname(index_path)
            if not os.path.exists(index_dir):
                os.makedirs(index_dir)
            
            # Проверка наличия файла индекса
            if os.path.exists(index_path):
                # Загрузка существующего индекса
                self.index = faiss.read_index(index_path)
                logger.info(f"Loaded existing FAISS index from {index_path}")
                
                # Загрузка маппинга ID к записям
                self._load_id_mapping()
            else:
                # Создание нового индекса
                self.index = faiss.IndexFlatIP(self.dimension)  # Cosine similarity using IP (inner product)
                logger.info("Created new FAISS index")
                
                # Добавление всех существующих векторных записей в индекс
                self._rebuild_index()
        except Exception as e:
            logger.error(f"Error loading/creating FAISS index: {e}")
            # Создание резервного индекса в памяти
            self.index = faiss.IndexFlatIP(self.dimension)
    
    def _load_id_mapping(self) -> None:
        """
        Загрузка маппинга идентификаторов к записям
        """
        try:
            entries = VectorEntry.objects.all()
            for i, entry in enumerate(entries):
                self.id_to_entry_map[i] = entry.id
            logger.info(f"Loaded {len(self.id_to_entry_map)} entries to ID mapping")
        except Exception as e:
            logger.error(f"Error loading ID mapping: {e}")
            self.id_to_entry_map = {}
    
    def _rebuild_index(self) -> None:
        """
        Перестроение индекса с использованием всех существующих векторных записей
        """
        try:
            entries = VectorEntry.objects.all()
            if not entries:
                logger.info("No vector entries found for rebuilding index")
                return
            
            # Сбор векторов
            vectors = []
            self.id_to_entry_map = {}
            
            for i, entry in enumerate(entries):
                vectors.append(np.array(entry.embedding, dtype=np.float32))
                self.id_to_entry_map[i] = entry.id
            
            if vectors:
                # Объединение векторов в массив
                vectors_array = np.vstack(vectors).astype(np.float32)
                
                # Нормализация векторов для косинусного сходства
                faiss.normalize_L2(vectors_array)
                
                # Добавление векторов в индекс
                self.index = faiss.IndexFlatIP(self.dimension)
                self.index.add(vectors_array)
                
                # Сохранение индекса
                self._save_index()
                
                logger.info(f"Rebuilt index with {len(vectors)} vectors")
            else:
                logger.warning("No valid vectors found for rebuilding index")
        except Exception as e:
            logger.error(f"Error rebuilding index: {e}")
    
    def _save_index(self) -> None:
        """
        Сохранение индекса на диск
        """
        try:
            index_file = f"index_{self.index_name}.faiss"
            index_path = os.path.join(settings.BASE_DIR, 'vector_indices', index_file)
            
            # Проверка наличия директории
            index_dir = os.path.dirname(index_path)
            if not os.path.exists(index_dir):
                os.makedirs(index_dir)
            
            faiss.write_index(self.index, index_path)
            
            # Обновление записи индекса в БД
            VectorIndex.objects.filter(name=self.index_name).update(
                last_updated=timezone.now()
            )
            
            logger.info(f"Saved FAISS index to {index_path}")
        except Exception as e:
            logger.error(f"Error saving FAISS index: {e}")
    
    def add_vector(self, entry: VectorEntry) -> bool:
        """
        Добавление нового вектора в индекс
        
        Args:
            entry: Векторная запись
            
        Returns:
            bool: Успешно ли добавлен вектор
        """
        try:
            # Преобразование эмбеддинга в numpy массив
            vector = np.array([entry.embedding], dtype=np.float32)
            
            # Нормализация вектора для косинусного сходства
            faiss.normalize_L2(vector)
            
            # Добавление вектора в индекс
            self.index.add(vector)
            
            # Обновление маппинга
            idx = self.index.ntotal - 1
            self.id_to_entry_map[idx] = entry.id
            
            # Сохранение индекса
            self._save_index()
            
            return True
        except Exception as e:
            logger.error(f"Error adding vector to index: {e}")
            return False
    
    def remove_vector(self, entry_id: int) -> bool:
        """
        Удаление вектора из индекса
        
        Args:
            entry_id: ID векторной записи
            
        Returns:
            bool: Успешно ли удален вектор
        """
        try:
            # Поиск индекса в маппинге
            idx_to_remove = None
            for idx, entry_id_mapped in self.id_to_entry_map.items():
                if entry_id_mapped == entry_id:
                    idx_to_remove = idx
                    break
            
            if idx_to_remove is not None:
                # FAISS не поддерживает прямое удаление, поэтому нужно перестроить индекс
                del self.id_to_entry_map[idx_to_remove]
                
                # Перестроение индекса
                self._rebuild_index()
                
                return True
            else:
                logger.warning(f"Vector entry with ID {entry_id} not found in mapping")
                return False
        except Exception as e:
            logger.error(f"Error removing vector from index: {e}")
            return False
    
    def update_vector(self, entry: VectorEntry) -> bool:
        """
        Обновление вектора в индексе
        
        Args:
            entry: Обновленная векторная запись
            
        Returns:
            bool: Успешно ли обновлен вектор
        """
        # Удаление старого вектора и добавление нового
        if self.remove_vector(entry.id):
            return self.add_vector(entry)
        return False
    
    def search(self, query: str, top_k: int = 10, filter_criteria: Dict = None) -> List[Dict]:
        """
        Поиск по индексу с использованием текстового запроса
        
        Args:
            query: Текстовый запрос
            top_k: Количество результатов
            filter_criteria: Критерии фильтрации результатов
            
        Returns:
            List[Dict]: Список результатов поиска
        """
        start_time = timezone.now()
        
        try:
            # Генерация вектора для запроса
            query_vector = generate_embeddings(query)
            
            if query_vector is None:
                logger.error("Failed to generate embedding for query")
                return []
            
            # Преобразование в numpy массив
            query_vector_np = np.array([query_vector], dtype=np.float32)
            
            # Нормализация вектора для косинусного сходства
            faiss.normalize_L2(query_vector_np)
            
            # Поиск ближайших векторов
            scores, indices = self.index.search(query_vector_np, top_k * 3)  # Запрашиваем больше, чтобы после фильтрации осталось достаточно
            
            # Преобразование результатов
            results = []
            
            for i in range(len(indices[0])):
                idx = indices[0][i]
                score = float(scores[0][i])
                
                if idx != -1 and idx in self.id_to_entry_map:
                    entry_id = self.id_to_entry_map[idx]
                    
                    try:
                        entry = VectorEntry.objects.get(id=entry_id)
                        
                        # Применение фильтров
                        if filter_criteria and not self._apply_filters(entry, filter_criteria):
                            continue
                        
                        results.append({
                            'id': entry.id,
                            'entity_type': entry.entity_type,
                            'entity_id': entry.entity_id,
                            'text': entry.text,
                            'metadata': entry.metadata,
                            'score': score
                        })
                    except VectorEntry.DoesNotExist:
                        logger.warning(f"Vector entry with ID {entry_id} not found in database")
            
            # Обрезание до запрошенного количества
            results = results[:top_k]
            
            # Логирование поиска
            end_time = timezone.now()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            SearchLog.objects.create(
                query=query,
                results_count=len(results),
                duration_ms=duration_ms
            )
            
            return results
        except Exception as e:
            logger.error(f"Error searching in index: {e}")
            
            # Логирование ошибки
            end_time = timezone.now()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            SearchLog.objects.create(
                query=query,
                results_count=0,
                duration_ms=duration_ms
            )
            
            return []
    
    def _apply_filters(self, entry: VectorEntry, filter_criteria: Dict) -> bool:
        """
        Применение фильтров к результатам поиска
        
        Args:
            entry: Векторная запись
            filter_criteria: Критерии фильтрации
            
        Returns:
            bool: Соответствует ли запись критериям
        """
        # Фильтрация по типу сущности
        if 'entity_types' in filter_criteria and filter_criteria['entity_types']:
            if entry.entity_type not in filter_criteria['entity_types']:
                return False
        
        # Фильтрация по метаданным
        if 'metadata' in filter_criteria and filter_criteria['metadata']:
            for key, value in filter_criteria['metadata'].items():
                if key not in entry.metadata or entry.metadata[key] != value:
                    return False
        
        return True


# Инициализация сервиса
_vector_index_service = None

def get_vector_index_service() -> VectorIndexService:
    """
    Получение экземпляра сервиса векторного индекса
    
    Returns:
        VectorIndexService: Экземпляр сервиса
    """
    global _vector_index_service
    if _vector_index_service is None:
        _vector_index_service = VectorIndexService()
    return _vector_index_service