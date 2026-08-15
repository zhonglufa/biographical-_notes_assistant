/**
 * Pre-commit Hook — 保存前校验
 *
 * 功能：在 SVG 文件保存前自动运行 lint + geometry 校验，
 *       拦截不合格输出，防止问题流入仓库。
 *
 * 使用: node hooks/pre-commit.js --file=fig-xxx.svg
 *       node hooks/pre-commit.js --dir=../../design/figures
 */

const path = require('path');
const { execSync } = require('child_process');
const fs = require('fs');

// 配置
const FIGURES_DIR = path.resolve(__dirname, '../../design/figures');
const LINT_SCRIPT = path.resolve(FIGURES_DIR, 'lint-svg.cjs');
const GEOMETRY_SCRIPT = path.resolve(FIGURES_DIR, 'geometry-check.ps1');

// 解析参数
function parseArgs() {
  const args = process.argv.slice(2);
  const result = { files: [] };
  for (const arg of args) {
    if (arg.startsWith('--file=')) result.files.push(arg.slice(7));
    else if (arg.startsWith('--dir=')) result.dir = arg.slice(6);
  }
  return result;
}

// 运行 lint
function runLint(filePath) {
  console.log(`[pre-commit] 🔍 Lint: ${path.basename(filePath)}`);
  try {
    const output = execSync(`node "${LINT_SCRIPT}" "${filePath}"`, {
      encoding: 'utf-8',
      timeout: 30000,
    });
    const hasError = output.includes('ERROR') || output.includes('error');
    if (hasError) {
      console.error(`[pre-commit] ❌ Lint 失败:\n${output}`);
      return false;
    }
    console.log(`[pre-commit] ✅ Lint 通过`);
    return true;
  } catch (err) {
    console.error(`[pre-commit] ❌ Lint 异常: ${err.message}`);
    return false;
  }
}

// 运行 geometry check
function runGeometry(filePath) {
  console.log(`[pre-commit] 🔍 Geometry: ${path.basename(filePath)}`);
  try {
    const output = execSync(
      `powershell -File "${GEOMETRY_SCRIPT}" -File "${filePath}"`,
      { encoding: 'utf-8', timeout: 30000 }
    );
    const hasError = output.includes('错误') || output.includes('error') || output.includes('FAIL');
    if (hasError) {
      console.error(`[pre-commit] ❌ Geometry 失败:\n${output}`);
      return false;
    }
    console.log(`[pre-commit] ✅ Geometry 通过`);
    return true;
  } catch (err) {
    console.error(`[pre-commit] ❌ Geometry 异常: ${err.message}`);
    return false;
  }
}

// 主流程
function main() {
  const args = parseArgs();
  let files = [];

  // 收集待校验文件
  if (args.files.length > 0) {
    files = args.files.map(f =>
      path.isAbsolute(f) ? f : path.resolve(process.cwd(), f)
    );
  } else if (args.dir) {
    const dir = path.resolve(process.cwd(), args.dir);
    const svgFiles = fs.readdirSync(dir).filter(f => f.startsWith('fig-') && f.endsWith('.svg'));
    files = svgFiles.map(f => path.resolve(dir, f));
  } else {
    // 默认检查 figures 目录下所有
    const svgFiles = fs.readdirSync(FIGURES_DIR).filter(f => f.startsWith('fig-') && f.endsWith('.svg'));
    files = svgFiles.map(f => path.resolve(FIGURES_DIR, f));
  }

  if (files.length === 0) {
    console.log('[pre-commit] ⚠ 没有找到 SVG 文件');
    process.exit(0);
  }

  console.log(`[pre-commit] 📋 待校验文件: ${files.length} 个`);

  let allPassed = true;
  for (const file of files) {
    if (!fs.existsSync(file)) {
      console.warn(`[pre-commit] ⚠ 文件不存在: ${file}`);
      continue;
    }
    const lintOk = runLint(file);
    const geoOk = runGeometry(file);
    if (!lintOk || !geoOk) {
      allPassed = false;
      console.error(`[pre-commit] ❌ ${path.basename(file)}: 校验失败`);
    }
  }

  if (allPassed) {
    console.log(`[pre-commit] 🎉 全部 ${files.length} 个文件校验通过`);
    process.exit(0);
  } else {
    console.error(`[pre-commit] ❌ 存在未通过的校验，请修复后重试`);
    process.exit(1);
  }
}

main();