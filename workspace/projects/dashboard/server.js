const http = require('http');
const fs = require('fs');
const path = require('path');
const os = require('os');
const { execFileSync, spawn } = require('child_process');

const PORT = 8899;
const CONFIG_PATH = path.join(os.homedir(), '.openclaw', 'openclaw.json');
const WORKSPACE_PATH = path.join(os.homedir(), '.openclaw', 'workspace');

const ERROR_CODE = {
  SUCCESS: 0,
  BAD_REQUEST: 40000,
  NOT_FOUND: 40400,
  BAD_GATEWAY: 50200,
  INTERNAL_ERROR: 50000,
};

// CORS headers
const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
  'Content-Type': 'application/json; charset=utf-8',
};

let configCache = {
  mtimeMs: null,
  data: null,
};

// Cache for system info (5-second cache)
let systemInfoCache = {
  data: null,
  timestamp: 0,
  ttl: 5000, // 5 seconds
};

// Cache for skills list (30-second cache)
let skillsCache = {
  data: null,
  timestamp: 0,
  ttl: 30000, // 30 seconds
};

// Cache for gateway logs (1-second cache)
let logsCache = {
  data: null,
  timestamp: 0,
  ttl: 1000, // 1 second
};

function success(data = null, message = 'ok', status = 200) {
  return {
    status,
    body: { ok: true, code: ERROR_CODE.SUCCESS, message, data },
  };
}

function failure(status, message, code = ERROR_CODE.INTERNAL_ERROR, data = null) {
  return {
    status,
    body: { ok: false, code, message, data },
  };
}

function sendJson(res, status, payload) {
  res.writeHead(status, corsHeaders);
  res.end(JSON.stringify(payload));
}

function safeExec(command, args = [], timeout = 10000) {
  try {
    return execFileSync(command, args, {
      encoding: 'utf-8',
      timeout,
      stdio: ['ignore', 'pipe', 'pipe'],
    }).trim();
  } catch {
    return null;
  }
}

function readConfig() {
  try {
    const stat = fs.statSync(CONFIG_PATH);
    if (configCache.data && configCache.mtimeMs === stat.mtimeMs) {
      return configCache.data;
    }

    const parsed = JSON.parse(fs.readFileSync(CONFIG_PATH, 'utf-8'));
    configCache = {
      mtimeMs: stat.mtimeMs,
      data: parsed,
    };
    return parsed;
  } catch {
    return null;
  }
}

function shouldMaskKey(key) {
  return /(api[-_]?key|secret|token|password|authorization|appSecret|botToken)/i.test(String(key));
}

function sanitizeConfig(value, key = '') {
  if (shouldMaskKey(key)) {
    return '***masked***';
  }

  if (Array.isArray(value)) {
    return value.map((item) => sanitizeConfig(item, key));
  }

  if (value && typeof value === 'object') {
    return Object.fromEntries(
      Object.entries(value).map(([k, v]) => [k, sanitizeConfig(v, k)])
    );
  }

  return value;
}

