/**
 * Post-commit Hook — 保存后记录
 *
 * 功能：在修复完成后，记录本次修复的问题类型、修复方式、
 *       涉及文件等元数据，写入 lessons 数据库供蒸馏引擎使用。
 *
 * 使用: node hooks/post-commit.js --file=fig-xxx.svg --type=z-order --desc="alt 背景遮挡激活条"
 *       node hooks/post-commit.js --batch  (交互式输入)
 */

const path = require('path');
const Database = require('better-sqlite3');
const fs = require('fs');

const DB_PATH = path.resolve(__dirname, '../db/lessons.db');

// 解析参数
function parseArgs() {
  const args = process.argv.slice(2);
  const result = { batch: false };
  for (const arg of args) {
    if (arg.startsWith('--file=')) result.file = arg.slice(7);
    if (arg.startsWith('--type=')) result.type = arg.slice(7);
    if (arg.startsWith('--desc=')) result.desc = arg.slice(7);
    if (arg.startsWith('--fix=')) result.fix = arg.slice(6);
    if (arg === '--batch') result.batch = true;
  }
  return result;
}

// 记录修复记录
function recordLesson(db, entry) {
  const stmt = db.prepare(`
    INSERT INTO lessons (file_path, problem_type, description, fix_summary, severity, spec_ref)
    VALUES (@file, @type, @desc, @fix, @severity, @specRef)
  `);
  stmt.run({
    file: entry.file,
    type: entry.type,
    desc: entry.desc,
    fix: entry.fix,
    severity: entry.severity || 'medium',
    specRef: entry.specRef || '',
  });
  console.log(`[post-commit] ✅ 已记录: ${entry.type} → ${entry.desc}`);
}

// 交互式批量录入
function batchInput(db) {
  console.log('[post-commit] 📝 交互式录入模式，输入空行结束');
  const readline = require('readline').createInterface({
    input: process.stdin,
    output: process.stdout,
  });

  function ask() {
    readline.question('文件路径: ', (file) => {
      if (!file) { readline.close(); return; }
      readline.question('问题类型 (geometry/color/z-order/label/legend/other): ', (type) => {
        readline.question('问题描述: ', (desc) => {
          readline.question('修复摘要: ', (fix) => {
            recordLesson(db, { file, type, desc, fix });
            ask();
          });
        });
      });
    });
  }
  ask();
}

function main() {
  const args = parseArgs();
  const db = new Database(DB_PATH);

  // 使用 schema.sql 初始化表结构（与外部定义保持同步）
  const schemaPath = path.resolve(__dirname, '../db/schema.sql');
  if (fs.existsSync(schemaPath)) {
    const schema = fs.readFileSync(schemaPath, 'utf-8');
    db.exec(schema);
  } else {
    console.warn('[post-commit] ⚠ schema.sql 不存在，使用内联定义');
    db.exec(`
      CREATE TABLE IF NOT EXISTS lessons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_path TEXT NOT NULL,
        problem_type TEXT NOT NULL,
        description TEXT NOT NULL,
        fix_summary TEXT,
        severity TEXT DEFAULT 'medium',
        spec_ref TEXT DEFAULT '',
        created_at TEXT DEFAULT (datetime('now', 'localtime')),
        reviewed INTEGER DEFAULT 0,
        tags TEXT DEFAULT ''
      )
    `);
  }

  if (args.batch) {
    batchInput(db);
  } else if (args.file && args.type && args.desc) {
    recordLesson(db, {
      file: args.file,
      type: args.type,
      desc: args.desc,
      fix: args.fix || '',
    });
  } else {
    console.log('[post-commit] ⚠ 使用方式:');
    console.log('  node hooks/post-commit.js --file=fig-xxx.svg --type=z-order --desc="alt 背景遮挡激活条" --fix="改为透明背景 + 提前绘制"');
    console.log('  node hooks/post-commit.js --batch');
  }

  db.close();
}

main();