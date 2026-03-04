const { test } = require('node:test');
const assert = require('assert');
const http = require('http');
const path = require('path');
const os = require('os');
const fs = require('fs');

// Import the server module (won't auto-listen because require.main !== module)
const { server, PORT } = require('./server.js');

// Helper function to make HTTP requests to the server
function makeRequest(options) {
  return new Promise((resolve, reject) => {
    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          resolve({
            statusCode: res.statusCode,
            headers: res.headers,
            body: data ? JSON.parse(data) : null
          });
        } catch (e) {
          resolve({
            statusCode: res.statusCode,
            headers: res.headers,
            body: data // Return as string if not JSON
          });
        }
      });
    });

    req.on('error', reject);
    if (options.data) {
      req.write(JSON.stringify(options.data));
    }
    req.end();
  });
}

// Test suite for Dashboard API
test('Dashboard API Tests', async (t) => {
  const testPort = 18899; // Use different port for testing
  
  await t.before(() => {
    return new Promise((resolve) => {
      server.listen(testPort, () => {
        console.log(`[TEST] Test server running on http://localhost:${testPort}`);
        resolve();
      });
    });
  });

  await t.after(() => {
    server.close();
  });

  // Test 1: Basic API route tests
  await t.test('GET /api/gateway/status returns correct format', async () => {
    const response = await makeRequest({
      hostname: 'localhost',
      port: testPort,
      path: '/api/gateway/status',
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    });

    assert.strictEqual(response.statusCode, 200);
    assert.ok(response.body.ok !== undefined);
    assert.ok(response.body.code !== undefined);
    assert.ok(response.body.message !== undefined);
    assert.ok(response.body.data !== undefined);
  });

  await t.test('GET /api/sessions returns correct format', async () => {
    const response = await makeRequest({
      hostname: 'localhost',
      port: testPort,
      path: '/api/sessions',
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    });

    assert.strictEqual(response.statusCode, 200);
    assert.ok(response.body.ok);
    assert.strictEqual(response.body.code, ERROR_CODE.SUCCESS);
    assert.ok(Array.isArray(response.body.data));
  });

  await t.test('GET /api/models returns correct format', async () => {
    const response = await makeRequest({
      hostname: 'localhost',
      port: testPort,
      path: '/api/models',
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    });

    assert.strictEqual(response.statusCode, 200);
    assert.ok(response.body.ok);
    assert.strictEqual(response.body.code, ERROR_CODE.SUCCESS);
    assert.ok(Array.isArray(response.body.data));
  });

  await t.test('GET /api/skills returns correct format', async () => {
    const response = await makeRequest({
      hostname: 'localhost',
      port: testPort,
      path: '/api/skills',
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    });

    assert.strictEqual(response.statusCode, 200);
    assert.ok(response.body.ok);
    assert.strictEqual(response.body.code, ERROR_CODE.SUCCESS);
    assert.ok(Array.isArray(response.body.data));
  });

  await t.test('GET /api/channels returns correct format', async () => {
    const response = await makeRequest({
      hostname: 'localhost',
      port: testPort,
      path: '/api/channels',
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    });

    assert.strictEqual(response.statusCode, 200);
    assert.ok(response.body.ok);
    assert.strictEqual(response.body.code, ERROR_CODE.SUCCESS);
    assert.ok(typeof response.body.data === 'object');
  });

  await t.test('GET /api/system/info returns correct format', async () => {
    const response = await makeRequest({
      hostname: 'localhost',
      port: testPort,
      path: '/api/system/info',
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    });

    assert.strictEqual(response.statusCode, 200);
    assert.ok(response.body.ok);
    assert.strictEqual(response.body.code, ERROR_CODE.SUCCESS);
    assert.ok(typeof response.body.data === 'object');
    assert.ok('hostname' in response.body.data);
    assert.ok('platform' in response.body.data);
    assert.ok('arch' in response.body.data);
    assert.ok('cpuCores' in response.body.data);
  });

  // Test 2: sanitizeConfig function tests
  await t.test('sanitizeConfig masks sensitive keys', () => {
    const testConfig = {
      apiKey: 'secret123',
      secret: 'very_secret',
      password: 'password123',
      token: 'abc123',
      normalKey: 'normal_value',
      nested: {
        api_key: 'nested_secret',
        regular: 'regular_value'
      },
      array: [
        { token: 'array_secret', id: 'valid' }
      ]
    };

    const sanitized = sanitizeConfig(testConfig);

    // Check that sensitive values are masked
    assert.strictEqual(sanitized.apiKey, '***masked***');
    assert.strictEqual(sanitized.secret, '***masked***');
    assert.strictEqual(sanitized.password, '***masked***');
    assert.strictEqual(sanitized.token, '***masked***');
    
    // Check that non-sensitive values remain unchanged
    assert.strictEqual(sanitized.normalKey, 'normal_value');
    
    // Check nested objects
    assert.strictEqual(sanitized.nested.api_key, '***masked***');
    assert.strictEqual(sanitized.nested.regular, 'regular_value');
    
    // Check arrays with objects
    assert.strictEqual(sanitized.array[0].token, '***masked***');
    assert.strictEqual(sanitized.array[0].id, 'valid');
  });

  await t.test('sanitizeConfig handles different key patterns', () => {
    const testConfig = {
      'api-key': 'secret1',
      'api_key': 'secret2',
      'APIKEY': 'secret3',
      'authorization': 'bearer token',
      'Authorization': 'Bearer Token',
      'appSecret': 'secret4',
      'botToken': 'secret5'
    };

    const sanitized = sanitizeConfig(testConfig);

    // All these patterns should be masked
    assert.strictEqual(sanitized['api-key'], '***masked***');
    assert.strictEqual(sanitized['api_key'], '***masked***');
    assert.strictEqual(sanitized['APIKEY'], '***masked***');
    assert.strictEqual(sanitized['authorization'], '***masked***');
    assert.strictEqual(sanitized['Authorization'], '***masked***');
    assert.strictEqual(sanitized['appSecret'], '***masked***');
    assert.strictEqual(sanitized['botToken'], '***masked***');
  });

  // Test 3: Error handling tests
  await t.test('Request to non-existent route returns 404', async () => {
    const response = await makeRequest({
      hostname: 'localhost',
      port: testPort,
      path: '/api/nonexistent/route',
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    });

    assert.strictEqual(response.statusCode, 404);
    assert.ok(!response.body.ok);
    assert.strictEqual(response.body.code, ERROR_CODE.NOT_FOUND);
    assert.strictEqual(response.body.message, 'Not found');
  });

  // Test 4: CORS headers test
  await t.test('API responses include CORS headers', async () => {
    const response = await makeRequest({
      hostname: 'localhost',
      port: testPort,
      path: '/api/gateway/status',
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    });

    assert.strictEqual(response.statusCode, 200);
    assert.ok(response.headers['access-control-allow-origin']);
    assert.strictEqual(response.headers['access-control-allow-origin'], '*');
    assert.ok(response.headers['access-control-allow-methods']);
    assert.ok(response.headers['access-control-allow-headers']);
    assert.ok(response.headers['content-type']);
  });

  // Test 5: OPTIONS preflight request
  await t.test('OPTIONS request returns 204 with CORS headers', async () => {
    const response = await makeRequest({
      hostname: 'localhost',
      port: testPort,
      path: '/api/gateway/status',
      method: 'OPTIONS',
      headers: { 'Content-Type': 'application/json' }
    });

    assert.strictEqual(response.statusCode, 204);
    assert.ok(response.headers['access-control-allow-origin']);
    assert.strictEqual(response.headers['access-control-allow-origin'], '*');
    assert.ok(response.headers['access-control-allow-methods']);
    assert.ok(response.headers['access-control-allow-headers']);
  });

  // Test 6: POST endpoints (if available)
  await t.test('POST /api/gateway/restart returns correct format', async () => {
    const response = await makeRequest({
      hostname: 'localhost',
      port: testPort,
      path: '/api/gateway/restart',
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });

    // The restart endpoint should return 202 (Accepted) or 500 (if it fails to execute)
    // Both are valid responses depending on the system state
    assert.ok([202, 500].includes(response.statusCode));
    assert.ok(response.body !== null);
    assert.ok('ok' in response.body);
    assert.ok('code' in response.body);
  });

  // Test 7: Config endpoint
  await t.test('GET /api/config returns sanitized config', async () => {
    const response = await makeRequest({
      hostname: 'localhost',
      port: testPort,
      path: '/api/config',
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    });

    assert.strictEqual(response.statusCode, 200);
    assert.ok(response.body.ok);
    assert.strictEqual(response.body.code, ERROR_CODE.SUCCESS);
    assert.ok(response.body.data !== null);
  });
});