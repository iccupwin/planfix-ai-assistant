// frontend/src/services/auth.js
import api from './api';

export const login = async (email, password) => {
  const response = await api.post('/api/accounts/login/', { email, password });
  localStorage.setItem('token', response.data.token);
  localStorage.setItem('user', JSON.stringify({
    id: response.data.user_id,
    email: response.data.email,
    firstName: response.data.first_name,
    lastName: response.data.last_name,
    isPlanfixConnected: response.data.is_planfix_connected
  }));
  return response.data;
};

export const register = async (email, password, firstName, lastName) => {
  const response = await api.post('/api/accounts/register/', {
    email,
    password,
    password2: password,
    first_name: firstName,
    last_name: lastName
  });
  localStorage.setItem('token', response.data.token);
  localStorage.setItem('user', JSON.stringify(response.data.user));
  return response.data;
};

export const logout = () => {
  localStorage.removeItem('token');
  localStorage.removeItem('user');
};

export const getCurrentUser = () => {
  const userStr = localStorage.getItem('user');
  if (userStr) {
    return JSON.parse(userStr);
  }
  return null;
};

export const isAuthenticated = () => {
  return !!localStorage.getItem('token');
};

export const updateUser = async (userData) => {
  const response = await api.put('/api/accounts/me/', userData);
  const currentUser = getCurrentUser();
  const updatedUser = { ...currentUser, ...response.data };
  localStorage.setItem('user', JSON.stringify(updatedUser));
  return response.data;
};

export const connectPlanfix = async (planfixToken, planfixId) => {
  const response = await api.post('/api/accounts/connect-planfix/', {
    planfix_token: planfixToken,
    planfix_id: planfixId
  });
  
  // Обновление статуса подключения Planfix в данных пользователя
  const currentUser = getCurrentUser();
  if (currentUser) {
    currentUser.isPlanfixConnected = response.data.is_planfix_connected;
    localStorage.setItem('user', JSON.stringify(currentUser));
  }
  
  return response.data;
};

export const disconnectPlanfix = async () => {
  const response = await api.post('/api/accounts/disconnect-planfix/');
  
  // Обновление статуса подключения Planfix в данных пользователя
  const currentUser = getCurrentUser();
  if (currentUser) {
    currentUser.isPlanfixConnected = false;
    localStorage.setItem('user', JSON.stringify(currentUser));
  }
  
  return response.data;
};
