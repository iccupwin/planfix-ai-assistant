// frontend/src/pages/ChatPage.jsx
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import ChatList from '../components/Chat/ChatList';
import ChatHeader from '../components/Chat/ChatHeader';
import ChatMessages from '../components/Chat/ChatMessages';
import ChatInput from '../components/Chat/ChatInput';
import { getChat, updateChatTitle } from '../services/chat';
import websocketService from '../services/websocket';

const ChatPage = () => {
  const { chatId } = useParams();
  const navigate = useNavigate();
  
  const [chat, setChat] = useState(null);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [assistantTyping, setAssistantTyping] = useState(false);
  
  // Загрузка данных чата при изменении chatId
  useEffect(() => {
    const loadChat = async () => {
      if (!chatId) return;
      
      try {
        setLoading(true);
        const chatData = await getChat(chatId);
        setChat(chatData);
        setMessages(chatData.messages || []);
      } catch (err) {
        console.error('Error loading chat:', err);
        setError('Не удалось загрузить чат');
      } finally {
        setLoading(false);
      }
    };
    
    loadChat();
  }, [chatId]);
  
  // Подключение к WebSocket при загрузке чата
  useEffect(() => {
    if (!chatId) return;
    
    // Подключение к WebSocket
    websocketService.connect(chatId);
    
    // Обработка сообщений
    const unsubMessage = websocketService.onMessage((message, metadata) => {
      setMessages(prevMessages => [...prevMessages, message]);
    });
    
    // Обработка события набора текста
    const unsubTyping = websocketService.onTyping((data) => {
      if (data.type === 'assistant_typing') {
        setAssistantTyping(data.is_typing);
      }
    });
    
    // Обработка ошибок
    const unsubError = websocketService.onError((errorMessage) => {
      setError(errorMessage);
    });
    
    // Отключение от WebSocket при размонтировании компонента
    return () => {
      unsubMessage();
      unsubTyping();
      unsubError();
      websocketService.disconnect();
    };
  }, [chatId]);
  
  // Обработка отправки сообщения
  const handleSendMessage = (content) => {
    // Добавление сообщения в локальный state
    const userMessage = {
      id: `temp-${Date.now()}`,
      role: 'user',
      content,
      created_at: new Date().toISOString(),
      status: 'sending'
    };
    
    setMessages(prevMessages => [...prevMessages, userMessage]);
    
    // Отправка сообщения через WebSocket
    websocketService.sendMessage(content);
  };
  
  // Обработка обратной связи
  const handleFeedback = (messageId, rating) => {
    websocketService.sendFeedback(messageId, rating);
  };
  
  // Обработка обновления заголовка чата
  const handleUpdateTitle = async (title) => {
    try {
      const updatedChat = await updateChatTitle(chatId, title);
      setChat(updatedChat);
    } catch (err) {
      console.error('Error updating chat title:', err);
      setError('Не удалось обновить название чата');
    }
  };
  
  // Создание нового чата если не указан ID
  useEffect(() => {
    if (!chatId && chatId !== 'history') {
      const createNewChat = async () => {
        try {
          const chatListRef = document.querySelector('.chat-list-component');
          if (chatListRef && typeof chatListRef.createNewChat === 'function') {
            const newChatId = await chatListRef.createNewChat();
            if (newChatId) {
              navigate(`/chat/${newChatId}`);
            }
          }
        } catch (err) {
          console.error('Error creating new chat:', err);
          setError('Не удалось создать новый чат');
        }
      };
      
      createNewChat();
    }
  }, [chatId, navigate]);

  return (
    <div className="h-full flex">
      {/* Левая панель с чатами (видима только на больших экранах) */}
      <div className="hidden w-64 md:block border-r border-gray-200 dark:border-gray-700">
        <ChatList ref={(el) => (window.chatListComponent = el)} />
      </div>
      
      {/* Основная область чата */}
      <div className="flex-1 flex flex-col">
        {chatId && chatId !== 'history' ? (
          <>
            {/* Заголовок чата */}
            <ChatHeader chat={chat} onUpdateTitle={handleUpdateTitle} />
            
            {/* Сообщения */}
            <ChatMessages
              messages={messages}
              loading={assistantTyping}
              error={error}
              onFeedback={handleFeedback}
            />
            
            {/* Поле ввода */}
            <ChatInput
              onSendMessage={handleSendMessage}
              disabled={loading || assistantTyping}
            />
          </>
        ) : (
          <div className="h-full flex items-center justify-center p-4 text-center">
            <div className="max-w-md">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                Выберите чат
              </h3>
              <p className="text-gray-500 dark:text-gray-400 mb-4">
                Выберите существующий чат из списка слева или создайте новый чат, чтобы начать общение с ассистентом.
              </p>
              <button
                onClick={() => navigate('/chat')}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                Создать новый чат
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatPage;