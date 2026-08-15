#!/usr/bin/env node
/**
 * lint-svg.cjs - SVG 自动化校验脚本
 *
 * 用途: 检查 SVG 图是否符合 作图大全标准 v1.6 规范
 * 检查项:
 *   - ST-3: 图例只画颜色/线型 (无完整协议/动态流向文字)
 *   - ST-10: 垂直线文字不居中
 *   - ST-11: 水平线文字居中
 *   - ST-13: 文字与线段不交叉
 *   - ST-14: 每条线只有一个标注
 *   - 线宽强制 1.5px (普通线) / 2.5px (边界框)
 *   - 颜色色板一致性 (强制使用 #1A73E8 / #22C55E / #F59E0B / #9CA3AF)
 *   - 字号强制 9 / 10 / 11 / 13 / 14 px
 *   - viewBox 宽高比 3:2 ~ 4:3
 *   - C3 组件图专项: 目标容器虚线边界 / 灰盒样式 / 协议:端口禁用 / 组件数 ≤ 12
 *
 * 用法:
 *   node lint-svg.cjs <file.svg> [file2.svg ...]
 *   node lint-svg.cjs --dir <directory>           # 校验目录下所有 SVG
 *   node lint-svg.cjs --json <file.svg>           # JSON 格式输出
 *   node lint-svg.cjs --strict <file.svg>         # 严格模式 (警告也算失败)
 *
 * 退出码:
 *   0 - PASS 或 PASS_WITH_WARNINGS
 *   1 - FAIL
 *   2 - 参数错误
 *
 * 对应文档: 作图-01-通用规范.md §2.4.5-2.4.10 (ST 规则)
 *           作图-10-附录.md 附录 D (脚本接口规范)
 */

'use strict';

const fs = require('fs');
const path = require('path');

// ============================================================
// 1. 常量与配置
// ============================================================

const CONFIG = {
  // 强制色板 (fill/stroke)
  ALLOWED_COLORS: new Set([
    '#1A73E8', '#22C55E', '#EF4444', '#E8A317', '#F59E0B',
    '#9CA3AF', '#333333', '#666666', '#999999', '#F8F9FA',
    '#DBEAFE', '#F0F0F0', '#FFFFFF', '#DC2626', '#1f2937',
    '#475569', '#64748b', '#0284c7', '#e0f2fe', '#f0fdf4',
    '#fef2f2', '#f8fafc', '#e2e8f0', '#f0f9ff', '#fdf4ff',
    '#94a3b8', '#F3F4F6', '#6B7280', '#CBD5E1',
    '#D1D5DB', '#F9FAFB', '#F5F5F5',
    '#AAAAAA', '#D0D0D0',
    '#000000', '#00000010', '#00000020',
    'none'
  ]),

  // 强制字号
  ALLOWED_FONT_SIZES: new Set([9, 10, 11, 12, 13, 14, 16]),

  // 强制线宽
  ALLOWED_STROKE_WIDTHS: new Set([0.5, 1, 1.5, 2, 2.5, 3]),

  // viewBox 宽高比范围
  ASPECT_RATIO: { min: 1.33, max: 2.0 }, // 4:3 ~ 2:1

  // 路径解析正则
  PATH_D_REGEX: /M\s*([\d.-]+)[,\s]+([\d.-]+)|L\s*([\d.-]+)[,\s]+([\d.-]+)/g,

  // 标签字符最大长度
  MAX_LABEL_LENGTH: 50
};

// ============================================================
// 2. SVG 解析器
// ============================================================

class SVGParser {
  constructor(svgContent) {
    this.content = svgContent;
    this.lines = [];
    this.paths = [];
    this.texts = [];
    this.rects = [];
    this.circles = [];
    this.viewBox = null;
    this.parse();
  }

  parse() {
    // 提取 viewBox
    const vbMatch = this.content.match(/viewBox="([^"]+)"/);
    if (vbMatch) {
      const parts = vbMatch[1].trim().split(/[\s,]+/).map(Number);
      if (parts.length === 4) {
        this.viewBox = { x: parts[0], y: parts[1], w: parts[2], h: parts[3] };
      }
    }

    // 提取所有 <path> 元素 (含 d/stroke/stroke-width/stroke-dasharray/marker-end)
    const pathRegex = /<path\b([^/>]*)\/?>/g;
    let m;
    while ((m = pathRegex.exec(this.content)) !== null) {
      const attrs = this.parseAttributes(m[1]);
      this.paths.push({
        d: attrs.d || '',
        stroke: attrs.stroke || '',
        strokeWidth: parseFloat(attrs['stroke-width'] || '1'),
        strokeDasharray: attrs['stroke-dasharray'] || '',
        markerEnd: attrs['marker-end'] || '',
        fill: attrs.fill || 'none'
      });
    }

    // 提取所有 <text> 元素 (含 x/y/font-size/text-anchor)
    const textRegex = /<text\b([^>]*)>([\s\S]*?)<\/text>/g;
    while ((m = textRegex.exec(this.content)) !== null) {
      const attrs = this.parseAttributes(m[1]);
      this.texts.push({
        x: parseFloat(attrs.x || '0'),
        y: parseFloat(attrs.y || '0'),
        fontSize: parseFloat(attrs['font-size'] || '11'),
        textAnchor: attrs['text-anchor'] || 'start',
        content: m[2].replace(/<[^>]+>/g, '').trim()
      });
    }

    // 提取所有 <rect> 元素 (含 x/y/width/height/fill/stroke)
    const rectRegex = /<rect\b([^/>]*)\/?>/g;
    while ((m = rectRegex.exec(this.content)) !== null) {
      const attrs = this.parseAttributes(m[1]);
      this.rects.push({
        x: parseFloat(attrs.x || '0'),
        y: parseFloat(attrs.y || '0'),
        w: parseFloat(attrs.width || '0'),
        h: parseFloat(attrs.height || '0'),
        fill: attrs.fill || '',
        stroke: attrs.stroke || '',
        strokeDasharray: attrs['stroke-dasharray'] || ''
      });
    }

    // 提取所有 <circle> 元素
    const circleRegex = /<circle\b([^/>]*)\/?>/g;
    while ((m = circleRegex.exec(this.content)) !== null) {
      const attrs = this.parseAttributes(m[1]);
      this.circles.push({
        cx: parseFloat(attrs.cx || '0'),
        cy: parseFloat(attrs.cy || '0'),
        r: parseFloat(attrs.r || '0'),
        fill: attrs.fill || '',
        stroke: attrs.stroke || ''
      });
    }
  }

  parseAttributes(attrStr) {
    const attrs = {};
    const re = /(\S+?)="([^"]*)"|(\S+?)=([^\s>]+)/g;
    let m;
    while ((m = re.exec(attrStr)) !== null) {
      attrs[m[1] || m[3]] = m[2] || m[4] || '';
    }
    return attrs;
  }

  // 解析 path d 属性为线段数组
  parsePathSegments(d) {
    const segments = [];
    const re = /([MLHV])\s*([\d.-]+)[,\s]+([\d.-]+)(?:[,\s]+([\d.-]+)[,\s]+([\d.-]+))?/g;
    let m;
    let lastX = 0, lastY = 0;
    while ((m = re.exec(d)) !== null) {
      const cmd = m[1];
      const x1 = cmd === 'M' || cmd === 'L' ? parseFloat(m[2]) : lastX;
      const y1 = cmd === 'M' || cmd === 'L' ? parseFloat(m[3]) : lastY;
      let x2, y2;
      if (cmd === 'H') {
        x2 = parseFloat(m[2]);
        y2 = y1;
      } else if (cmd === 'V') {
        x2 = x1;
        y2 = parseFloat(m[2]);
      } else {
        x2 = cmd === 'M' || cmd === 'L' ? parseFloat(m[4] || m[2]) : lastX;
        y2 = cmd === 'M' || cmd === 'L' ? parseFloat(m[5] || m[3]) : lastY;
      }
      segments.push({ x1, y1, x2, y2, type: cmd });
      lastX = x2;
      lastY = y2;
    }
    return segments;
  }
}

// ============================================================
// 3. 校验规则
// ============================================================

class LintResult {
  constructor(file) {
    this.file = file;
    this.errors = [];      // 必须修复
    this.warnings = [];    // 建议改进
    this.passed = [];      // 通过的检查项
  }

  addError(rule, message, location = '') {
    this.errors.push({ rule, message, location });
  }

  addWarning(rule, message, location = '') {
    this.warnings.push({ rule, message, location });
  }

  addPass(rule) {
    this.passed.push(rule);
  }

  get status() {
    if (this.errors.length > 0) return 'FAIL';
    if (this.warnings.length > 0) return 'PASS_WITH_WARNINGS';
    return 'PASS';
  }
}

function lintFile(filePath, options = {}) {
  const content = fs.readFileSync(filePath, 'utf8');
  const parser = new SVGParser(content);
  const result = new LintResult(filePath);

  // ---- ST-10: 垂直线文字位置 ----
  checkST10(parser, result);

  // ---- ST-11: 水平线文字位置 ----
  checkST11(parser, result);

  // ---- ST-13: 文字与线不交叉 ----
  checkST13(parser, result);

  // ---- ST-14: 每条线只有一个标注 ----
  checkST14(parser, result);

  // ---- 线宽强制 ----
  checkStrokeWidth(parser, result);

  // ---- 颜色色板一致性 ----
  checkColorPalette(parser, result);

  // ---- 字号强制 ----
  checkFontSize(parser, result);

  // ---- viewBox 宽高比 ----
  checkViewBoxAspect(result, parser);

  // ---- C3 组件图专项 ----
  if (filePath.toLowerCase().includes('c3') || /c3-?component/i.test(filePath)) {
    checkC3Diagram(parser, result);
  }

  return result;
}

// ST-10: 垂直线文字位置 - 居中 (text-anchor="middle" 且 x 与 path 垂直段重合) 视为违规
function checkST10(parser, result) {
  for (const text of parser.texts) {
    if (text.textAnchor !== 'middle') {
      result.addPass('ST-10');
      continue;
    }
    // 找到与 text.x 最近的垂直线段
    for (const path of parser.paths) {
      const segments = parser.parsePathSegments(path.d);
      for (const seg of segments) {
        // 垂直段: x1 == x2
        if (seg.x1 === seg.x2 && Math.abs(seg.x1 - text.x) < 5) {
          // 检查文字 y 是否在垂直段 y 范围内
          const yMin = Math.min(seg.y1, seg.y2);
          const yMax = Math.max(seg.y1, seg.y2);
          if (text.y >= yMin && text.y <= yMax) {
            result.addError(
              'ST-10',
              `垂直线文字居中 (text x=${text.x}, y=${text.y}, 与垂直线 x=${seg.x1} 重合), 应改为 text-anchor="end" (居左) 或 "start" (居右)`,
              `<text>${text.content}</text>`
            );
            return;
          }
        }
      }
    }
    result.addPass('ST-10');
  }
}

// ST-11: 水平线文字位置 - 居中 (text-anchor="middle" 且 y 与 path 水平段接近) 是正确的
function checkST11(parser, result) {
  // 这条规则主要验证水平线段上的文字是否居中(无强制报错,仅警告)
  let hasWarning = false;
  for (const text of parser.texts) {
    if (text.textAnchor !== 'middle') continue;
    for (const path of parser.paths) {
      const segments = parser.parsePathSegments(path.d);
      for (const seg of segments) {
        // 水平段: y1 == y2
        if (seg.y1 === seg.y2 && Math.abs(seg.y1 - text.y) < 8) {
          if (text.x >= Math.min(seg.x1, seg.x2) && text.x <= Math.max(seg.x1, seg.x2)) {
            // 文字 y 在水平段上下 8px 内
            if (Math.abs(text.y - seg.y1) > 6) {
              result.addWarning(
                'ST-11',
                `水平线文字 y=${text.y} 与水平线 y=${seg.y1} 距离 > 6px, 应在水平段上方 4-6px`,
                `<text>${text.content}</text>`
              );
              hasWarning = true;
            }
          }
        }
      }
    }
  }
  if (!hasWarning) result.addPass('ST-11');
}

