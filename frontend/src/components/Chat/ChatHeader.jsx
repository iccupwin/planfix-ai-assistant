// frontend/src/components/Chat/ChatHeader.jsx
import React, { useState } from 'react';
import { EditIcon, CheckIcon, XIcon } from 'lucide-react';

const ChatHeader = ({ chat, onUpdateTitle }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [title, setTitle] = useState(chat?.title || 'Новый чат');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (title.trim()) {
      onUpdateTitle(title);
      setIsEditing(false);
    }
  };

  const handleCancel = () => {
    setTitle(chat?.title || 'Новый чат');
    setIsEditing(false);
  };

  return (
    <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
      {isEditing ? (
        <form onSubmit={handleSubmit} className="flex-1 flex items-center">
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="flex-1 py-1 px-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            autoFocus
          />
          <button
            type="submit"
            className="ml-2 p-1 text-green-600 hover:text-green-700 dark:text-green-400 dark:hover:text-green-300"
          >
            <CheckIcon className="w-5 h-5" />
          </button>
          <button
            type="button"
            onClick={handleCancel}
            className="ml-1 p-1 text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300"
          >
            <XIcon className="w-5 h-5" />
          </button>
        </form>
      ) : (
        <div className="flex items-center flex-1">
          <h2 className="text-lg font-medium text-gray-900 dark:text-white truncate">
            {chat?.title || 'Новый чат'}
          </h2>
          <button
            onClick={() => setIsEditing(true)}
            className="ml-2 p-1 text-gray-400 hover:text-gray-500 dark:text-gray-500 dark:hover:text-gray-400"
          >
            <EditIcon className="w-4 h-4" />
          </button>
        </div>
      )}
    </div>
  );
};

export default ChatHeader;