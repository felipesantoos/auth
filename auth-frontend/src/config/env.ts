/**
 * Type-safe environment configuration
 * Validates and exposes environment variables with type safety
 */

interface EnvironmentConfig {
  apiBaseUrl: string;
  apiTimeout: number;
  environment: 'development' | 'production' | 'test';
  logLevel: 'debug' | 'info' | 'warn' | 'error';
}

function getEnvVar(key: string, defaultValue?: string): string {
  const value = import.meta.env[key] || defaultValue;
  if (!value) {
    throw new Error(`Environment variable ${key} is required`);
  }
  return value;
}

export const env: EnvironmentConfig = {
  apiBaseUrl: getEnvVar('VITE_API_BASE_URL', 'http://localhost:8080'),
  apiTimeout: parseInt(getEnvVar('VITE_API_TIMEOUT', '10000'), 10),
  environment: (getEnvVar('VITE_ENVIRONMENT', 'development') as 'development' | 'production' | 'test'),
  logLevel: (getEnvVar('VITE_LOG_LEVEL', 'debug') as 'debug' | 'info' | 'warn' | 'error'),
};

// Validate on load
if (!['development', 'production', 'test'].includes(env.environment)) {
  throw new Error(`Invalid environment: ${env.environment}`);
}

if (!['debug', 'info', 'warn', 'error'].includes(env.logLevel)) {
  throw new Error(`Invalid log level: ${env.logLevel}`);
}

// Log configuration on startup (only in development)
if (env.environment === 'development') {
  console.log('🔧 Environment Configuration:', {
    apiBaseUrl: env.apiBaseUrl,
    environment: env.environment,
    logLevel: env.logLevel,
  });
}