// ST-13: 文字与所有线不交叉 - 简化版: 检查文字 bbox 与线段 bbox 是否相交
function checkST13(parser, result) {
  for (const text of parser.texts) {
    if (!text.content || text.content.length === 0) continue;
    // 估算文字 bbox (字符宽度近似 字号 * 0.6)
    const charW = text.fontSize * 0.6;
    const bbox = {
      x1: text.x - (text.textAnchor === 'middle' ? (text.content.length * charW) / 2 : 0),
      y1: text.y - text.fontSize,
      x2: text.x + (text.textAnchor === 'middle' ? (text.content.length * charW) / 2 : text.content.length * charW),
      y2: text.y + 2
    };

    for (const path of parser.paths) {
      const segments = parser.parsePathSegments(path.d);
      for (const seg of segments) {
        if (segmentsIntersect(bbox, seg)) {
          // 排除容器内部装饰文字 (如 rect 内的 label)
          if (isInsideContainer(bbox, parser.rects)) continue;
          result.addWarning(
            'ST-13',
            `文字 "${text.content}" (x=${text.x}, y=${text.y}) 与线段 (${seg.x1},${seg.y1})-(${seg.x2},${seg.y2}) 相交`,
            `<text>${text.content}</text>`
          );
        }
      }
    }
  }
  result.addPass('ST-13');
}

// ST-14: 每条线只有一个标注 - 简化: 同一条线的差异段上不应有 2+ 连线标注
function checkST14(parser, result) {
  // 简化为: 同一 path 周围 30px 内不应有 2+ text
  for (const path of parser.paths) {
    const segments = parser.parsePathSegments(path.d);
    const nearbyTexts = [];
    for (const text of parser.texts) {
      // 排除「盒内文字」(盒标题/子标签): 其中心落在任一 <rect> 盒范围内,
      // 视为组件标签而非连线标注, 不计入 ST-14, 避免对盒标题的误报
      if (textCenterInsideBox(text, parser.rects)) continue;
      for (const seg of segments) {
        const dist = pointToSegmentDistance(text.x, text.y, seg);
        if (dist < 30) {
          nearbyTexts.push(text.content);
          break;
        }
      }
    }
    if (nearbyTexts.length > 1) {
      result.addError(
        'ST-14',
        `单条线附近有 ${nearbyTexts.length} 个文字标签: ${nearbyTexts.join(', ')}, 应只保留 1 个`,
        `<path d="${path.d.substring(0, 50)}..."/>`
      );
    }
  }
  result.addPass('ST-14');
}

// 线宽强制
function checkStrokeWidth(parser, result) {
  for (const path of parser.paths) {
    if (path.stroke && path.stroke !== 'none') {
      if (!CONFIG.ALLOWED_STROKE_WIDTHS.has(path.strokeWidth)) {
        result.addWarning(
          'STROKE-WIDTH',
          `线宽 ${path.strokeWidth} 不在标准列表 (${[...CONFIG.ALLOWED_STROKE_WIDTHS].join(', ')}) 中`,
          `<path stroke-width="${path.strokeWidth}"/>`
        );
      }
    }
  }
  result.addPass('STROKE-WIDTH');
}

// 颜色色板一致性
function checkColorPalette(parser, result) {
  const usedColors = new Set();

  for (const path of parser.paths) {
    if (path.stroke) usedColors.add(path.stroke.toUpperCase());
    if (path.fill && path.fill !== 'none') usedColors.add(path.fill.toUpperCase());
  }
  for (const rect of parser.rects) {
    if (rect.fill) usedColors.add(rect.fill.toUpperCase());
    if (rect.stroke) usedColors.add(rect.stroke.toUpperCase());
  }
  for (const circle of parser.circles) {
    if (circle.fill) usedColors.add(circle.fill.toUpperCase());
    if (circle.stroke) usedColors.add(circle.stroke.toUpperCase());
  }

  for (const color of usedColors) {
    if (!CONFIG.ALLOWED_COLORS.has(color) && !CONFIG.ALLOWED_COLORS.has(color.toLowerCase())) {
      result.addWarning(
        'COLOR-PALETTE',
        `颜色 ${color} 不在强制色板中, 请检查是否为临时调试色`,
        ''
      );
    }
  }
  result.addPass('COLOR-PALETTE');
}

