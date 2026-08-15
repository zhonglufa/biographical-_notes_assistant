/**
 * 数据库初始化脚本
 *
 * 功能：创建 lessons.db 数据库，初始化表结构和预置数据
 *
 * 使用: node db/init.js
 */

const path = require('path');
const fs = require('fs');
const Database = require('better-sqlite3');

const DB_PATH = path.resolve(__dirname, 'lessons.db');
const SCHEMA_PATH = path.resolve(__dirname, 'schema.sql');

function init() {
  // 删除旧数据库（如果存在）
  if (fs.existsSync(DB_PATH)) {
    console.log('[init] ⚠ 发现旧数据库，备份中...');
    const backupPath = DB_PATH.replace('.db', `.bak.${Date.now()}.db`);
    fs.copyFileSync(DB_PATH, backupPath);
    console.log(`[init] 📦 已备份到: ${path.basename(backupPath)}`);
    fs.unlinkSync(DB_PATH);
  }

  // 创建数据库
  const db = new Database(DB_PATH);

  // 执行 Schema
  const schema = fs.readFileSync(SCHEMA_PATH, 'utf-8');
  db.exec(schema);

  console.log('[init] ✅ 数据库初始化完成');
  console.log(`[init] 📁 路径: ${DB_PATH}`);

  // 验证
  const tables = db.prepare(`
    SELECT name FROM sqlite_master WHERE type='table' ORDER BY name
  `).all();

  console.log('[init] 📋 已创建表:');
  for (const table of tables) {
    const count = db.prepare(`SELECT COUNT(*) as count FROM ${table.name}`).get();
    console.log(`  - ${table.name} (${count.count} 条记录)`);
  }

  db.close();
}

init();