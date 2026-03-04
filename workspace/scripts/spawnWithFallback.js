#!/usr/bin/env node
/**
 * spawnWithFallback - 带降级策略的子智能体分发工具
 * 
 * 用法：
 *   node spawnWithFallback.js '{"agentId": "frontend-engineer", "task": "..."}'
 * 
 * 模型降级策略：
 *   frontend-engineer: gemini → kimi → qwen
 *   backend-engineer: codex → glm5 → qwen
 *   product-manager: opus → qwen → glm5
 *   math-teacher: kimi → qwen → glm5
 *   ops-agent: qwen → glm5
 *   qa-engineer: qwen → glm5
 */

const MODEL_FALLBACK = {
  'frontend-engineer': ['freestyle/gemini-3-1-pro', 'bailian/kimi-k2.5', 'bailian/qwen3-coder-plus'],
  'backend-engineer': ['codex-makeup/gpt-5.3-codex', 'bailian/glm-5', 'bailian/qwen3-coder-plus'],
  'product-manager': ['anyrouter/claude-opus-4-6', 'bailian/qwen3-coder-plus', 'bailian/glm-5'],
  'math-teacher': ['bailian/kimi-k2.5', 'bailian/qwen3-coder-plus', 'bailian/glm-5'],
  'ops-agent': ['bailian/qwen3-coder-plus', 'bailian/glm-5'],
  'qa-engineer': ['bailian/qwen3-coder-plus', 'bailian/glm-5'],
  'default': ['bailian/qwen3-coder-plus', 'bailian/glm-5']
};

function getFallbackModels(agentId) {
  return MODEL_FALLBACK[agentId] || MODEL_FALLBACK['default'];
}

/**
 * 判断 spawn 是否成功
 */
function isSuccess(result) {
  if (!result) return false;
  if (result.error) return false;
  if (result.status === 'failed') return false;
  return true;
}

/**
 * 模拟 spawn（实际使用时调用 OpenClaw API）
 */
async function spawn(agentId, task, model, timeoutSeconds = 600) {
  const { execSync } = require('child_process');
  
  const payload = {
    agentId,
    task,
    model,
    mode: 'run',
    runTimeoutSeconds: timeoutSeconds
  };
  
  // 这里简化处理，实际应该调用 sessions_spawn tool
  // 目前只是打印命令，让调用者手动执行
  console.log(JSON.stringify({
    action: 'spawn',
    agentId,
    model,
    task: task.substring(0, 100) + '...',
    fallbackChain: getFallbackModels(agentId)
  }));
  
  return { status: 'accepted' };
}

/**
 * 带降级的 spawn
 */
async function spawnWithFallback(options) {
  const { agentId, task, timeoutSeconds = 600, preferredModel } = options;
  
  // 获取降级链
  let models = getFallbackModels(agentId);
  
  // 如果指定了首选模型，放到第一位
  if (preferredModel && !models.includes(preferredModel)) {
    models = [preferredModel, ...models];
  }
  
  const errors = [];
  
  for (const model of models) {
    try {
      console.error(`[spawnWithFallback] 尝试模型: ${model}`);
      
      const result = await spawn(agentId, task, model, timeoutSeconds);
      
      if (isSuccess(result)) {
        console.error(`[spawnWithFallback] 成功: ${model}`);
        return { success: true, model, result };
      }
      
      errors.push({ model, error: '返回结果无效' });
    } catch (e) {
      console.error(`[spawnWithFallback] 失败: ${model} - ${e.message}`);
      errors.push({ model, error: e.message });
    }
  }
  
  return {
    success: false,
    errors,
    message: `所有模型都失败了: ${models.join(' → ')}`
  };
}

// CLI 入口
if (require.main === module) {
  const args = process.argv.slice(2);
  
  if (args.length === 0) {
    console.log(`
用法: node spawnWithFallback.js '<JSON配置>'

示例:
  node spawnWithFallback.js '{"agentId":"frontend-engineer","task":"创建一个按钮组件"}'
  node spawnWithFallback.js '{"agentId":"backend-engineer","task":"实现登录API","timeoutSeconds":300}'

支持的 Agent:
  - frontend-engineer (前端开发)
  - backend-engineer (后端开发)
  - product-manager (产品设计)
  - math-teacher (数学教学)
  - ops-agent (运维/杂事)
  - qa-engineer (测试验证)
`);
    process.exit(0);
  }
  
  try {
    const config = JSON.parse(args[0]);
    spawnWithFallback(config).then(result => {
      console.log(JSON.stringify(result, null, 2));
      process.exit(result.success ? 0 : 1);
    });
  } catch (e) {
    console.error('解析参数失败:', e.message);
    process.exit(1);
  }
}

module.exports = { spawnWithFallback, getFallbackModels, MODEL_FALLBACK };