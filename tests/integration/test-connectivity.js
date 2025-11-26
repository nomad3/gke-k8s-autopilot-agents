const axios = require('axios');
const { expect } = require('chai');

// Configuration
const API_URL = process.env.API_URL || 'http://localhost:8080';
const FRONTEND_URL = process.env.FRONTEND_URL || 'http://localhost:3000';

describe('Integration Tests: Microservices', function() {
  this.timeout(10000); // 10s timeout

  describe('Frontend Service', () => {
    it('should be reachable and return 200 OK', async () => {
      try {
        const response = await axios.get(FRONTEND_URL);
        expect(response.status).to.equal(200);
      } catch (error) {
        throw new Error(`Frontend unreachable: ${error.message}`);
      }
    });

    it('should have health check endpoint', async () => {
      try {
        const response = await axios.get(`${FRONTEND_URL}/health`);
        expect(response.status).to.equal(200);
      } catch (error) {
        // Some frontends might not expose /health, skip if 404
        if (error.response && error.response.status === 404) this.skip();
        throw error;
      }
    });
  });

  describe('Backend Service', () => {
    it('should be reachable and return 200 OK', async () => {
      try {
        const response = await axios.get(`${API_URL}/health`);
        expect(response.status).to.equal(200);
        expect(response.data).to.have.property('status', 'ok');
      } catch (error) {
        throw new Error(`Backend health check failed: ${error.message}`);
      }
    });

    it('should connect to database', async () => {
      try {
        const response = await axios.get(`${API_URL}/api/db-check`);
        expect(response.status).to.equal(200);
        expect(response.data).to.have.property('database', 'connected');
      } catch (error) {
        throw new Error(`Database connection check failed: ${error.message}`);
      }
    });
  });

  describe('End-to-End Flow', () => {
    it('should retrieve data from backend via frontend proxy (if applicable)', async () => {
      // This test assumes the frontend proxies /api requests to the backend
      try {
        const response = await axios.get(`${FRONTEND_URL}/api/health`);
        expect(response.status).to.equal(200);
      } catch (error) {
        if (error.response && error.response.status === 404) this.skip();
        throw error;
      }
    });
  });
});
