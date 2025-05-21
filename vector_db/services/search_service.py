import logging
from typing import List, Dict, Any, Optional
from django.db.models import Q
from django.utils import timezone
from django.db import connection
from ..models import VectorEntry, SearchLog
from .vector_index import get_vector_index_service
from planfix_integration.models import Project, Task, Employee, Comment, Document

logger = logging.getLogger(__name__)

class SearchService:
    """
    Сервис для семантического поиска по данным из Planfix
    """
    def __init__(self):
        self.vector_index = get_vector_index_service()
    
    def search(self, query: str, top_k: int = 10, entity_types: List[str] = None, 
               metadata_filters: Dict = None) -> Dict[str, Any]:
        """
        Выполнение семантического поиска по данным
        
        Args:
            query: Поисковый запрос
            top_k: Количество результатов
            entity_types: Список типов сущностей для поиска
            metadata_filters: Фильтры по метаданным
            
        Returns:
            Dict: Результаты поиска с группировкой по типам
        """
        start_time = timezone.now()
        
        try:
            # Подготовка фильтров
            filter_criteria = {}
            if entity_types:
                filter_criteria['entity_types'] = entity_types
            if metadata_filters:
                filter_criteria['metadata'] = metadata_filters
            
            # Выполнение поиска
            vector_results = self.vector_index.search(query, top_k=top_k, filter_criteria=filter_criteria)
            
            # Группировка результатов по типам
            grouped_results = self._group_results_by_type(vector_results)
            
            # Обогащение результатов данными из моделей
            enriched_results = self._enrich_results(grouped_results)
            
            # Логирование поиска
            end_time = timezone.now()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            SearchLog.objects.create(
                query=query,
                results_count=len(vector_results),
                duration_ms=duration_ms
            )
            
            return {
                'query': query,
                'total_results': len(vector_results),
                'duration_ms': duration_ms,
                'results': enriched_results
            }
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            
            # Логирование ошибки
            end_time = timezone.now()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            SearchLog.objects.create(
                query=query,
                results_count=0,
                duration_ms=duration_ms
            )
            
            return {
                'query': query,
                'error': str(e),
                'total_results': 0,
                'duration_ms': duration_ms,
                'results': {}
            }
    
    def _group_results_by_type(self, results: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Группировка результатов поиска по типам сущностей
        
        Args:
            results: Результаты поиска
            
        Returns:
            Dict: Сгруппированные результаты
        """
        grouped = {}
        
        for result in results:
            entity_type = result['entity_type']
            if entity_type not in grouped:
                grouped[entity_type] = []
            
            grouped[entity_type].append(result)
        
        return grouped
    
    def _enrich_results(self, grouped_results: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
        """
        Обогащение результатов поиска данными из соответствующих моделей
        
        Args:
            grouped_results: Сгруппированные результаты поиска
            
        Returns:
            Dict: Обогащенные результаты
        """
        enriched = {}
        
        # Обогащение для проектов
        if 'project' in grouped_results:
            project_ids = [result['entity_id'] for result in grouped_results['project']]
            projects = {p.id: p for p in Project.objects.filter(id__in=project_ids)}
            
            enriched_projects = []
            for result in grouped_results['project']:
                project_id = result['entity_id']
                if project_id in projects:
                    result['project'] = {
                        'id': projects[project_id].id,
                        'planfix_id': projects[project_id].planfix_id,
                        'name': projects[project_id].name,
                        'description': projects[project_id].description,
                        'status': projects[project_id].status
                    }
                enriched_projects.append(result)
            
            enriched['project'] = enriched_projects
        
        # Обогащение для задач
        if 'task' in grouped_results:
            task_ids = [result['entity_id'] for result in grouped_results['task']]
            tasks = {t.id: t for t in Task.objects.filter(id__in=task_ids)}
            
            enriched_tasks = []
            for result in grouped_results['task']:
                task_id = result['entity_id']
                if task_id in tasks:
                    task = tasks[task_id]
                    task_data = {
                        'id': task.id,
                        'planfix_id': task.planfix_id,
                        'name': task.name,
                        'description': task.description,
                        'status': task.status,
                        'priority': task.priority,
                        'due_date': task.due_date.isoformat() if task.due_date else None
                    }
                    
                    if task.project:
                        task_data['project'] = {
                            'id': task.project.id,
                            'planfix_id': task.project.planfix_id,
                            'name': task.project.name
                        }
                    
                    if task.assignee:
                        task_data['assignee'] = {
                            'id': task.assignee.id,
                            'planfix_id': task.assignee.planfix_id,
                            'name': task.assignee.name
                        }
                    
                    result['task'] = task_data
                enriched_tasks.append(result)
            
            enriched['task'] = enriched_tasks
        
        # Обогащение для сотрудников
        if 'employee' in grouped_results:
            employee_ids = [result['entity_id'] for result in grouped_results['employee']]
            employees = {e.id: e for e in Employee.objects.filter(id__in=employee_ids)}
            
            enriched_employees = []
            for result in grouped_results['employee']:
                employee_id = result['entity_id']
                if employee_id in employees:
                    result['employee'] = {
                        'id': employees[employee_id].id,
                        'planfix_id': employees[employee_id].planfix_id,
                        'name': employees[employee_id].name,
                        'email': employees[employee_id].email,
                        'position': employees[employee_id].position
                    }
                enriched_employees.append(result)
            
            enriched['employee'] = enriched_employees
        
        # Обогащение для комментариев
        if 'comment' in grouped_results:
            comment_ids = [result['entity_id'] for result in grouped_results['comment']]
            comments = {c.id: c for c in Comment.objects.filter(id__in=comment_ids)}
            
            enriched_comments = []
            for result in grouped_results['comment']:
                comment_id = result['entity_id']
                if comment_id in comments:
                    comment = comments[comment_id]
                    comment_data = {
                        'id': comment.id,
                        'planfix_id': comment.planfix_id,
                        'text': comment.text
                    }
                    
                    if comment.task:
                        comment_data['task'] = {
                            'id': comment.task.id,
                            'planfix_id': comment.task.planfix_id,
                            'name': comment.task.name
                        }
                    
                    if comment.author:
                        comment_data['author'] = {
                            'id': comment.author.id,
                            'planfix_id': comment.author.planfix_id,
                            'name': comment.author.name
                        }
                    
                    result['comment'] = comment_data
                enriched_comments.append(result)
            
            enriched['comment'] = enriched_comments
        
        # Обогащение для документов
        if 'document' in grouped_results:
            document_ids = [result['entity_id'] for result in grouped_results['document']]
            documents = {d.id: d for d in Document.objects.filter(id__in=document_ids)}
            
            enriched_documents = []
            for result in grouped_results['document']:
                document_id = result['entity_id']
                if document_id in documents:
                    document = documents[document_id]
                    document_data = {
                        'id': document.id,
                        'planfix_id': document.planfix_id,
                        'name': document.name,
                        'description': document.description,
                        'file_url': document.file_url,
                        'file_type': document.file_type
                    }
                    
                    if document.project:
                        document_data['project'] = {
                            'id': document.project.id,
                            'planfix_id': document.project.planfix_id,
                            'name': document.project.name
                        }
                    
                    result['document'] = document_data
                enriched_documents.append(result)
            
            enriched['document'] = enriched_documents
        
        # Обогащение для содержимого документов
        if 'document_content' in grouped_results:
            document_ids = [result['entity_id'] for result in grouped_results['document_content']]
            documents = {d.id: d for d in Document.objects.filter(id__in=document_ids)}
            
            enriched_document_contents = []
            for result in grouped_results['document_content']:
                document_id = result['entity_id']
                if document_id in documents:
                    document = documents[document_id]
                    document_data = {
                        'id': document.id,
                        'planfix_id': document.planfix_id,
                        'name': document.name,
                        'description': document.description,
                        'file_url': document.file_url,
                        'file_type': document.file_type,
                        'content_preview': document.content[:500] + '...' if document.content and len(document.content) > 500 else document.content
                    }
                    
                    if document.project:
                        document_data['project'] = {
                            'id': document.project.id,
                            'planfix_id': document.project.planfix_id,
                            'name': document.project.name
                        }
                    
                    result['document_content'] = document_data
                enriched_document_contents.append(result)
            
            enriched['document_content'] = enriched_document_contents
        
        return enriched
    
    def search_by_keywords(self, keywords: str, entity_types: List[str] = None) -> Dict[str, Any]:
        """
        Поиск по ключевым словам с использованием полнотекстового поиска
        
        Args:
            keywords: Ключевые слова для поиска
            entity_types: Список типов сущностей для поиска
            
        Returns:
            Dict: Результаты поиска
        """
        start_time = timezone.now()
        
        try:
            # Построение запроса
            query = Q()
            for keyword in keywords.split():
                query |= Q(text__icontains=keyword)
            
            # Фильтрация по типам сущностей
            if entity_types:
                entity_type_query = Q()
                for entity_type in entity_types:
                    entity_type_query |= Q(entity_type=entity_type)
                query &= entity_type_query
            
            # Выполнение поиска
            results = VectorEntry.objects.filter(query)
            
            # Преобразование результатов
            vector_results = []
            for entry in results:
                vector_results.append({
                    'id': entry.id,
                    'entity_type': entry.entity_type,
                    'entity_id': entry.entity_id,
                    'text': entry.text,
                    'metadata': entry.metadata,
                    'score': 1.0  # Нет оценки релевантности для полнотекстового поиска
                })
            
            # Группировка и обогащение результатов
            grouped_results = self._group_results_by_type(vector_results)
            enriched_results = self._enrich_results(grouped_results)
            
            # Логирование поиска
            end_time = timezone.now()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            SearchLog.objects.create(
                query=f"keywords:{keywords}",
                results_count=len(vector_results),
                duration_ms=duration_ms
            )
            
            return {
                'query': keywords,
                'total_results': len(vector_results),
                'duration_ms': duration_ms,
                'results': enriched_results
            }
        except Exception as e:
            logger.error(f"Error in keyword search: {e}")
            
            # Логирование ошибки
            end_time = timezone.now()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            SearchLog.objects.create(
                query=f"keywords:{keywords}",
                results_count=0,
                duration_ms=duration_ms
            )
            
            return {
                'query': keywords,
                'error': str(e),
                'total_results': 0,
                'duration_ms': duration_ms,
                'results': {}
            }


# Инициализация сервиса
_search_service = None

def get_search_service() -> SearchService:
    """
    Получение экземпляра сервиса поиска
    
    Returns:
        SearchService: Экземпляр сервиса
    """
    global _search_service
    if _search_service is None:
        _search_service = SearchService()
    return _search_service