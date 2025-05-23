// frontend/postcss.config.js
module.exports = {
    plugins: {
      tailwindcss: {},
      autoprefixer: {},
    },
  };
  
  // frontend/package.json
  {
    "name": "planfix-ai-assistant-frontend",
    "version": "0.1.0",
    "private": true,
    "dependencies": {
      "@testing-library/jest-dom": "^5.16.5",
      "@testing-library/react": "^13.4.0",
      "@testing-library/user-event": "^13.5.0",
      "axios": "^1.4.0",
      "date-fns": "^2.30.0",
      "lucide-react": "^0.259.0",
      "react": "^18.2.0",
      "react-dom": "^18.2.0",
      "react-markdown": "^8.0.7",
      "react-router-dom": "^6.14.1",
      "react-scripts": "5.0.1",
      "web-vitals": "^2.1.4"
    },
    "scripts": {
      "start": "react-scripts start",
      "build": "react-scripts build",
      "test": "react-scripts test",
      "eject": "react-scripts eject"
    },
    "eslintConfig": {
      "extends": [
        "react-app",
        "react-app/jest"
      ]
    },
    "browserslist": {
      "production": [
        ">0.2%",
        "not dead",
        "not op_mini all"
      ],
      "development": [
        "last 1 chrome version",
        "last 1 firefox version",
        "last 1 safari version"
      ]
    },
    "devDependencies": {
      "@tailwindcss/forms": "^0.5.3",
      "@tailwindcss/typography": "^0.5.9",
      "autoprefixer": "^10.4.14",
      "postcss": "^8.4.24",
      "tailwindcss": "^3.3.2"
    },
    "proxy": "http://localhost:8000"
  }