# SVG 作图自我学习机制

## 架构概述

```
┌──────────────────────────────────────────────────────────────┐
│                   自我学习机制体系                              │
├──────────┬──────────────┬───────────────┬────────────────────┤
│ 钩子层    │ 触发链        │ 蒸馏引擎       │ 持久化层            │
│ (Hook)   │ (Trigger)    │ (Distillation)│ (Database)         │
├──────────┼──────────────┼───────────────┼────────────────────┤
│ pre-     │ 问题检测 →    │ 分类器 →       │ lessons.db（教训）  │
│ commit   │ 问题分析 →    │ 规则提取 →     │ rules.json（规则）  │
│ post-    │ 模式提取 →    │ 规范生成       │ 每日统计（趋势）     │
│ commit   │ 规范更新       │               │                    │
└──────────┴──────────────┴───────────────┴────────────────────┘
```

## 使用方式

### 单次修复流程

```bash
# 1. 修改 SVG 文件
# 2. 运行 pre-commit 校验
npm run pre-commit -- --file=fig-xxx.svg

# 3. 修复通过后，记录本次修复
npm run post-commit

# 4. 运行蒸馏引擎，提取规则并更新规范
npm run distill
```

### 持续集成

```bash
# 初始化数据库
npm run init-db

# 注册 git hook（手动复制到 .git/hooks/）
cp hooks/pre-commit.js ../.git/hooks/pre-commit
cp hooks/post-commit.js ../.git/hooks/post-commit
```

## 目录结构

```
scripts/self-learning/
├── hooks/                    # 钩子脚本
│   ├── pre-commit.js         # 保存前校验
│   └── post-commit.js        # 保存后记录
├── trigger-chain/            # 触发链
│   ├── dispatch.js           # 事件分发器
│   └── rules/                # 规则集
│       ├── geometry.json     # 几何规则
│       ├── color.json        # 颜色规则
│       ├── z-order.json      # Z 轴顺序规则
│       └── label.json        # 标签规则
├── distillation/             # 蒸馏引擎
│   ├── classifier.js         # 问题分类
│   ├── extractor.js          # 规则提取
│   └── spec-updater.js       # 规范文档更新
├── db/                       # 数据库
│   ├── schema.sql            # 表结构
│   └── init.js               # 初始化脚本
├── package.json
└── README.md
```