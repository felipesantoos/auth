import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import DIContainer from './app/dicontainer/container'
import { env } from './config/env'

// Initialize DI Container with type-safe env config
DIContainer.init(env.apiBaseUrl);

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