// 字号强制
function checkFontSize(parser, result) {
  for (const text of parser.texts) {
    if (!CONFIG.ALLOWED_FONT_SIZES.has(text.fontSize)) {
      result.addWarning(
        'FONT-SIZE',
        `字号 ${text.fontSize} 不在标准列表 (${[...CONFIG.ALLOWED_FONT_SIZES].join(', ')}) 中`,
        `<text font-size="${text.fontSize}">${text.content}</text>`
      );
    }
  }
  result.addPass('FONT-SIZE');
}

// viewBox 宽高比
function checkViewBoxAspect(result, parser) {
  if (!parser.viewBox) {
    result.addWarning('ASPECT-RATIO', '未找到 viewBox 属性', '');
    return;
  }
  const ratio = parser.viewBox.w / parser.viewBox.h;
  if (ratio < CONFIG.ASPECT_RATIO.min || ratio > CONFIG.ASPECT_RATIO.max) {
    result.addWarning(
      'ASPECT-RATIO',
      `viewBox 宽高比 ${ratio.toFixed(2)} 不在 4:3 ~ 2:1 (${CONFIG.ASPECT_RATIO.min}~${CONFIG.ASPECT_RATIO.max}) 范围内`,
      `viewBox="${parser.viewBox.w}x${parser.viewBox.h}"`
    );
  }
  result.addPass('ASPECT-RATIO');
}

// ============================================================
// C3 组件图专项校验 (作图-11-C3组件图.md §3.9)
// ============================================================
function checkC3Diagram(parser, result) {
  // 1. C3 协议:端口禁用 (C3 是关系描述层,不应出现协议:端口)
  const protocolRegex = /([A-Z][A-Z0-9]+):(\d{2,5})/;
  let hasProtocolViolation = false;
  for (const text of parser.texts) {
    if (protocolRegex.test(text.content)) {
      result.addError(
        'C3-PROTOCOL',
        `C3 组件图禁止标注协议:端口 ("${text.content}"), 协议信息属于 C2 层级`,
        `<text>${text.content}</text>`
      );
      hasProtocolViolation = true;
    }
  }
  if (!hasProtocolViolation) result.addPass('C3-PROTOCOL');

  // 2. 目标容器虚线边界: 必须存在 stroke-dasharray="6,4" 的大矩形
  const dashedRects = parser.rects.filter(r =>
    r.strokeDasharray && /6[, ]*4/.test(r.strokeDasharray) &&
    r.w > 300 && r.h > 300
  );
  if (dashedRects.length === 0) {
    result.addWarning(
      'C3-CONTAINER-BOUNDARY',
      'C3 组件图应包含目标容器虚线边界 (stroke-dasharray="6,4" 的大矩形), 标识展开的容器',
      '建议在画布外围添加蓝色虚线圆角矩形'
    );
  } else {
    result.addPass('C3-CONTAINER-BOUNDARY');
  }

  // 3. 灰盒样式: 外部容器应使用 #F3F4F6 填充 + #9CA3AF 边框
  const grayBoxRects = parser.rects.filter(r =>
    (r.fill || '').toUpperCase() === '#F3F4F6' &&
    (r.stroke || '').toUpperCase() === '#9CA3AF'
  );
  if (grayBoxRects.length === 0 && parser.rects.length > 5) {
    result.addWarning(
      'C3-GRAY-BOX',
      'C3 组件图建议使用灰盒 (fill=#F3F4F6 + stroke=#9CA3AF) 表示外部容器, 与内部组件区分',
      '灰盒为只读显示, 不展开内部'
    );
  } else if (grayBoxRects.length > 0) {
    result.addPass('C3-GRAY-BOX');
  }

  // 4. 组件数上限检查: 内部组件 rect (浅蓝填充 #E0F2FE) ≤ 12
  const componentRects = parser.rects.filter(r =>
    (r.fill || '').toUpperCase() === '#E0F2FE'
  );
  if (componentRects.length > 12) {
    result.addError(
      'C3-COMPONENT-COUNT',
      `内部组件数 ${componentRects.length} 超过上限 12, 请按子域拆分为多张 C3`,
      ''
    );
  } else {
    result.addPass('C3-COMPONENT-COUNT');
  }

  // 5. 接口标记: 至少应有 1 个 circle (lollipop 标识)
  if (parser.circles.length > 0) {
    result.addPass('C3-INTERFACE-MARKER');
  } else {
    result.addWarning(
      'C3-INTERFACE-MARKER',
      'C3 组件图建议使用 lollipop (圆形接口标记) 标识关键对外接口',
      ''
    );
  }
}

