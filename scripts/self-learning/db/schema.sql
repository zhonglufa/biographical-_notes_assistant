-- SVG 作图自我学习机制 — 数据库 Schema
-- 数据库: lessons.db (SQLite)

-- ==========================================
-- 1. 教训记录表 (核心表)
-- 记录每次修复的问题类型、描述、修复方式
-- ==========================================
CREATE TABLE IF NOT EXISTS lessons (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path       TEXT NOT NULL,              -- 问题文件路径
    problem_type    TEXT NOT NULL,              -- 问题类型: geometry/color/z-order/label/legend/other
    description     TEXT NOT NULL,              -- 问题描述（详细）
    fix_summary     TEXT,                       -- 修复摘要
    severity        TEXT DEFAULT 'medium',      -- 严重程度: high/medium/low
    spec_ref        TEXT DEFAULT '',            -- 引用的规范章节
    created_at      TEXT DEFAULT (datetime('now', 'localtime')),  -- 创建时间
    reviewed        INTEGER DEFAULT 0,          -- 是否已审查: 0=未审查, 1=已审查
    tags            TEXT DEFAULT '',            -- 标签（逗号分隔，用于多维分析）
    FOREIGN KEY (problem_type) REFERENCES problem_types(code)
);

-- ==========================================
-- 2. 问题类型字典表
-- 规范管理问题分类
-- ==========================================
CREATE TABLE IF NOT EXISTS problem_types (
    code            TEXT PRIMARY KEY,           -- 类型编码: geometry/color/z-order/label/legend
    name            TEXT NOT NULL,              -- 中文名称
    description     TEXT,                       -- 类型说明
    spec_section    TEXT,                       -- 对应的规范章节
    created_at      TEXT DEFAULT (datetime('now', 'localtime'))
);

-- 预置类型
INSERT OR IGNORE INTO problem_types (code, name, description, spec_section) VALUES
    ('geometry', '几何问题', '线段穿透、路径交叉、容器内外连接等', '作图-01-通用规范.md §2.3'),
    ('color', '颜色问题', '色板外颜色、颜色语义错误等', '作图-01-通用规范.md §2.1'),
    ('z-order', 'Z轴顺序问题', 'SVG 渲染顺序错误，组合片段遮挡激活条等', '作图-04-UML时序图.md §3.3.8'),
    ('label', '标签问题', '白底矩形遮挡箭头、标签位置偏移等', '作图-01-通用规范.md §2.4.6'),
    ('legend', '图例问题', '图例格式不完整、缺少要素等', '作图-04-UML时序图.md §3.3.8.2'),
    ('other', '其他问题', '未分类问题', 'N/A');

-- ==========================================
-- 3. 规则库表
-- 蒸馏引擎提取的通用规则
-- ==========================================
CREATE TABLE IF NOT EXISTS rules (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_id         TEXT UNIQUE NOT NULL,       -- 规则编号: GEO-001, COL-001, Z-001 等
    name            TEXT NOT NULL,              -- 规则名称
    severity        TEXT DEFAULT 'error',       -- 严重程度: error/warning
    problem_type    TEXT NOT NULL,              -- 关联问题类型
    description     TEXT,                       -- 规则描述
    detect_pattern  TEXT,                       -- 检测模式（正则表达式）
    fix_template    TEXT,                       -- 修复模板
    spec_section    TEXT,                       -- 规范章节
    checklist_ref   TEXT,                       -- 审查清单编号
    frequency       INTEGER DEFAULT 0,          -- 命中次数
    is_active       INTEGER DEFAULT 1,          -- 是否启用
    created_at      TEXT DEFAULT (datetime('now', 'localtime')),
    updated_at      TEXT DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (problem_type) REFERENCES problem_types(code)
);

-- ==========================================
-- 4. 规格统计表
-- 按类型/严重程度的多维聚合
-- ==========================================
CREATE TABLE IF NOT EXISTS statistics (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    problem_type    TEXT NOT NULL,              -- 问题类型
    period          TEXT NOT NULL,              -- 统计周期: daily/weekly/monthly
    count           INTEGER DEFAULT 0,          -- 发生次数
    avg_severity    REAL,                       -- 平均严重程度
    snapshot_date   TEXT NOT NULL,              -- 统计日期
    UNIQUE(problem_type, period, snapshot_date)
);

-- ==========================================
-- 5. 索引
-- 提升查询性能
-- ==========================================
CREATE INDEX IF NOT EXISTS idx_lessons_type ON lessons(problem_type);
CREATE INDEX IF NOT EXISTS idx_lessons_created ON lessons(created_at);
CREATE INDEX IF NOT EXISTS idx_lessons_severity ON lessons(severity);
CREATE INDEX IF NOT EXISTS idx_rules_type ON rules(problem_type);
CREATE INDEX IF NOT EXISTS idx_rules_active ON rules(is_active);
CREATE INDEX IF NOT EXISTS idx_statistics_type ON statistics(problem_type, snapshot_date);