function parseJson(raw) {
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

function isSafeIdentifier(input) {
  return typeof input === 'string' && /^[\w./:-]{1,160}$/.test(input);
}

function joinUrl(base, suffix) {
  return `${String(base).replace(/\/+$/, '')}/${String(suffix).replace(/^\/+/, '')}`;
}

function extractModelPreview(responseJson) {
  const anthropicText = responseJson?.content
    ?.filter((item) => item && typeof item.text === 'string')
    .map((item) => item.text)
    .join(' ') || '';

  const openaiText = responseJson?.choices?.[0]?.message?.content || '';
  const previewSource = anthropicText || openaiText || JSON.stringify(responseJson || {});
  return String(previewSource).slice(0, 200);
}

// Route handlers
const routes = {
  'GET /api/gateway/status': async () => {
    const health = safeExec('openclaw', ['health', '--json']);
    if (health) {
      const parsed = parseJson(health);
      if (parsed) {
        return success(parsed);
      }
    }

    const status = safeExec('openclaw', ['gateway', 'status']);
    return success({
      raw: status || 'unable to fetch',
      running: /running/i.test(status || ''),
    });
  },

  'GET /api/gateway/logs': async (req) => {
    try {
      // Check cache first
      const now = Date.now();
      if (logsCache.data && (now - logsCache.timestamp) < logsCache.ttl) {
        return success(logsCache.data);
      }

      const url = new URL(req.url, 'http://localhost');
      const lines = parseInt(url.searchParams.get('lines') || '100', 10);
      const maxLines = Math.min(lines, 1000); // Max 1000 lines to prevent abuse

      // Find today's log file
      const today = new Date().toISOString().split('T')[0]; // YYYY-MM-DD
      const logDir = path.join('/tmp', 'openclaw');
      const logFilePath = path.join(logDir, `openclaw-${today}.log`);

      if (!fs.existsSync(logFilePath)) {
        return failure(404, `Log file not found: ${logFilePath}`, ERROR_CODE.NOT_FOUND);
      }

      // Read the last N lines from the log file
      const content = fs.readFileSync(logFilePath, 'utf-8');
      const linesArray = content.split('\n');
      const lastLines = linesArray.slice(-maxLines).filter(line => line.trim() !== '');
      
      const result = lastLines.join('\n');
      
      // Update cache
      logsCache.data = result;
      logsCache.timestamp = now;
      
      return success(result);
    } catch (error) {
      return failure(500, `Failed to read logs: ${error.message}`, ERROR_CODE.INTERNAL_ERROR);
    }
  },

  'POST /api/gateway/restart': async () => {
    try {
      const child = spawn('openclaw', ['gateway', 'restart'], {
        detached: true,
        stdio: 'ignore',
      });
      child.unref();
      return success(null, 'Restart initiated', 202);
    } catch {
      return failure(500, 'Failed to restart gateway', ERROR_CODE.INTERNAL_ERROR);
    }
  },

  'GET /api/agents': async () => {
    const config = readConfig();
    if (!config) {
      return failure(500, 'Cannot read config', ERROR_CODE.INTERNAL_ERROR);
    }

    const agents = (config.agents?.list || []).map((agent) => ({
      id: agent.id,
      name: agent.name || agent.id,
      model: agent.model || config.agents?.defaults?.model?.primary || 'default',
      workspace: agent.workspace || config.agents?.defaults?.workspace || '',
      hasAgentDir: Boolean(agent.agentDir),
    }));

    return success(agents);
  },

  'GET /api/agents/': async (req) => {
    // Extract agent ID from URL like /api/agents/agent-id/files
    const urlParts = req.url.split('?')[0].split('/');
    // ['', 'api', 'agents', '<id>', 'files']
    if (urlParts.length >= 5 && urlParts[4] === 'files') {
      const agentId = urlParts[3];
      if (!isSafeIdentifier(agentId)) {
        return failure(400, 'Invalid agent ID', ERROR_CODE.BAD_REQUEST);
      }
      
      // Get agent config to find workspace
      const config = readConfig();
      if (!config) {
        return failure(500, 'Cannot read config', ERROR_CODE.INTERNAL_ERROR);
      }

      const agentConfig = config.agents?.list?.find(a => a.id === agentId);
      if (!agentConfig) {
        return failure(404, `Agent "${agentId}" not found`, ERROR_CODE.NOT_FOUND);
      }

      const agentWorkspace = agentConfig.workspace || config.agents?.defaults?.workspace || '';
      const agentDir = agentConfig.agentDir;
      
      const result = {
        agentId,
        workspace: agentWorkspace,
        files: {}
      };

      // Read agent workspace files
      if (agentWorkspace) {
        const workspacePath = path.resolve(agentWorkspace);
        
        // Read SOUL.md, AGENTS.md, TOOLS.md, IDENTITY.md
        const workspaceFiles = ['SOUL.md', 'AGENTS.md', 'TOOLS.md', 'IDENTITY.md'];
        for (const fileName of workspaceFiles) {
          try {
            const filePath = path.join(workspacePath, fileName);
            if (fs.existsSync(filePath)) {
              result.files[fileName] = fs.readFileSync(filePath, 'utf-8');
            }
          } catch (error) {
            // Skip if file doesn't exist or can't be read
            continue;
          }
        }
      }

      // Read agentDir files if they exist
      if (agentDir) {
        const agentDirPath = path.resolve(agentDir);
        
        // Read auth.json (with sanitization)
        try {
          const authPath = path.join(agentDirPath, 'auth.json');
          if (fs.existsSync(authPath)) {
            const authContent = JSON.parse(fs.readFileSync(authPath, 'utf-8'));
            result.files['auth.json'] = sanitizeConfig(authContent);
          }
        } catch (error) {
          // Skip if file doesn't exist or can't be parsed
        }
        
        // Read models.json
        try {
          const modelsPath = path.join(agentDirPath, 'models.json');
          if (fs.existsSync(modelsPath)) {
            result.files['models.json'] = fs.readFileSync(modelsPath, 'utf-8');
          }
        } catch (error) {
          // Skip if file doesn't exist or can't be read
        }
      }

      return success(result);
    } else {
      return failure(404, 'Not found', ERROR_CODE.NOT_FOUND);
    }
  },

  'GET /api/model-stats': async () => {
    // 模型分配与降级策略
    const modelStats = {
      agents: [
        {
          id: 'frontend-engineer',
          name: '前端开发工程师',
          primaryModel: 'gemini-3-1-pro',
          fallbackModels: ['kimi-k2.5', 'qwen3-coder-plus']
        },
        {
          id: 'backend-engineer',
          name: '后端开发工程师',
          primaryModel: 'gpt-5.3-codex',
          fallbackModels: ['glm-5', 'qwen3-coder-plus']
        },
        {
          id: 'product-manager',
          name: '产品经理',
          primaryModel: 'opus-4.6',
          fallbackModels: ['qwen3-coder-plus', 'glm-5']
        },
        {
          id: 'math-teacher',
          name: '数学老师',
          primaryModel: 'kimi-k2.5',
          fallbackModels: ['qwen3-coder-plus', 'glm-5']
        },
        {
          id: 'ops-agent',
          name: '运营专家',
          primaryModel: 'qwen3-coder-plus',
          fallbackModels: ['glm-5']
        },
        {
          id: 'qa-engineer',
          name: 'QA测试工程师',
          primaryModel: 'qwen3-coder-plus',
          fallbackModels: ['glm-5']
        }
      ]
    };
    return success(modelStats);
  },

  'GET /api/models': async () => {
    const config = readConfig();
    if (!config) {
      return failure(500, 'Cannot read config', ERROR_CODE.INTERNAL_ERROR);
    }

    const providers = config.models?.providers || {};
    const result = [];

    for (const [providerId, provider] of Object.entries(providers)) {
      for (const model of provider.models || []) {
        result.push({
          provider: providerId,
          id: model.id,
          name: model.name || model.id,
          reasoning: model.reasoning || false,
          input: model.input || [],
          contextWindow: model.contextWindow || 0,
          maxTokens: model.maxTokens || 0,
          apiType: provider.api || 'openai-completions',
          alias: model.alias || undefined,
          usageBy: [] // Will be populated based on agent configs
        });
      }
    }

    // Populate usageBy information
    const agents = config.agents?.list || [];
    for (const model of result) {
      for (const agent of agents) {
        if (agent.model === model.id || 
            (agent.model && agent.model.includes(model.id)) ||
            (config.agents?.defaults?.model?.primary === model.id)) {
          model.usageBy.push(agent.id);
        }
      }
    }

    return success(result);
  },

  'GET /api/models/test': async (req) => {
    return handleModelTest(req.url);
  },

  'POST /api/models/test-all': async () => {
    try {
      const config = readConfig();
      if (!config) {
        return failure(500, 'Cannot read config', ERROR_CODE.INTERNAL_ERROR);
      }

      const providers = config.models?.providers || {};
      const testPromises = [];

      for (const [providerId, provider] of Object.entries(providers)) {
        for (const model of provider.models || []) {
          const testPromise = (async () => {
            try {
              if (!provider.baseUrl || !provider.apiKey) {
                return {
                  provider: providerId,
                  model: model.id,
                  ok: false,
                  error: 'Provider config missing baseUrl or apiKey'
                };
              }

              const apiType = provider.api || 'openai-completions';
              
              // Test basic connectivity and measure latency
              const basicResult = await testModelBasic(provider, model, apiType);
              
              // Test tool calling capability if possible
              let supportsToolCalls = false;
              try {
                const toolResult = await testModelToolCalling(provider, model, apiType);
                supportsToolCalls = toolResult.ok;
              } catch (toolError) {
                // If tool calling fails, that's okay, just means it doesn't support it
                supportsToolCalls = false;
              }

              return {
                provider: providerId,
                model: model.id,
                ...basicResult,
                supportsToolCalls
              };
            } catch (error) {
              return {
                provider: providerId,
                model: model.id,
                ok: false,
                error: error.message
              };
            }
          })();

          testPromises.push(testPromise);
        }
      }

      // Execute all tests concurrently using Promise.allSettled to handle failures gracefully
      const results = await Promise.allSettled(testPromises);
      
      // Process results to get both fulfilled and rejected promises
      const processedResults = results.map((result, index) => {
        if (result.status === 'fulfilled') {
          return result.value;
        } else {
          // Handle rejected promises
          const providerEntry = Object.entries(providers)[Math.floor(index / 10)]; // Approximate provider
          const modelEntry = providerEntry ? providerEntry[1].models[index % (providerEntry[1].models?.length || 1)] : null;
          
          return {
            provider: providerEntry ? providerEntry[0] : 'unknown',
            model: modelEntry ? modelEntry.id : 'unknown',
            ok: false,
            error: result.reason?.message || 'Test failed'
          };
        }
      });

      // Calculate summary statistics
      const passedCount = processedResults.filter(r => r.ok).length;
      const failedCount = processedResults.length - passedCount;

      return success({
        results: processedResults,
        summary: {
          total: processedResults.length,
          passed: passedCount,
          failed: failedCount
        }
      }, 'All models tested');
    } catch (error) {
      return failure(500, `Failed to test models: ${error.message}`, ERROR_CODE.INTERNAL_ERROR);
    }
  },

  'GET /api/sessions': async () => {
    const raw = safeExec('openclaw', ['sessions', '--json']);
    return success(parseJson(raw || '') || []);
  },

  'GET /api/cron/jobs': async () => {
    const raw = safeExec('openclaw', ['cron', 'list', '--json']);
    return success(parseJson(raw || '') || []);
  },

  'GET /api/skills': async () => {
    try {
      const now = Date.now();
      if (skillsCache.data && (now - skillsCache.timestamp) < skillsCache.ttl) {
        return success(skillsCache.data);
      }

      const homedir = os.homedir();
      const skillPaths = [
        path.join(homedir, '.openclaw', 'skills'),
        path.join(WORKSPACE_PATH, 'skills')
      ];
      
      const skills = [];
      
      for (const skillPath of skillPaths) {
        try {
          if (fs.existsSync(skillPath) && fs.statSync(skillPath).isDirectory()) {
            const items = fs.readdirSync(skillPath);
            for (const item of items) {
              if (item !== '.DS_Store' && fs.statSync(path.join(skillPath, item)).isDirectory()) {
                const skillDir = path.join(skillPath, item);
                const skillMdPath = path.join(skillDir, 'SKILL.md');
                
                if (fs.existsSync(skillMdPath)) {
                  try {
                    const content = fs.readFileSync(skillMdPath, 'utf-8');
                    
                    // Parse frontmatter if it exists
                    let description = 'No description available';
                    if (content.startsWith('---')) {
                      const endFrontmatter = content.indexOf('---', 3);
                      if (endFrontmatter > 0) {
                        const frontmatter = content.substring(3, endFrontmatter);
                        const lines = frontmatter.split('\n');
                        for (const line of lines) {
                          if (line.startsWith('description:')) {
                            description = line.substring(13).trim();
                            break;
                          }
                        }
                      }
                    }
                    
                    skills.push({
                      name: item,
                      description: description,
                      path: skillPath,
                      source: skillPath.includes('.openclaw') ? 'managed' : 'workspace'
                    });
                  } catch (err) {
                    // Add basic info if SKILL.md can't be read
                    skills.push({
                      name: item,
                      description: 'Error reading description',
                      path: skillPath,
                      source: skillPath.includes('.openclaw') ? 'managed' : 'workspace'
                    });
                  }
                } else {
                  // If no SKILL.md, add basic info
                  skills.push({
                    name: item,
                    description: 'No SKILL.md file found',
                    path: skillPath,
                    source: skillPath.includes('.openclaw') ? 'managed' : 'workspace'
                  });
                }
              }
            }
          }
        } catch (err) {
          // Continue to next path if one fails
          continue;
        }
      }
      
      // Update cache
      skillsCache.data = skills;
      skillsCache.timestamp = now;
      
      return success(skills);
    } catch (error) {
      return failure(500, 'Failed to read skills', ERROR_CODE.INTERNAL_ERROR);
    }
  },

  'GET /api/channels': async () => {
    const config = readConfig();
    if (!config) {
      return failure(500, 'Cannot read config', ERROR_CODE.INTERNAL_ERROR);
    }

    const channels = config.channels || {};
    const bindings = config.bindings || {};

    const result = {
      channels: {},
      bindings: bindings
    };

    for (const [channelId, channelConfig] of Object.entries(channels)) {
      result.channels[channelId] = {
        id: channelId,
        type: channelConfig.type || 'unknown',
        mode: channelConfig.mode || 'unknown', // websocket/webhook
        enabled: channelConfig.enabled !== false,
        config: sanitizeConfig(channelConfig) // Sanitize sensitive data
      };
    }

    return success(result);
  },

  'GET /api/memory': async () => {
    try {
      const memoryDir = path.join(WORKSPACE_PATH, 'memory');
      
      if (!fs.existsSync(memoryDir)) {
        return success([]);
      }

      const files = fs.readdirSync(memoryDir);
      const mdFiles = files.filter(file => file.endsWith('.md')).map(file => ({
        filename: file,
        size: fs.statSync(path.join(memoryDir, file)).size,
        modifiedAt: fs.statSync(path.join(memoryDir, file)).mtime.toISOString()
      }));

      return success(mdFiles);
    } catch (error) {
      return failure(500, `Failed to read memory directory: ${error.message}`, ERROR_CODE.INTERNAL_ERROR);
    }
  },

  'GET /api/memory/': async (req) => {
    const urlParts = req.url.split('/');
    if (urlParts.length >= 4) { // /api/memory/:filename
      const filename = decodeURIComponent(urlParts[3]);
      
      if (!filename.endsWith('.md') || !isSafeIdentifier(filename)) {
        return failure(400, 'Invalid filename', ERROR_CODE.BAD_REQUEST);
      }

      try {
        const memoryDir = path.join(WORKSPACE_PATH, 'memory');
        const filePath = path.join(memoryDir, filename);

        if (!fs.existsSync(filePath)) {
          return failure(404, `Memory file not found: ${filename}`, ERROR_CODE.NOT_FOUND);
        }

        const content = fs.readFileSync(filePath, 'utf-8');
        return success(content);
      } catch (error) {
        return failure(500, `Failed to read memory file: ${error.message}`, ERROR_CODE.INTERNAL_ERROR);
      }
    } else {
      return failure(404, 'Not found', ERROR_CODE.NOT_FOUND);
    }
  },

  'GET /api/system/info': async () => {
    try {
      // Check if we have a valid cache entry
      const now = Date.now();
      if (systemInfoCache.data && (now - systemInfoCache.timestamp) < systemInfoCache.ttl) {
        return success(systemInfoCache.data);
      }

      const cpus = os.cpus();
      const totalMem = os.totalmem();
      const freeMem = os.freemem();
      const loadAvg = os.loadavg();

      const systemInfo = {
        hostname: os.hostname(),
        platform: os.platform(),
        arch: os.arch(),
        nodeVersion: process.version,
        cpuModel: cpus[0]?.model || 'unknown',
        cpuCores: cpus.length,
        loadAvg: loadAvg.map((value) => Number(value.toFixed(2))),
        totalMemoryGB: Number((totalMem / 1073741824).toFixed(1)),
        freeMemoryGB: Number((freeMem / 1073741824).toFixed(1)),
        usedMemoryPercent: Number((((totalMem - freeMem) / totalMem) * 100).toFixed(1)),
        uptime: formatUptime(os.uptime()),
      };

      // Update cache
      systemInfoCache.data = systemInfo;
      systemInfoCache.timestamp = now;

      return success(systemInfo);
    } catch (error) {
      return failure(500, 'Failed to get system info', ERROR_CODE.INTERNAL_ERROR);
    }
  },

  'GET /api/config': async () => {
    const config = readConfig();
    if (!config) {
      return failure(500, 'Cannot read config', ERROR_CODE.INTERNAL_ERROR);
    }
    return success(sanitizeConfig(config));
  },

  'GET /api/heartbeat': async () => {
    try {
      const config = readConfig();
      if (!config) {
        return failure(500, 'Cannot read config', ERROR_CODE.INTERNAL_ERROR);
      }

      // Try to read HEARTBEAT.md if it exists
      let heartbeatContent = null;
      try {
        const heartbeatPath = path.join(WORKSPACE_PATH, 'HEARTBEAT.md');
        if (fs.existsSync(heartbeatPath)) {
          heartbeatContent = fs.readFileSync(heartbeatPath, 'utf-8');
        }
      } catch (error) {
        // Ignore error if HEARTBEAT.md doesn't exist or can't be read
      }

      const result = {
        config: {
          interval: config.heartbeat?.interval || 30000, // Default 30 seconds
          enabled: config.heartbeat?.enabled !== false
        },
        content: heartbeatContent
      };

      return success(result);
    } catch (error) {
      return failure(500, `Failed to read heartbeat: ${error.message}`, ERROR_CODE.INTERNAL_ERROR);
    }
  },
};

async function handleModelTest(rawUrl) {
  const params = new URL(rawUrl, 'http://localhost').searchParams;
  const provider = params.get('provider')?.trim();
  const model = params.get('model')?.trim();

  if (!provider || !model) {
    return failure(400, 'Missing provider or model param', ERROR_CODE.BAD_REQUEST);
  }

  if (!isSafeIdentifier(provider) || !isSafeIdentifier(model)) {
    return failure(400, 'Invalid provider or model param', ERROR_CODE.BAD_REQUEST);
  }

  const config = readConfig();
  if (!config) {
    return failure(500, 'Cannot read config', ERROR_CODE.INTERNAL_ERROR);
  }

  const providerConfig = config.models?.providers?.[provider];
  if (!providerConfig) {
    return failure(404, `Provider "${provider}" not found`, ERROR_CODE.NOT_FOUND);
  }

  const modelConfig = providerConfig.models?.find((item) => item.id === model);
  if (!modelConfig) {
    return failure(404, `Model "${model}" not found in ${provider}`, ERROR_CODE.NOT_FOUND);
  }

  if (!providerConfig.baseUrl || !providerConfig.apiKey) {
    return failure(500, 'Provider config missing baseUrl or apiKey', ERROR_CODE.INTERNAL_ERROR);
  }

  try {
    const parsedBaseUrl = new URL(providerConfig.baseUrl);
    if (!['http:', 'https:'].includes(parsedBaseUrl.protocol)) {
      return failure(400, 'Provider baseUrl must be http/https', ERROR_CODE.BAD_REQUEST);
    }
  } catch {
    return failure(400, 'Provider baseUrl is invalid', ERROR_CODE.BAD_REQUEST);
  }

  const apiType = providerConfig.api || 'openai-completions';
  const endpoint = apiType === 'anthropic-messages'
    ? joinUrl(providerConfig.baseUrl, 'v1/messages')
    : joinUrl(providerConfig.baseUrl, 'chat/completions');

  const headers = {
    'Content-Type': 'application/json',
  };

  let payload;
  if (apiType === 'anthropic-messages') {
    headers['x-api-key'] = providerConfig.apiKey;
    headers['anthropic-version'] = '2023-06-01';
    payload = {
      model,
      max_tokens: 20,
      messages: [{ role: 'user', content: 'Hi, reply with OK' }],
    };
  } else {
    headers.Authorization = `Bearer ${providerConfig.apiKey}`;
    payload = {
      model,
      max_tokens: 20,
      messages: [{ role: 'user', content: 'Hi, reply with OK' }],
    };
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 15000);

  let response;
  let responseText;
  try {
    response = await fetch(endpoint, {
      method: 'POST',
      headers,
      body: JSON.stringify(payload),
      signal: controller.signal,
    });
    responseText = await response.text();
  } catch {
    return failure(502, 'Request timeout or failed', ERROR_CODE.BAD_GATEWAY);
  } finally {
    clearTimeout(timeoutId);
  }

  const parsed = parseJson(responseText || '');

  if (!response.ok) {
    const detail = parsed?.error?.message || parsed?.error || String(responseText || '').slice(0, 200);
    return failure(502, `Provider returned ${response.status}`, ERROR_CODE.BAD_GATEWAY, {
      detail: String(detail).slice(0, 200),
    });
  }

  if (parsed?.error) {
    const detail = parsed.error.message || JSON.stringify(parsed.error);
    return failure(502, detail, ERROR_CODE.BAD_GATEWAY);
  }

  return success(
    { preview: extractModelPreview(parsed) },
    'Model responded successfully'
  );
}

function formatUptime(seconds) {
  const d = Math.floor(seconds / 86400);
  const h = Math.floor((seconds % 86400) / 3600);
  const m = Math.floor((seconds % 3600) / 60);

  const parts = [];
  if (d > 0) parts.push(`${d}d`);
  if (h > 0) parts.push(`${h}h`);
  parts.push(`${m}m`);
  return parts.join(' ');
}

const server = http.createServer(async (req, res) => {
  if (req.method === 'OPTIONS') {
    res.writeHead(204, corsHeaders);
    res.end();
    return;
  }

  try {
    const requestUrl = new URL(req.url || '/', 'http://localhost');
    const urlPath = requestUrl.pathname;
    
    // Special handling for dynamic routes like /api/agents/:id/files and /api/memory/:filename
    let routeKey = `${req.method} ${urlPath}`;
    
    // Check if the path might match a dynamic route
    if (urlPath.startsWith('/api/agents/') && urlPath.endsWith('/files')) {
      routeKey = `${req.method} /api/agents/`;
    } else if (urlPath.startsWith('/api/memory/')) {
      routeKey = `${req.method} /api/memory/`;
    }

    if (req.method === 'GET' && urlPath === '/api/models/test') {
      const result = await handleModelTest(req.url || '/');
      sendJson(res, result.status, result.body);
      return;
    }

    if (req.method === 'GET' && (urlPath === '/' || urlPath === '/index.html')) {
      const htmlPath = path.join(__dirname, 'index.html');
      try {
        const html = fs.readFileSync(htmlPath, 'utf-8');
        res.writeHead(200, { ...corsHeaders, 'Content-Type': 'text/html; charset=utf-8' });
        res.end(html);
      } catch {
        sendJson(
          res,
          404,
          failure(404, 'index.html not found', ERROR_CODE.NOT_FOUND).body
        );
      }
      return;
    }

    const handler = routes[routeKey];
    if (handler) {
      const result = await handler(req);
      sendJson(res, result.status, result.body);
      return;
    }

    sendJson(res, 404, failure(404, 'Not found', ERROR_CODE.NOT_FOUND).body);
  } catch (error) {
    console.error('[dashboard-api] unexpected error:', error && error.message ? error.message : error);
    sendJson(res, 500, failure(500, 'Internal server error', ERROR_CODE.INTERNAL_ERROR).body);
  }
});

// Only start if run directly (not required by tests)
if (require.main === module) {
  server.listen(PORT, () => {
    console.log(`🦞 OpenClaw Dashboard API running on http://localhost:${PORT}`);
  });
}

module.exports = { server, PORT, routes };