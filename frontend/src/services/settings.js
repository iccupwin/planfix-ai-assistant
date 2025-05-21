import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const savePlanfixSettings = async (settings) => {
  try {
    const response = await axios.post(`${API_URL}/api/settings/planfix`, settings);
    return response.data;
  } catch (error) {
    throw error;
  }
};

export const getPlanfixSettings = async () => {
  try {
    const response = await axios.get(`${API_URL}/api/settings/planfix`);
    return response.data;
  } catch (error) {
    throw error;
  }
}; 