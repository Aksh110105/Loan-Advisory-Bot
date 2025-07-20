import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css'; // Tailwind & global styles
import App from './App';

// Initialize React 18 root
const container = document.getElementById('root');
const root = ReactDOM.createRoot(container);

root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
