// frontend/src/services/websocket.js
class WebSocketService {
    constructor() {
      this.socket = null;
      this.callbacks = {
        message: [],
        typing: [],
        error: []
      };
    }
  
    connect(chatId) {
      const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
      const token = localStorage.getItem('token');
      this.socket = new WebSocket(`${protocol}://${window.location.host}/ws/chat/${chatId}/?token=${token}`);
  
      this.socket.onopen = () => {
        console.log('WebSocket connection established');
      };
  
      this.socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          switch (data.type) {
            case 'chat_message':
              this.callbacks.message.forEach(callback => callback(data.message, data.metadata));
              break;
            case 'user_typing':
            case 'assistant_typing':
              this.callbacks.typing.forEach(callback => callback(data));
              break;
            case 'error':
              this.callbacks.error.forEach(callback => callback(data.message));
              break;
            default:
              console.log('Unknown message type:', data.type);
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };
  
      this.socket.onclose = (event) => {
        console.log('WebSocket connection closed:', event.code, event.reason);
        if (event.code === 4001) {
          // Unauthorized
          localStorage.removeItem('token');
          localStorage.removeItem('user');
          window.location.href = '/login';
        }
      };
  
      this.socket.onerror = (error) => {
        console.error('WebSocket error:', error);
        this.callbacks.error.forEach(callback => 
          callback('Ошибка соединения с сервером')
        );
      };
    }
  
    disconnect() {
      if (this.socket) {
        this.socket.close();
        this.socket = null;
      }
    }
  
    sendMessage(content) {
      if (this.socket && this.socket.readyState === WebSocket.OPEN) {
        this.socket.send(JSON.stringify({
          type: 'user_message',
          content,
          id: new Date().getTime().toString() // Временный ID для отслеживания
        }));
      } else {
        this.callbacks.error.forEach(callback => 
          callback('Соединение с сервером не установлено')
        );
      }
    }
  
    sendTyping(isTyping) {
      if (this.socket && this.socket.readyState === WebSocket.OPEN) {
        this.socket.send(JSON.stringify({
          type: 'typing',
          is_typing: isTyping
        }));
      }
    }
  
    sendFeedback(messageId, rating, comment = '') {
      if (this.socket && this.socket.readyState === WebSocket.OPEN) {
        this.socket.send(JSON.stringify({
          type: 'feedback',
          message_id: messageId,
          rating,
          comment
        }));
      } else {
        this.callbacks.error.forEach(callback => 
          callback('Соединение с сервером не установлено')
        );
      }
    }
  
    onMessage(callback) {
      this.callbacks.message.push(callback);
      return () => {
        this.callbacks.message = this.callbacks.message.filter(cb => cb !== callback);
      };
    }
  
    onTyping(callback) {
      this.callbacks.typing.push(callback);
      return () => {
        this.callbacks.typing = this.callbacks.typing.filter(cb => cb !== callback);
      };
    }
  
    onError(callback) {
      this.callbacks.error.push(callback);
      return () => {
        this.callbacks.error = this.callbacks.error.filter(cb => cb !== callback);
      };
    }
  }
  
  export default new WebSocketService();