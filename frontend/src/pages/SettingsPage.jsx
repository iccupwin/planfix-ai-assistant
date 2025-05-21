// frontend/src/pages/SettingsPage.jsx
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { savePlanfixSettings, getPlanfixSettings } from '../services/settings';

const SettingsPage = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [planfixForm, setPlanfixForm] = useState({
    planfixToken: '',
    planfixId: ''
  });
  const [message, setMessage] = useState({ type: '', text: '' });

  useEffect(() => {
    const loadSettings = async () => {
      try {
        const settings = await getPlanfixSettings();
        if (settings) {
          setPlanfixForm({
            planfixToken: settings.planfixToken || '',
            planfixId: settings.planfixId || ''
          });
        }
      } catch (error) {
        setMessage({ type: 'error', text: 'Ошибка при загрузке настроек' });
      }
    };

    loadSettings();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage({ type: '', text: '' });

    if (!planfixForm.planfixToken || !planfixForm.planfixId) {
      setMessage({ type: 'error', text: 'Пожалуйста, заполните все поля' });
      return;
    }

    try {
      await savePlanfixSettings(planfixForm);
      setMessage({ type: 'success', text: 'Настройки успешно сохранены' });
      navigate('/');
    } catch (error) {
      setMessage({ type: 'error', text: 'Ошибка при сохранении настроек' });
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setPlanfixForm(prev => ({
      ...prev,
      [name]: value
    }));
  };

  return (
    <div className="min-h-screen bg-gray-100 py-6 flex flex-col justify-center sm:py-12">
      <div className="relative py-3 sm:max-w-xl sm:mx-auto">
        <div className="relative px-4 py-10 bg-white shadow-lg sm:rounded-3xl sm:p-20">
          <div className="max-w-md mx-auto">
            <div className="divide-y divide-gray-200">
              <div className="py-8 text-base leading-6 space-y-4 text-gray-700 sm:text-lg sm:leading-7">
                <h2 className="text-2xl font-bold mb-8 text-center">Настройки Planfix</h2>
                {message.text && (
                  <div className={`p-4 rounded ${message.type === 'error' ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}`}>
                    {message.text}
                  </div>
                )}
                <form onSubmit={handleSubmit} className="space-y-6">
                  <div>
                    <label htmlFor="planfixToken" className="block text-sm font-medium text-gray-700">
                      API Token
                    </label>
                    <input
                      type="text"
                      name="planfixToken"
                      id="planfixToken"
                      value={planfixForm.planfixToken}
                      onChange={handleChange}
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                    />
                  </div>
                  <div>
                    <label htmlFor="planfixId" className="block text-sm font-medium text-gray-700">
                      Planfix ID
                    </label>
                    <input
                      type="text"
                      name="planfixId"
                      id="planfixId"
                      value={planfixForm.planfixId}
                      onChange={handleChange}
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                    />
                  </div>
                  <div>
                    <button
                      type="submit"
                      className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                    >
                      Сохранить
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;
