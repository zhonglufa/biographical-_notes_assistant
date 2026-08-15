/**
 * 规则提取器 — 从修复记录中提取通用规则
 *
 * 功能：读取 lessons 数据库中同类别的问题记录，
 *       归纳出通用规则，输出为规则 JSON 文件。
 *
 * 使用: node distillation/extractor.js
 *       node distillation/extractor.js --category=z-order
 */

const path = require('path');
const Database = require('better-sqlite3');
const fs = require('fs');

const DB_PATH = path.resolve(__dirname, '../db/lessons.db');
const RULES_DIR = path.resolve(__dirname, '../trigger-chain/rules');

// 提取模板
const EXTRACTION_TEMPLATES = {
  'z-order': {
    pattern: '渲染顺序',
    template: {
      id: 'EXTRACTED-{num}',
      name: '提取规则: {rootCause}',
      severity: 'error',
      detect: `function(eventType, payload) { return eventType === 'review' && payload.error && payload.error.includes('{keyword}'); }`,
      analyze: `function(payload) { return { rootCause: '{rootCause}', impact: '{impact}', suggestedFix: '{fix}', severity: 'high' }; }`,
      specSection: '作图-04-UML时序图.md §3.3.8',
      checklist: '3.16',
    },
  },
  geometry: {
    pattern: '几何约束',
    template: {
      id: 'EXTRACTED-{num}',
      name: '提取规则: {rootCause}',
      severity: 'error',
      detect: `function(eventType, payload) { return eventType === 'geometry-fail' && payload.error && payload.error.includes('{keyword}'); }`,
      analyze: `function(payload) { return { rootCause: '{rootCause}', impact: '{impact}', suggestedFix: '{fix}', severity: 'high' }; }`,
      specSection: '作图-01-通用规范.md §2.3',
      checklist: 'Q5',
    },
  },
  label: {
    pattern: '标签约束',
    template: {
      id: 'EXTRACTED-{num}',
      name: '提取规则: {rootCause}',
      severity: 'error',
      detect: `function(eventType, payload) { return eventType === 'lint-fail' && payload.error && payload.error.includes('{keyword}'); }`,
      analyze: `function(payload) { return { rootCause: '{rootCause}', impact: '{impact}', suggestedFix: '{fix}', severity: 'high' }; }`,
      specSection: '作图-01-通用规范.md §2.4.6',
      checklist: 'Q12.4',
    },
  },
};

// 从 lessons 中提取趋势
function extractTrends(db, category) {
  let query;
  const params = {};

  if (category) {
    query = `SELECT description, fix_summary, COUNT(*) as freq
             FROM lessons WHERE problem_type = @category
             GROUP BY description ORDER BY freq DESC LIMIT 5`;
    params.category = category;
  } else {
    query = `SELECT problem_type, description, fix_summary, COUNT(*) as freq
             FROM lessons GROUP BY description ORDER BY freq DESC LIMIT 10`;
  }

  return db.prepare(query).all(params);
}

// 生成规则建议
function generateRuleEntry(trend, category, num) {
  const template = EXTRACTION_TEMPLATES[category];
  if (!template) return null;

  const keyword = (trend.description || '').slice(0, 10);
  const rootCause = trend.description || '未知';
  const fix = trend.fix_summary || '待补充';

  const impacts = {
    'z-order': '视觉遮挡，违反渲染顺序规范',
    geometry: '视觉混乱，不符合几何规范',
    label: '箭头被遮挡，不符合标签规范',
  };

  return {
    id: template.template.id.replace('{num}', String(num).padStart(3, '0')),
    name: template.template.name.replace('{rootCause}', rootCause.slice(0, 40)),
    severity: template.template.severity,
    detect: template.template.detect.replace('{keyword}', keyword),
    analyze: template.template.analyze
      .replace('{rootCause}', rootCause)
      .replace('{impact}', impacts[category] || '不符合规范')
      .replace('{fix}', fix),
    specSection: template.template.specSection,
    checklist: template.template.checklist,
    frequency: trend.freq,
    extractedFrom: 'auto-distillation',
  };
}

function main() {
  const args = process.argv.slice(2);
  let category = null;
  for (const arg of args) {
    if (arg.startsWith('--category=')) category = arg.slice(11);
    if (arg.startsWith('--rule-id=')) category = 'rule'; // placeholder
  }

  if (!fs.existsSync(DB_PATH)) {
    console.log('[extractor] ⚠ lessons.db 不存在，跳过提取');
    process.exit(0);
  }

  const db = new Database(DB_PATH);
  const trends = extractTrends(db, category);

  if (trends.length === 0) {
    console.log(`[extractor] ⚠ 没有找到${category ? ` ${category} 类别` : ''}的教训记录`);
    db.close();
    process.exit(0);
  }

  console.log(`[extractor] ⚗ 发现 ${trends.length} 个高频模式`);
  const newRules = [];

  for (let i = 0; i < trends.length; i++) {
    const trend = trends[i];
    const cat = category || trend.problem_type;
    const rule = generateRuleEntry(trend, cat, i + 1);
    if (rule && trend.freq >= 2) {
      // 仅对出现 ≥2 次的问题自动生成规则
      newRules.push(rule);
      console.log(`[extractor] 📝 生成规则 ${rule.id}: ${trend.description.slice(0, 50)}... (频率: ${trend.freq})`);
    }
  }

  if (newRules.length > 0) {
    const outputPath = path.resolve(RULES_DIR, `extracted-${Date.now()}.json`);
    fs.writeFileSync(outputPath, JSON.stringify({ name: '蒸馏提取规则', rules: newRules }, null, 2));
    console.log(`[extractor] ✅ 已写入 ${outputPath}`);
  } else {
    console.log('[extractor] ⚠ 没有满足频率阈值（≥2）的模式，跳过规则生成');
  }

  db.close();
}

main();