import json
import logging
import requests
from typing import Dict, List, Any, Optional
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

class PlanfixApiClient:
    """
    Клиент для работы с Planfix API
    """
    def __init__(self, api_key=None, account_id=None, user_id=None, user_password=None):
        self.api_url = settings.PLANFIX_API_URL
        self.api_key = api_key or settings.PLANFIX_API_KEY
        self.account_id = account_id or settings.PLANFIX_ACCOUNT_ID
        self.user_id = user_id or settings.PLANFIX_USER_ID
        self.user_password = user_password or settings.PLANFIX_USER_PASSWORD
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }
    
    def _make_request(self, endpoint: str, method: str = 'GET', data: Dict = None) -> Dict:
        """
        Выполнение запроса к API
        
        Args:
            endpoint: Конечная точка API
            method: HTTP метод
            data: Данные для отправки
            
        Returns:
            Dict: Ответ от API
        """
        url = f"{self.api_url}{endpoint}"
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=self.headers, params=data)
            elif method == 'POST':
                response = requests.post(url, headers=self.headers, json=data)
            elif method == 'PUT':
                response = requests.put(url, headers=self.headers, json=data)
            elif method == 'DELETE':
                response = requests.delete(url, headers=self.headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
                
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error making request to Planfix API: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response status code: {e.response.status_code}")
                logger.error(f"Response body: {e.response.text}")
            raise
    
    def get_projects(self, offset: int = 0, limit: int = 100) -> List[Dict]:
        """
        Получение списка проектов
        
        Args:
            offset: Смещение
            limit: Лимит записей
            
        Returns:
            List[Dict]: Список проектов
        """
        endpoint = "projects"
        data = {
            "offset": offset,
            "limit": limit
        }
        
        response = self._make_request(endpoint, data=data)
        return response.get('projects', [])
    
    def get_project(self, project_id: str) -> Dict:
        """
        Получение информации о проекте
        
        Args:
            project_id: ID проекта
            
        Returns:
            Dict: Информация о проекте
        """
        endpoint = f"projects/{project_id}"
        return self._make_request(endpoint)
    
    def get_tasks(self, project_id: Optional[str] = None, offset: int = 0, limit: int = 100) -> List[Dict]:
        """
        Получение списка задач
        
        Args:
            project_id: ID проекта (опционально)
            offset: Смещение
            limit: Лимит записей
            
        Returns:
            List[Dict]: Список задач
        """
        endpoint = "tasks"
        data = {
            "offset": offset,
            "limit": limit
        }
        
        if project_id:
            data["project"] = project_id
        
        response = self._make_request(endpoint, data=data)
        return response.get('tasks', [])
    
    def get_task(self, task_id: str) -> Dict:
        """
        Получение информации о задаче
        
        Args:
            task_id: ID задачи
            
        Returns:
            Dict: Информация о задаче
        """
        endpoint = f"tasks/{task_id}"
        return self._make_request(endpoint)
    
    def get_task_comments(self, task_id: str, offset: int = 0, limit: int = 100) -> List[Dict]:
        """
        Получение комментариев к задаче
        
        Args:
            task_id: ID задачи
            offset: Смещение
            limit: Лимит записей
            
        Returns:
            List[Dict]: Список комментариев
        """
        endpoint = f"tasks/{task_id}/comments"
        data = {
            "offset": offset,
            "limit": limit
        }
        
        response = self._make_request(endpoint, data=data)
        return response.get('comments', [])
    
    def get_employees(self, offset: int = 0, limit: int = 100) -> List[Dict]:
        """
        Получение списка сотрудников
        
        Args:
            offset: Смещение
            limit: Лимит записей
            
        Returns:
            List[Dict]: Список сотрудников
        """
        endpoint = "users"
        data = {
            "offset": offset,
            "limit": limit
        }
        
        response = self._make_request(endpoint, data=data)
        return response.get('users', [])
    
    def get_employee(self, employee_id: str) -> Dict:
        """
        Получение информации о сотруднике
        
        Args:
            employee_id: ID сотрудника
            
        Returns:
            Dict: Информация о сотруднике
        """
        endpoint = f"users/{employee_id}"
        return self._make_request(endpoint)
    
    def get_documents(self, project_id: Optional[str] = None, offset: int = 0, limit: int = 100) -> List[Dict]:
        """
        Получение списка документов
        
        Args:
            project_id: ID проекта (опционально)
            offset: Смещение
            limit: Лимит записей
            
        Returns:
            List[Dict]: Список документов
        """
        endpoint = "files"
        data = {
            "offset": offset,
            "limit": limit
        }
        
        if project_id:
            data["project"] = project_id
        
        response = self._make_request(endpoint, data=data)
        return response.get('files', [])
    
    def get_document_content(self, document_id: str) -> str:
        """
        Получение содержимого документа
        
        Args:
            document_id: ID документа
            
        Returns:
            str: Содержимое документа
        """
        endpoint = f"files/{document_id}/content"
        return self._make_request(endpoint).get('content', '')