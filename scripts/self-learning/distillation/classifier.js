/**
 * 问题分类器 — 将问题归入已有类别，相同类别自动聚合
 *
 * 功能：读取 lessons 数据库，按 problem_type 聚合统计，
 *       输出分类报告，为蒸馏引擎提供输入。
 *
 * 使用: node distillation/classifier.js
 *       node distillation/classifier.js --report
 */

const path = require('path');
const Database = require('better-sqlite3');
const fs = require('fs');

const DB_PATH = path.resolve(__dirname, '../db/lessons.db');

// 分类类别定义
const CATEGORIES = {
  geometry: {
    name: '几何',
    keywords: ['穿透', '交叉', '路径', '路由', '折线', '正交', '对齐'],
    specRef: '作图-01-通用规范.md §2.3',
  },
  color: {
    name: '颜色',
    keywords: ['色板', '颜色', '语义', '填充', '描边', 'palette'],
    specRef: '作图-01-通用规范.md §2.1',
  },
  'z-order': {
    name: 'Z 轴顺序',
    keywords: ['顺序', 'z-index', '渲染', '遮挡', '覆盖', 'alt', '激活条', '分支背景'],
    specRef: '作图-04-UML时序图.md §3.3.8',
  },
  label: {
    name: '标签',
    keywords: ['白底', '标签', '矩形', '箭头', '标注', '文字'],
    specRef: '作图-01-通用规范.md §2.4.6',
  },
  legend: {
    name: '图例',
    keywords: ['图例', 'legend', '说明', '标注'],
    specRef: '作图-04-UML时序图.md §3.3.8.2',
  },
};

// 自动分类（根据描述文本匹配关键词）
function autoClassify(description) {
  const desc = (description || '').toLowerCase();
  for (const [key, cat] of Object.entries(CATEGORIES)) {
    for (const kw of cat.keywords) {
      if (desc.includes(kw.toLowerCase())) return key;
    }
  }
  return 'other';
}

// 生成分类报告
function generateReport(db) {
  console.log('═══════════════════════════════════════════');
  console.log('  问题分类报告');
  console.log('═══════════════════════════════════════════');

  const total = db.prepare('SELECT COUNT(*) as count FROM lessons').get();
  console.log(`\n📊 总记录数: ${total.count}`);

  console.log('\n--- 按类别统计 ---');
  const byType = db.prepare(`
    SELECT problem_type, COUNT(*) as count, GROUP_CONCAT(description, ' ||| ') as samples
    FROM lessons GROUP BY problem_type ORDER BY count DESC
  `).all();

  for (const row of byType) {
    const catName = CATEGORIES[row.problem_type]?.name || row.problem_type;
    console.log(`  ${catName}: ${row.count} 次`);
    const samples = row.samples.split(' ||| ').slice(0, 3);
    for (const s of samples) {
      console.log(`    - ${s.slice(0, 60)}${s.length > 60 ? '...' : ''}`);
    }
  }

  console.log('\n--- 按严重程度统计 ---');
  const bySeverity = db.prepare(`
    SELECT severity, COUNT(*) as count FROM lessons GROUP BY severity
  `).all();
  for (const row of bySeverity) {
    const icon = row.severity === 'high' ? '🔴' : row.severity === 'medium' ? '🟡' : '🟢';
    console.log(`  ${icon} ${row.severity}: ${row.count}`);
  }

  // 高频问题 TOP 3
  console.log('\n--- 高频问题 TOP 3 ---');
  const topTypes = byType.slice(0, 3);
  for (const row of topTypes) {
    const catName = CATEGORIES[row.problem_type]?.name || row.problem_type;
    const specRef = CATEGORIES[row.problem_type]?.specRef || 'N/A';
    console.log(`  ${catName} (${row.count} 次) → 规范: ${specRef}`);
  }

  console.log('\n═══════════════════════════════════════════');
}

// 补全未分类的记录
function fillUnclassified(db) {
  const unclassified = db.prepare(`
    SELECT id, description FROM lessons WHERE problem_type = 'unclassified' OR problem_type IS NULL
  `).all();

  if (unclassified.length === 0) {
    console.log('[classifier] ✅ 没有未分类的记录');
    return;
  }

  const update = db.prepare('UPDATE lessons SET problem_type = ? WHERE id = ?');
  const tx = db.transaction(() => {
    for (const row of unclassified) {
      const category = autoClassify(row.description);
      update.run(category, row.id);
      console.log(`[classifier] 📝 ID ${row.id}: ${row.description.slice(0, 40)}... → ${category}`);
    }
  });
  tx();
  console.log(`[classifier] ✅ 已补全 ${unclassified.length} 条记录`);
}

function main() {
  const args = process.argv.slice(2);
  const isReport = args.includes('--report');

  if (!fs.existsSync(DB_PATH)) {
    console.log('[classifier] ⚠ lessons.db 不存在，请先运行 post-commit 记录问题');
    process.exit(0);
  }

  const db = new Database(DB_PATH);

  // 补全分类
  fillUnclassified(db);

  // 生成报告
  if (isReport) {
    generateReport(db);
  } else {
    // 统计概况
    const total = db.prepare('SELECT COUNT(*) as count FROM lessons').get();
    const byType = db.prepare(
      'SELECT problem_type, COUNT(*) as count FROM lessons GROUP BY problem_type ORDER BY count DESC'
    ).all();
    console.log(`[classifier] 📊 共 ${total.count} 条记录，${byType.length} 个类别`);
    for (const row of byType) {
      const catName = CATEGORIES[row.problem_type]?.name || row.problem_type;
      console.log(`  ${catName}: ${row.count}`);
    }
  }

  db.close();
}

main();