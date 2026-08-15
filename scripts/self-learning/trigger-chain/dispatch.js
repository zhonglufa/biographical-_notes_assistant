/**
 * Trigger Chain Dispatcher — 事件分发器
 *
 * 功能：检测到问题后，按触发链自动化处理：
 *       问题检测 → 问题分析 → 模式提取 → 规范更新 → 反馈闭环
 *
 * 使用: node trigger-chain/dispatch.js --event=lint-fail --file=fig-xxx.svg
 *       node trigger-chain/dispatch.js --event=geometry-fail --file=fig-xxx.svg
 */

const path = require('path');
const fs = require('fs');
const { execSync } = require('child_process');

// 规则加载器
const RULES_DIR = path.resolve(__dirname, 'rules');

function loadRules() {
  const rules = {};
  const files = fs.readdirSync(RULES_DIR).filter(f => f.endsWith('.json'));
  for (const file of files) {
    const key = path.basename(file, '.json');
    rules[key] = JSON.parse(fs.readFileSync(path.resolve(RULES_DIR, file), 'utf-8'));
  }
  return rules;
}

// 将 JSON 中的检测函数字符串转为可执行函数
function createDetectFn(detectStr) {
  if (typeof detectStr === 'function') return detectStr;
  return new Function('eventType', 'payload', `return ${detectStr}`);
}

// 将 JSON 中的分析函数字符串转为可执行函数
function createAnalyzeFn(analyzeStr) {
  if (typeof analyzeStr === 'function') return analyzeStr;
  return new Function('payload', `return ${analyzeStr}`);
}

// 事件分类
function classifyEvent(eventType, payload) {
  const rules = loadRules();
  for (const [category, ruleSet] of Object.entries(rules)) {
    for (const rule of ruleSet.rules) {
      const detectFn = createDetectFn(rule.detect);
      if (detectFn(eventType, payload)) {
        return { category, rule };
      }
    }
  }
  return null;
}

// 执行触发链
function executeTriggerChain(eventType, payload) {
  console.log(`[dispatch] 🔔 事件: ${eventType}`);
  console.log(`[dispatch] 📄 文件: ${payload.file || 'N/A'}`);

  // Step 1: 分类
  console.log(`[dispatch] 🔍 Step 1: 问题分类...`);
  const match = classifyEvent(eventType, payload);
  if (!match) {
    console.log(`[dispatch] ⚠ 未匹配到已知规则，记录为未分类问题`);
    // 记录到数据库
    execSync(`node "${path.resolve(__dirname, '../hooks/post-commit.js')}" \
      --file="${payload.file}" --type=unclassified --desc="${payload.error || '未知问题'}"`, {
      encoding: 'utf-8',
    });
    return;
  }

  console.log(`[dispatch] ✅ 匹配规则: ${match.category}/${match.rule.id}`);

  // Step 2: 分析
  console.log(`[dispatch] 🔍 Step 2: 问题分析...`);
  const analyzeFn = createAnalyzeFn(match.rule.analyze);
  const analysis = analyzeFn(payload);
  console.log(`[dispatch]  根因: ${analysis.rootCause}`);
  console.log(`[dispatch]  影响: ${analysis.impact}`);

  // Step 3: 记录到 lessons db
  console.log(`[dispatch] 📝 Step 3: 记录教训...`);
  const fixCmd = `node "${path.resolve(__dirname, '../hooks/post-commit.js')}" \
    --file="${payload.file}" \
    --type="${match.category}" \
    --desc="${analysis.rootCause}" \
    --fix="${analysis.suggestedFix}" \
    --severity="${analysis.severity}"`;
  execSync(fixCmd, { encoding: 'utf-8' });

  // Step 4: 提取规则
  console.log(`[dispatch] ⚗ Step 4: 规则提取...`);
  const extractCmd = `node "${path.resolve(__dirname, '../distillation/extractor.js')}" \
    --category="${match.category}" \
    --rule-id="${match.rule.id}"`;
  try {
    execSync(extractCmd, { encoding: 'utf-8', timeout: 15000 });
  } catch (e) {
    console.warn(`[dispatch] ⚠ 规则提取跳过: ${e.message}`);
  }

  // Step 5: 更新规范
  console.log(`[dispatch] 📚 Step 5: 规范更新...`);
  const specCmd = `node "${path.resolve(__dirname, '../distillation/spec-updater.js')}" \
    --category="${match.category}" \
    --rule-id="${match.rule.id}"`;
  try {
    execSync(specCmd, { encoding: 'utf-8', timeout: 15000 });
  } catch (e) {
    console.warn(`[dispatch] ⚠ 规范更新跳过: ${e.message}`);
  }

  console.log(`[dispatch] ✅ 触发链完成`);
}

// 解析参数
function parseArgs() {
  const args = process.argv.slice(2);
  const result = { payload: {} };
  for (const arg of args) {
    if (arg.startsWith('--event=')) result.eventType = arg.slice(8);
    if (arg.startsWith('--file=')) result.payload.file = arg.slice(7);
    if (arg.startsWith('--error=')) result.payload.error = arg.slice(8);
    if (arg.startsWith('--line=')) result.payload.line = arg.slice(7);
  }
  return result;
}

// 主入口
function main() {
  const { eventType, payload } = parseArgs();
  if (!eventType) {
    console.log('[dispatch] ⚠ 使用方式:');
    console.log('  node trigger-chain/dispatch.js --event=lint-fail --file=fig-xxx.svg --error="...description..."');
    console.log('  node trigger-chain/dispatch.js --event=geometry-fail --file=fig-xxx.svg --error="...description..."');
    console.log('  node trigger-chain/dispatch.js --event=manual-review --file=fig-xxx.svg --error="...description..."');
    process.exit(1);
  }

  executeTriggerChain(eventType, payload);
}

main();