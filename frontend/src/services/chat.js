// frontend/src/services/chat.js
import api from './api';

export const getChats = async () => {
  const response = await api.get('/api/chat/');
  return response.data;
};

export const getChat = async (chatId) => {
  const response = await api.get(`/api/chat/${chatId}/`);
  return response.data;
};

export const createChat = async (title = null) => {
  const response = await api.post('/api/chat/', title ? { title } : {});
  return response.data;
};

export const updateChatTitle = async (chatId, title) => {
  const response = await api.patch(`/api/chat/${chatId}/`, { title });
  return response.data;
};

export const deleteChat = async (chatId) => {
  const response = await api.delete(`/api/chat/${chatId}/`);
  return response.data;
};

export const getChatMessages = async (chatId) => {
  const response = await api.get(`/api/chat/${chatId}/messages/`);
  return response.data;
};

export const sendMessage = async (chatId, content) => {
  const response = await api.post(`/api/chat/${chatId}/messages/`, { content });
  return response.data;
};

export const provideFeedback = async (messageId, rating, comment = '') => {
  const response = await api.post(`/api/chat/feedback/`, {
    message_id: messageId,
    rating,
    comment
  });
  return response.data;
};