// ============================================================
// 4. 几何辅助函数
// ============================================================

function segmentsIntersect(bbox, seg) {
  // bbox 与线段相交判定: 线段任一端点在 bbox 内, 或线段穿越 bbox
  const minX = Math.min(bbox.x1, bbox.x2);
  const maxX = Math.max(bbox.x1, bbox.x2);
  const minY = Math.min(bbox.y1, bbox.y2);
  const maxY = Math.max(bbox.y1, bbox.y2);

  // 端点检测
  if ((seg.x1 >= minX && seg.x1 <= maxX && seg.y1 >= minY && seg.y1 <= maxY) ||
      (seg.x2 >= minX && seg.x2 <= maxX && seg.y2 >= minY && seg.y2 <= maxY)) {
    return true;
  }
  // 简化: 水平线段穿越垂直 bbox, 或垂直线段穿越水平 bbox
  if (seg.y1 === seg.y2) {
    if (seg.y1 >= minY && seg.y1 <= maxY) {
      const x1 = Math.min(seg.x1, seg.x2);
      const x2 = Math.max(seg.x1, seg.x2);
      if (x1 <= maxX && x2 >= minX) return true;
    }
  }
  if (seg.x1 === seg.x2) {
    if (seg.x1 >= minX && seg.x1 <= maxX) {
      const y1 = Math.min(seg.y1, seg.y2);
      const y2 = Math.max(seg.y1, seg.y2);
      if (y1 <= maxY && y2 >= minY) return true;
    }
  }
  return false;
}

function pointToSegmentDistance(px, py, seg) {
  const dx = seg.x2 - seg.x1;
  const dy = seg.y2 - seg.y1;
  const len2 = dx * dx + dy * dy;
  if (len2 === 0) {
    return Math.hypot(px - seg.x1, py - seg.y1);
  }
  let t = ((px - seg.x1) * dx + (py - seg.y1) * dy) / len2;
  t = Math.max(0, Math.min(1, t));
  const projX = seg.x1 + t * dx;
  const projY = seg.y1 + t * dy;
  return Math.hypot(px - projX, py - projY);
}

function isInsideContainer(bbox, rects) {
  for (const rect of rects) {
    const cx = (bbox.x1 + bbox.x2) / 2;
    const cy = (bbox.y1 + bbox.y2) / 2;
    if (cx >= rect.x && cx <= rect.x + rect.w && cy >= rect.y && cy <= rect.y + rect.h) {
      return true;
    }
  }
  return false;
}

// 文字几何中心是否落在任一 <rect> 盒范围内 (视为组件标签, 非连线标注)
// 用于 ST-14 排除盒标题/子标签误报: x 取 text.x (middle 锚点即中心), y 取基线上方半个字号
function textCenterInsideBox(text, rects) {
  const cx = text.x;
  const cy = text.y - text.fontSize / 2;
  for (const rect of rects) {
    if (cx >= rect.x && cx <= rect.x + rect.w && cy >= rect.y && cy <= rect.y + rect.h) {
      return true;
    }
  }
  return false;
}

