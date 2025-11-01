import '@testing-library/jest-dom';
import { cleanup } from '@testing-library/react';
import { afterEach, beforeAll } from 'vitest';
import DIContainer from '../app/dicontainer/container';

// Initialize DI Container before all tests
beforeAll(() => {
  const API_BASE_URL = 'http://localhost:8080';
  DIContainer.init(API_BASE_URL);
});

afterEach(() => {
  cleanup();
});

