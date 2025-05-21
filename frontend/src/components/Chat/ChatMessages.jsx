// frontend/src/components/Chat/ChatMessages.jsx
import React, { useRef, useEffect } from 'react';
import { CheckIcon, ThumbsUpIcon, ThumbsDownIcon } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { formatRelative } from 'date-fns';
import { ru } from 'date-fns/locale';

const ChatMessages = ({ messages, loading, error, onFeedback }) => {
  const messagesEndRef = useRef(null);

  // Прокрутка вниз при новых сообщениях
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const formatTime = (dateString) => {
    return formatRelative(new Date(dateString), new Date(), {
      locale: ru,
    });
  };

  if (messages.length === 0 && !loading && !error) {
    return (
      <div className="h-full flex items-center justify-center p-4 text-center">
        <div className="max-w-md">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            Начало нового чата
          </h3>
          <p className="text-gray-500 dark:text-gray-400">
            Задайте вопрос ИИ-ассистенту о ваших проектах, задачах или любой другой информации
            из Planfix.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4">
      {messages.map((message) => (
        <div
          key={message.id}
          className={`flex ${
            message.role === 'user' ? 'justify-end' : 'justify-start'
          }`}
        >
          <div
            className={`max-w-3xl rounded-lg p-4 ${
              message.role === 'user'
                ? 'bg-indigo-600 text-white'
                : 'bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-white'
            }`}
          >
            <div className="prose dark:prose-invert prose-sm max-w-none">
              <ReactMarkdown>{message.content}</ReactMarkdown>
            </div>
            <div className="mt-2 flex items-center justify-between text-xs">
              <span
                className={
                  message.role === 'user'
                    ? 'text-indigo-200'
                    : 'text-gray-500 dark:text-gray-400'
                }
              >
                {formatTime(message.created_at)}
              </span>
              
              {message.role === 'assistant' && (
                <div className="flex space-x-2">
                  <button
                    onClick={() => onFeedback(message.id, 5)}
                    className="text-gray-500 hover:text-green-500 dark:text-gray-400 dark:hover:text-green-400"
                    title="Полезный ответ"
                  >
                    <ThumbsUpIcon className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => onFeedback(message.id, 1)}
                    className="text-gray-500 hover:text-red-500 dark:text-gray-400 dark:hover:text-red-400"
                    title="Бесполезный ответ"
                  >
                    <ThumbsDownIcon className="w-4 h-4" />
                  </button>
                </div>
              )}
              
              {message.role === 'user' && message.status === 'sent' && (
                <span className="text-indigo-200">
                  <CheckIcon className="w-4 h-4" />
                </span>
              )}
            </div>
          </div>
        </div>
      ))}
      
      {loading && (
        <div className="flex justify-start">
          <div className="max-w-3xl rounded-lg p-4 bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-white">
            <div className="flex space-x-2 items-center">
              <div className="w-2 h-2 rounded-full bg-gray-400 dark:bg-gray-500 animate-bounce"></div>
              <div className="w-2 h-2 rounded-full bg-gray-400 dark:bg-gray-500 animate-bounce" style={{ animationDelay: '0.2s' }}></div>
              <div className="w-2 h-2 rounded-full bg-gray-400 dark:bg-gray-500 animate-bounce" style={{ animationDelay: '0.4s' }}></div>
            </div>
          </div>
        </div>
      )}
      
      {error && (
        <div className="flex justify-center">
          <div className="max-w-3xl rounded-lg p-4 bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-100">
            <p>Ошибка: {error}</p>
          </div>
        </div>
      )}
      
      <div ref={messagesEndRef} />
    </div>
  );
};

export default ChatMessages;