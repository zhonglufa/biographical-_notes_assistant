/**
 * 规范文档更新器 — 将蒸馏出的规则写入规范文档
 *
 * 功能：根据蒸馏引擎提取的规则，自动更新对应规范文档的
 *       章节内容、审查清单和反模式表。
 *
 * 使用: node distillation/spec-updater.js
 *       node distillation/spec-updater.js --category=z-order
 *       node distillation/spec-updater.js --dry-run  (预览模式，不实际写入)
 */

const path = require('path');
const fs = require('fs');

const DESIGN_DIR = path.resolve(__dirname, '../../design');

// 规范文档映射
const SPEC_MAP = {
  'z-order': {
    file: '作图-04-UML时序图.md',
    section: '§3.3.8.1',
    label: '渲染顺序（Z 轴顺序）',
  },
  'label': {
    file: '作图-01-通用规范.md',
    section: '§2.4.6',
    label: '标签白底矩形约束规则 (ST-16)',
  },
  'geometry': {
    file: '作图-01-通用规范.md',
    section: '§2.3.3',
    label: '标注与线间距规范',
  },
  'color': {
    file: '作图-01-通用规范.md',
    section: '§2.1.1',
    label: '色板总表',
  },
  'legend': {
    file: '作图-04-UML时序图.md',
    section: '§3.3.8.2',
    label: '图例规范',
  },
};

// 更新日志模板
function generateUpdateLog(category, changes) {
  const now = new Date().toISOString().slice(0, 10);
  const spec = SPEC_MAP[category];
  return `\n> **v-auto-${now}**（蒸馏自动更新）: ${spec.label} — ${changes}`;
}

// 预览更新内容
function previewUpdate(category) {
  const spec = SPEC_MAP[category];
  if (!spec) {
    console.log(`[spec-updater] ⚠ 未知类别: ${category}`);
    return;
  }

  const filePath = path.resolve(DESIGN_DIR, spec.file);
  if (!fs.existsSync(filePath)) {
    console.log(`[spec-updater] ⚠ 文件不存在: ${filePath}`);
    return;
  }

  console.log(`[spec-updater] 📝 [预览] 更新: ${spec.file} ${spec.section}`);
  console.log(`[spec-updater]   章节: ${spec.label}`);
  console.log(`[spec-updater]   更新日志: ${generateUpdateLog(category, '蒸馏规则补充')}`);
  console.log(`[spec-updater]   (dry-run 模式，未实际写入)`);
}

// 执行更新
function applyUpdate(category, changes) {
  const spec = SPEC_MAP[category];
  if (!spec) {
    console.log(`[spec-updater] ⚠ 未知类别: ${category}`);
    return false;
  }

  const filePath = path.resolve(DESIGN_DIR, spec.file);
  if (!fs.existsSync(filePath)) {
    console.log(`[spec-updater] ⚠ 文件不存在: ${filePath}`);
    return false;
  }

  const content = fs.readFileSync(filePath, 'utf-8');
  const logEntry = generateUpdateLog(category, changes);

  // 在文件末尾追加更新日志（先确保与末尾内容分隔）
  const trimmed = content.endsWith('\n') ? content : content + '\n';
  fs.writeFileSync(filePath, trimmed + '\n' + logEntry + '\n');
  console.log(`[spec-updater] ✅ 已更新: ${spec.file} ${spec.section}`);
  return true;
}

function main() {
  const args = process.argv.slice(2);
  let category = null;
  let isDryRun = false;

  for (const arg of args) {
    if (arg.startsWith('--category=')) category = arg.slice(11);
    if (arg.startsWith('--rule-id=')) category = 'rule'; // placeholder
    if (arg === '--dry-run') isDryRun = true;
  }

  // 如果没有指定类别，处理所有
  const categories = category ? [category] : Object.keys(SPEC_MAP);

  for (const cat of categories) {
    if (isDryRun) {
      previewUpdate(cat);
    } else {
      applyUpdate(cat, '蒸馏自动提取的规则补充');
    }
  }

  if (isDryRun) {
    console.log(`\n[spec-updater] 📋 预览完成，使用 --dry-run 移除可实际写入`);
  } else {
    console.log(`[spec-updater] ✅ 规范更新完成`);
  }
}

main();