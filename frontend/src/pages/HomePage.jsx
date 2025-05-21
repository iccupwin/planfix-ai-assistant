// frontend/src/pages/HomePage.jsx
import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { PlusCircleIcon, MessageCircleIcon, SearchIcon } from 'lucide-react';

const HomePage = () => {
  const { user } = useAuth();
  
  return (
    <div className="max-w-5xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
      <header className="text-center mb-12">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">
          Добро пожаловать в Planfix ИИ-ассистент
        </h1>
        <p className="text-lg text-gray-600 dark:text-gray-400 max-w-3xl mx-auto">
          Персональный ИИ-ассистент с доступом к данным из Planfix. Задавайте вопросы о проектах, задачах и любой другой информации из вашего рабочего пространства.
        </p>
      </header>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Link
          to="/chat"
          className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 hover:shadow-lg transition-shadow duration-200"
        >
          <div className="flex items-center space-x-4 mb-4">
            <div className="bg-indigo-100 dark:bg-indigo-900 p-3 rounded-full">
              <PlusCircleIcon className="h-6 w-6 text-indigo-600 dark:text-indigo-400" />
            </div>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Новый чат</h2>
          </div>
          <p className="text-gray-600 dark:text-gray-400">
            Начните новую беседу с ИИ-ассистентом и получите ответы на ваши вопросы
          </p>
        </Link>
        
        <Link
          to="/chat/history"
          className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 hover:shadow-lg transition-shadow duration-200"
        >
          <div className="flex items-center space-x-4 mb-4">
            <div className="bg-green-100 dark:bg-green-900 p-3 rounded-full">
              <MessageCircleIcon className="h-6 w-6 text-green-600 dark:text-green-400" />
            </div>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">История чатов</h2>
          </div>
          <p className="text-gray-600 dark:text-gray-400">
            Просмотрите историю ваших бесед с ассистентом и продолжите общение
          </p>
        </Link>
        
        <Link
          to="/search"
          className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 hover:shadow-lg transition-shadow duration-200"
        >
          <div className="flex items-center space-x-4 mb-4">
            <div className="bg-purple-100 dark:bg-purple-900 p-3 rounded-full">
              <SearchIcon className="h-6 w-6 text-purple-600 dark:text-purple-400" />
            </div>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Поиск по Planfix</h2>
          </div>
          <p className="text-gray-600 dark:text-gray-400">
            Выполните семантический поиск по данным из Planfix
          </p>
        </Link>
      </div>
      
      {!user?.isPlanfixConnected && (
        <div className="mt-12 bg-yellow-50 dark:bg-yellow-900 border border-yellow-200 dark:border-yellow-800 p-6 rounded-lg">
          <h3 className="text-lg font-medium text-yellow-800 dark:text-yellow-200 mb-2">
            Подключите ваш аккаунт Planfix
          </h3>
          <p className="text-yellow-700 dark:text-yellow-300 mb-4">
            Для использования всех возможностей ассистента необходимо подключить ваш аккаунт Planfix. Это позволит получить доступ к вашим проектам, задачам и другим данным.
          </p>
          <Link
            to="/settings"
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-yellow-600 hover:bg-yellow-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-yellow-500"
          >
            Подключить Planfix
          </Link>
        </div>
      )}
    </div>
  );
};

export default HomePage;