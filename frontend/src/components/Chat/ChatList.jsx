// frontend/src/components/Chat/ChatList.jsx
import React, { useState, useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import { PlusIcon, TrashIcon } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { ru } from 'date-fns/locale';
import api from '../../services/api';

const ChatList = () => {
  const [chats, setChats] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchChats = async () => {
      try {
        setLoading(true);
        const response = await api.get('/api/chat/');
        setChats(response.data);
        setLoading(false);
      } catch (error) {
        console.error('Error fetching chats:', error);
        setError('Не удалось загрузить список чатов');
        setLoading(false);
      }
    };

    fetchChats();
  }, []);

  const createNewChat = async () => {
    try {
      const response = await api.post('/api/chat/');
      setChats([response.data, ...chats]);
      return response.data.id;
    } catch (error) {
      console.error('Error creating chat:', error);
      setError('Не удалось создать новый чат');
      return null;
    }
  };

  const deleteChat = async (chatId, e) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (window.confirm('Вы уверены, что хотите удалить этот чат?')) {
      try {
        await api.delete(`/api/chat/${chatId}/`);
        setChats(chats.filter(chat => chat.id !== chatId));
      } catch (error) {
        console.error('Error deleting chat:', error);
        setError('Не удалось удалить чат');
      }
    }
  };

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="animate-pulse text-gray-400">Загрузка чатов...</div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <button
          onClick={createNewChat}
          className="w-full py-2 px-4 bg-indigo-600 hover:bg-indigo-700 text-white rounded-md flex items-center justify-center"
        >
          <PlusIcon className="w-4 h-4 mr-2" />
          Новый чат
        </button>
        {error && <div className="mt-2 text-sm text-red-500">{error}</div>}
      </div>
      
      <div className="flex-1 overflow-auto">
        {chats.length === 0 ? (
          <div className="p-4 text-center text-gray-500">
            У вас пока нет чатов. Создайте новый чат, чтобы начать общение с ассистентом.
          </div>
        ) : (
          <ul className="divide-y divide-gray-200 dark:divide-gray-700">
            {chats.map((chat) => (
              <li key={chat.id}>
                <NavLink
                  to={`/chat/${chat.id}`}
                  className={({ isActive }) =>
                    `block p-4 hover:bg-gray-50 dark:hover:bg-gray-800 ${
                      isActive ? 'bg-gray-100 dark:bg-gray-800' : ''
                    }`
                  }
                >
                  <div className="flex justify-between items-center">
                    <div className="truncate flex-1">
                      <h3 className="text-sm font-medium text-gray-900 dark:text-white truncate">
                        {chat.title}
                      </h3>
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                        {formatDistanceToNow(new Date(chat.updated_at), {
                          addSuffix: true,
                          locale: ru,
                        })}
                      </p>
                    </div>
                    <button
                      onClick={(e) => deleteChat(chat.id, e)}
                      className="ml-2 p-1 text-gray-400 hover:text-red-500 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700"
                    >
                      <TrashIcon className="w-4 h-4" />
                    </button>
                  </div>
                </NavLink>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};

export default ChatList;