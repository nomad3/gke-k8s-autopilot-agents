/// <reference types="jest" />
import { jest } from '@jest/globals';
// Jest test setup for backend
// Increase default timeout for integration-like tests
jest.setTimeout(30000);

// Optionally, set test env vars for CI/local runs
process.env.LOG_LEVEL = process.env.LOG_LEVEL || 'error';
process.env.NODE_ENV = process.env.NODE_ENV || 'test';