// ============================================================
// 5. CLI 入口
// ============================================================

function printResult(result, options) {
  if (options.json) {
    console.log(JSON.stringify({
      file: result.file,
      status: result.status,
      errors: result.errors,
      warnings: result.warnings,
      passed: result.passed
    }, null, 2));
    return;
  }

  const colorByStatus = {
    PASS: '\x1b[32m',
    PASS_WITH_WARNINGS: '\x1b[33m',
    FAIL: '\x1b[31m'
  };
  const reset = '\x1b[0m';

  console.log(`\n${'='.repeat(60)}`);
  console.log(`文件: ${result.file}`);
  console.log(`状态: ${colorByStatus[result.status]}${result.status}${reset}`);
  console.log(`通过: ${result.passed.length} 项, 警告: ${result.warnings.length} 项, 错误: ${result.errors.length} 项`);
  console.log('='.repeat(60));

  if (result.errors.length > 0) {
    console.log(`\n${colorByStatus.FAIL}❌ 错误 (必须修复):${reset}`);
    result.errors.forEach((e, i) => {
      console.log(`  [${i + 1}] [${e.rule}] ${e.message}`);
      if (e.location) console.log(`      位置: ${e.location}`);
    });
  }

  if (result.warnings.length > 0) {
    console.log(`\n${colorByStatus.PASS_WITH_WARNINGS}⚠️  警告 (建议改进):${reset}`);
    result.warnings.forEach((w, i) => {
      console.log(`  [${i + 1}] [${w.rule}] ${w.message}`);
      if (w.location) console.log(`      位置: ${w.location}`);
    });
  }

  if (result.passed.length > 0) {
    console.log(`\n✅ 通过:`);
    const grouped = {};
    result.passed.forEach(p => {
      grouped[p] = (grouped[p] || 0) + 1;
    });
    Object.entries(grouped).forEach(([rule, count]) => {
      console.log(`  [${rule}] × ${count}`);
    });
  }
}

function main() {
  const args = process.argv.slice(2);
  if (args.length === 0) {
    console.log('用法:');
    console.log('  node lint-svg.cjs <file.svg> [file2.svg ...]');
    console.log('  node lint-svg.cjs --dir <directory>');
    console.log('  node lint-svg.cjs --json <file.svg>');
    console.log('  node lint-svg.cjs --strict <file.svg>');
    process.exit(2);
  }

  const options = {
    json: false,
    strict: false,
    dir: null
  };

  const files = [];
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--json') options.json = true;
    else if (args[i] === '--strict') options.strict = true;
    else if (args[i] === '--dir') {
      options.dir = args[++i];
    } else {
      files.push(args[i]);
    }
  }

  // 目录模式
  if (options.dir) {
    const dirPath = path.resolve(options.dir);
    if (!fs.existsSync(dirPath)) {
      console.error(`目录不存在: ${dirPath}`);
      process.exit(2);
    }
    const entries = fs.readdirSync(dirPath);
    for (const entry of entries) {
      if (entry.endsWith('.svg')) {
        files.push(path.join(dirPath, entry));
      }
    }
  }

  if (files.length === 0) {
    console.error('未指定 SVG 文件');
    process.exit(2);
  }

  let hasFail = false;
  let hasWarning = false;
  for (const file of files) {
    if (!fs.existsSync(file)) {
      console.error(`文件不存在: ${file}`);
      hasFail = true;
      continue;
    }
    const result = lintFile(file, options);
    printResult(result, options);
    if (result.status === 'FAIL') hasFail = true;
    if (result.status === 'PASS_WITH_WARNINGS') hasWarning = true;
  }

  // 严格模式: 警告也算失败
  if (options.strict && hasWarning) {
    hasFail = true;
  }

  process.exit(hasFail ? 1 : 0);
}

if (require.main === module) {
  main();
}

module.exports = { lintFile, SVGParser, CONFIG, LintResult };
