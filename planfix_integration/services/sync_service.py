import logging
from typing import List, Dict, Any, Optional
from django.utils import timezone
from django.db import transaction
from ..models import Project, Task, Employee, Comment, Document, SyncLog
from .api_client import PlanfixApiClient
from vector_db.services.embeddings_service import generate_embeddings
from vector_db.models import VectorEntry

logger = logging.getLogger(__name__)

class PlanfixSyncService:
    """
    Сервис для синхронизации данных из Planfix
    """
    def __init__(self, api_client=None):
        self.api_client = api_client or PlanfixApiClient()
    
    def sync_all(self) -> Dict[str, Any]:
        """
        Полная синхронизация всех данных из Planfix
        
        Returns:
            Dict: Результаты синхронизации
        """
        logger.info("Starting full Planfix sync")
        
        results = {
            'projects': self.sync_projects(),
            'employees': self.sync_employees(),
            'tasks': self.sync_tasks(),
            'documents': self.sync_documents()
        }
        
        logger.info(f"Full Planfix sync completed: {results}")
        return results
    
    @transaction.atomic
    def sync_projects(self) -> Dict[str, int]:
        """
        Синхронизация проектов
        
        Returns:
            Dict: Результаты синхронизации проектов
        """
        logger.info("Starting projects sync")
        
        result = {
            'fetched': 0,
            'created': 0,
            'updated': 0,
            'error': 0
        }
        
        try:
            offset = 0
            limit = 100
            
            while True:
                projects_data = self.api_client.get_projects(offset=offset, limit=limit)
                result['fetched'] += len(projects_data)
                
                if not projects_data:
                    break
                
                for project_data in projects_data:
                    try:
                        self._process_project(project_data)
                        if Project.objects.filter(planfix_id=project_data['id']).exists():
                            result['updated'] += 1
                        else:
                            result['created'] += 1
                    except Exception as e:
                        logger.error(f"Error processing task {task_data.get('id')}: {e}")
                        SyncLog.objects.create(
                            entity_type='task',
                            entity_id=task_data.get('id'),
                            status='error',
                            message=str(e)
                        )
                        result['error'] += 1
                
                offset += limit
                
                # Если получено меньше записей, чем лимит, значит это последняя страница
                if len(tasks_data) < limit:
                    break
        
        except Exception as e:
            logger.error(f"Error syncing tasks: {e}")
            SyncLog.objects.create(
                entity_type='tasks',
                status='error',
                message=str(e)
            )
        
        logger.info(f"Tasks sync completed: {result}")
        return result
    
    def _process_task(self, task_data: Dict) -> Task:
        """
        Обработка данных задачи и сохранение в БД
        
        Args:
            task_data: Данные задачи из API
            
        Returns:
            Task: Объект задачи
        """
        # Получаем связанные объекты (проект и исполнителя)
        project = None
        if task_data.get('project', {}).get('id'):
            project = Project.objects.filter(planfix_id=task_data['project']['id']).first()
        
        assignee = None
        if task_data.get('assignee', {}).get('id'):
            assignee = Employee.objects.filter(planfix_id=task_data['assignee']['id']).first()
        
        # Создаем или обновляем задачу
        task, created = Task.objects.update_or_create(
            planfix_id=task_data['id'],
            defaults={
                'name': task_data.get('name', ''),
                'description': task_data.get('description', ''),
                'status': task_data.get('status', {}).get('name', ''),
                'priority': task_data.get('priority', {}).get('name', ''),
                'project': project,
                'assignee': assignee,
                'due_date': task_data.get('dueDate'),
                'last_sync': timezone.now()
            }
        )
        
        # Создаем векторные эмбеддинги для задачи
        task_text = f"{task.name}\n{task.description}\nStatus: {task.status}\nPriority: {task.priority}"
        metadata = {
            'planfix_id': task.planfix_id,
            'name': task.name,
            'status': task.status,
            'priority': task.priority
        }
        
        if project:
            metadata['project_id'] = project.id
            metadata['project_name'] = project.name
        
        if assignee:
            metadata['assignee_id'] = assignee.id
            metadata['assignee_name'] = assignee.name
        
        self._create_vector_entry(
            entity_id=task.id,
            entity_type='task',
            text=task_text,
            metadata=metadata
        )
        
        return task
    
    def _sync_task_comments(self, task: Task) -> Dict[str, int]:
        """
        Синхронизация комментариев к задаче
        
        Args:
            task: Объект задачи
            
        Returns:
            Dict: Результаты синхронизации комментариев
        """
        result = {
            'total': 0,
            'created': 0,
            'updated': 0,
            'error': 0
        }
        
        try:
            offset = 0
            limit = 100
            
            while True:
                comments_data = self.api_client.get_task_comments(task.planfix_id, offset=offset, limit=limit)
                result['total'] += len(comments_data)
                
                if not comments_data:
                    break
                
                for comment_data in comments_data:
                    try:
                        self._process_comment(comment_data, task)
                        if Comment.objects.filter(planfix_id=comment_data['id']).exists():
                            result['updated'] += 1
                        else:
                            result['created'] += 1
                    except Exception as e:
                        logger.error(f"Error processing comment {comment_data.get('id')}: {e}")
                        SyncLog.objects.create(
                            entity_type='comment',
                            entity_id=comment_data.get('id'),
                            status='error',
                            message=str(e)
                        )
                        result['error'] += 1
                
                offset += limit
                
                # Если получено меньше записей, чем лимит, значит это последняя страница
                if len(comments_data) < limit:
                    break
        
        except Exception as e:
            logger.error(f"Error syncing comments for task {task.planfix_id}: {e}")
            SyncLog.objects.create(
                entity_type='comments',
                entity_id=task.planfix_id,
                status='error',
                message=str(e)
            )
        
        return result
    
    def _process_comment(self, comment_data: Dict, task: Task) -> Comment:
        """
        Обработка данных комментария и сохранение в БД
        
        Args:
            comment_data: Данные комментария из API
            task: Объект задачи
            
        Returns:
            Comment: Объект комментария
        """
        # Получаем автора комментария
        author = None
        if comment_data.get('author', {}).get('id'):
            author = Employee.objects.filter(planfix_id=comment_data['author']['id']).first()
        
        # Создаем или обновляем комментарий
        comment, created = Comment.objects.update_or_create(
            planfix_id=comment_data['id'],
            defaults={
                'name': f"Comment {comment_data['id']}",  # Комментарии обычно не имеют имени
                'text': comment_data.get('text', ''),
                'task': task,
                'author': author,
                'last_sync': timezone.now()
            }
        )
        
        # Создаем векторные эмбеддинги для комментария
        comment_text = comment.text
        metadata = {
            'planfix_id': comment.planfix_id,
            'task_id': task.id,
            'task_name': task.name,
            'task_planfix_id': task.planfix_id
        }
        
        if author:
            metadata['author_id'] = author.id
            metadata['author_name'] = author.name
        
        self._create_vector_entry(
            entity_id=comment.id,
            entity_type='comment',
            text=comment_text,
            metadata=metadata
        )
        
        return comment
    
    @transaction.atomic
    def sync_documents(self) -> Dict[str, int]:
        """
        Синхронизация документов
        
        Returns:
            Dict: Результаты синхронизации документов
        """
        logger.info("Starting documents sync")
        
        result = {
            'fetched': 0,
            'created': 0,
            'updated': 0,
            'content_synced': 0,
            'error': 0
        }
        
        try:
            offset = 0
            limit = 100
            
            while True:
                documents_data = self.api_client.get_documents(offset=offset, limit=limit)
                result['fetched'] += len(documents_data)
                
                if not documents_data:
                    break
                
                for document_data in documents_data:
                    try:
                        document = self._process_document(document_data)
                        
                        # Если документ поддерживает извлечение содержимого, синхронизируем его
                        if document.file_type in ['txt', 'doc', 'docx', 'pdf']:
                            try:
                                document_content = self.api_client.get_document_content(document.planfix_id)
                                document.content = document_content
                                document.save()
                                result['content_synced'] += 1
                                
                                # Создаем векторные эмбеддинги для содержимого документа
                                if document.content:
                                    self._create_vector_entry(
                                        entity_id=document.id,
                                        entity_type='document_content',
                                        text=document.content,
                                        metadata={
                                            'planfix_id': document.planfix_id,
                                            'name': document.name,
                                            'file_type': document.file_type,
                                            'document_id': document.id
                                        }
                                    )
                            except Exception as e:
                                logger.error(f"Error syncing content for document {document.planfix_id}: {e}")
                                SyncLog.objects.create(
                                    entity_type='document_content',
                                    entity_id=document.planfix_id,
                                    status='error',
                                    message=str(e)
                                )
                        
                        if Document.objects.filter(planfix_id=document_data['id']).exists():
                            result['updated'] += 1
                        else:
                            result['created'] += 1
                    except Exception as e:
                        logger.error(f"Error processing document {document_data.get('id')}: {e}")
                        SyncLog.objects.create(
                            entity_type='document',
                            entity_id=document_data.get('id'),
                            status='error',
                            message=str(e)
                        )
                        result['error'] += 1
                
                offset += limit
                
                # Если получено меньше записей, чем лимит, значит это последняя страница
                if len(documents_data) < limit:
                    break
        
        except Exception as e:
            logger.error(f"Error syncing documents: {e}")
            SyncLog.objects.create(
                entity_type='documents',
                status='error',
                message=str(e)
            )
        
        logger.info(f"Documents sync completed: {result}")
        return result
    
    def _process_document(self, document_data: Dict) -> Document:
        """
        Обработка данных документа и сохранение в БД
        
        Args:
            document_data: Данные документа из API
            
        Returns:
            Document: Объект документа
        """
        # Получаем связанный проект
        project = None
        if document_data.get('project', {}).get('id'):
            project = Project.objects.filter(planfix_id=document_data['project']['id']).first()
        
        # Определяем тип файла
        file_name = document_data.get('name', '')
        file_type = file_name.split('.')[-1].lower() if '.' in file_name else ''
        
        # Создаем или обновляем документ
        document, created = Document.objects.update_or_create(
            planfix_id=document_data['id'],
            defaults={
                'name': file_name,
                'description': document_data.get('description', ''),
                'file_url': document_data.get('url', ''),
                'file_type': file_type,
                'project': project,
                'last_sync': timezone.now()
            }
        )
        
        # Создаем векторные эмбеддинги для метаданных документа
        document_text = f"{document.name}\n{document.description}"
        metadata = {
            'planfix_id': document.planfix_id,
            'name': document.name,
            'file_type': document.file_type
        }
        
        if project:
            metadata['project_id'] = project.id
            metadata['project_name'] = project.name
        
        self._create_vector_entry(
            entity_id=document.id,
            entity_type='document',
            text=document_text,
            metadata=metadata
        )
        
        return document
    
    def _create_vector_entry(self, entity_id: int, entity_type: str, text: str, metadata: Dict) -> Optional[VectorEntry]:
        """
        Создание векторной записи для текста
        
        Args:
            entity_id: ID сущности
            entity_type: Тип сущности
            text: Текст для векторизации
            metadata: Метаданные
            
        Returns:
            Optional[VectorEntry]: Созданная векторная запись или None в случае ошибки
        """
        try:
            if not text:
                return None
            
            # Генерация эмбеддингов
            embedding = generate_embeddings(text)
            
            if embedding is None:
                logger.error(f"Failed to generate embeddings for {entity_type} {entity_id}")
                return None
            
            # Создаем или обновляем векторную запись
            vector_entry, created = VectorEntry.objects.update_or_create(
                entity_type=entity_type,
                entity_id=entity_id,
                defaults={
                    'text': text,
                    'embedding': embedding,
                    'metadata': metadata
                }
            )
            
            return vector_entry
        except Exception as e:
            logger.error(f"Error creating vector entry for {entity_type} {entity_id}: {e}")
            return None project {project_data.get('id')}: {e}")
                        SyncLog.objects.create(
                            entity_type='project',
                            entity_id=project_data.get('id'),
                            status='error',
                            message=str(e)
                        )
                        result['error'] += 1
                
                offset += limit
                
                # Если получено меньше записей, чем лимит, значит это последняя страница
                if len(projects_data) < limit:
                    break
        
        except Exception as e:
            logger.error(f"Error syncing projects: {e}")
            SyncLog.objects.create(
                entity_type='projects',
                status='error',
                message=str(e)
            )
        
        logger.info(f"Projects sync completed: {result}")
        return result
    
    def _process_project(self, project_data: Dict) -> Project:
        """
        Обработка данных проекта и сохранение в БД
        
        Args:
            project_data: Данные проекта из API
            
        Returns:
            Project: Объект проекта
        """
        project, created = Project.objects.update_or_create(
            planfix_id=project_data['id'],
            defaults={
                'name': project_data.get('name', ''),
                'description': project_data.get('description', ''),
                'status': project_data.get('status', {}).get('name', ''),
                'last_sync': timezone.now()
            }
        )
        
        # Создаем векторные эмбеддинги для проекта
        project_text = f"{project.name}\n{project.description}"
        self._create_vector_entry(
            entity_id=project.id,
            entity_type='project',
            text=project_text,
            metadata={
                'planfix_id': project.planfix_id,
                'name': project.name,
                'status': project.status
            }
        )
        
        return project
    
    @transaction.atomic
    def sync_employees(self) -> Dict[str, int]:
        """
        Синхронизация сотрудников
        
        Returns:
            Dict: Результаты синхронизации сотрудников
        """
        logger.info("Starting employees sync")
        
        result = {
            'fetched': 0,
            'created': 0,
            'updated': 0,
            'error': 0
        }
        
        try:
            offset = 0
            limit = 100
            
            while True:
                employees_data = self.api_client.get_employees(offset=offset, limit=limit)
                result['fetched'] += len(employees_data)
                
                if not employees_data:
                    break
                
                for employee_data in employees_data:
                    try:
                        self._process_employee(employee_data)
                        if Employee.objects.filter(planfix_id=employee_data['id']).exists():
                            result['updated'] += 1
                        else:
                            result['created'] += 1
                    except Exception as e:
                        logger.error(f"Error processing employee {employee_data.get('id')}: {e}")
                        SyncLog.objects.create(
                            entity_type='employee',
                            entity_id=employee_data.get('id'),
                            status='error',
                            message=str(e)
                        )
                        result['error'] += 1
                
                offset += limit
                
                # Если получено меньше записей, чем лимит, значит это последняя страница
                if len(employees_data) < limit:
                    break
        
        except Exception as e:
            logger.error(f"Error syncing employees: {e}")
            SyncLog.objects.create(
                entity_type='employees',
                status='error',
                message=str(e)
            )
        
        logger.info(f"Employees sync completed: {result}")
        return result
    
    def _process_employee(self, employee_data: Dict) -> Employee:
        """
        Обработка данных сотрудника и сохранение в БД
        
        Args:
            employee_data: Данные сотрудника из API
            
        Returns:
            Employee: Объект сотрудника
        """
        employee, created = Employee.objects.update_or_create(
            planfix_id=employee_data['id'],
            defaults={
                'name': f"{employee_data.get('firstName', '')} {employee_data.get('lastName', '')}",
                'email': employee_data.get('email', ''),
                'position': employee_data.get('position', {}).get('name', ''),
                'last_sync': timezone.now()
            }
        )
        
        # Создаем векторные эмбеддинги для сотрудника
        employee_text = f"{employee.name}\n{employee.position}\n{employee.email}"
        self._create_vector_entry(
            entity_id=employee.id,
            entity_type='employee',
            text=employee_text,
            metadata={
                'planfix_id': employee.planfix_id,
                'name': employee.name,
                'position': employee.position,
                'email': employee.email
            }
        )
        
        return employee
    
    @transaction.atomic
    def sync_tasks(self) -> Dict[str, int]:
        """
        Синхронизация задач
        
        Returns:
            Dict: Результаты синхронизации задач
        """
        logger.info("Starting tasks sync")
        
        result = {
            'fetched': 0,
            'created': 0,
            'updated': 0,
            'comments_synced': 0,
            'error': 0
        }
        
        try:
            offset = 0
            limit = 100
            
            while True:
                tasks_data = self.api_client.get_tasks(offset=offset, limit=limit)
                result['fetched'] += len(tasks_data)
                
                if not tasks_data:
                    break
                
                for task_data in tasks_data:
                    try:
                        task = self._process_task(task_data)
                        if Task.objects.filter(planfix_id=task_data['id']).exists():
                            result['updated'] += 1
                        else:
                            result['created'] += 1
                        
                        # Синхронизация комментариев к задаче
                        comments_result = self._sync_task_comments(task)
                        result['comments_synced'] += comments_result.get('total', 0)
                    except Exception as e:
                        logger.error(f"Error processing