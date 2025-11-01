import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import DIContainer from './app/dicontainer/container'

// Initialize DI Container
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080';
DIContainer.init(API_BASE_URL);

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
