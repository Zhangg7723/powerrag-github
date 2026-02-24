#!/usr/bin/env node

/**
 * 自动修复 UmiJS Tailwind CSS 插件的已知问题
 * 在 npm install 后自动运行（通过 postinstall 脚本）
 */

const fs = require('fs');
const path = require('path');

const PLUGIN_PATH = path.join(
  __dirname,
  '../node_modules/@umijs/plugins/dist/tailwindcss.js',
);

function fixTailwindcssPlugin() {
  if (!fs.existsSync(PLUGIN_PATH)) {
    console.log('⚠️  Tailwind CSS plugin not found, skipping fix.');
    return;
  }

  let content = fs.readFileSync(PLUGIN_PATH, 'utf8');
  let modified = false;

  // 修复 1: 超时时间从 5 秒增加到 60 秒
  if (content.includes('CHECK_TIMEOUT_UNIT_SECOND = 5')) {
    content = content.replace(
      /CHECK_TIMEOUT_UNIT_SECOND = 5/g,
      'CHECK_TIMEOUT_UNIT_SECOND = 60',
    );
    modified = true;
    console.log('✓ Fixed: Increased timeout from 5s to 60s');
  } else if (content.includes('CHECK_TIMEOUT_UNIT_SECOND = 60')) {
    console.log('✓ Already fixed: Timeout is 60s');
  }

  // 修复 2: 确保输出目录存在
  const generatedDirCheck =
    /const generatedDir = .*dirname.*generatedPath.*;\s*if \(!.*existsSync.*generatedDir.*\)/s;
  if (!generatedDirCheck.test(content)) {
    // 查找 generatedDir 定义的位置
    const dirPattern =
      /(const generatedDir = \(0, import_path\.dirname\)\(generatedPath\);\s*)(const binPath)/s;
    if (dirPattern.test(content)) {
      content = content.replace(
        dirPattern,
        `$1if (!(0, import_fs.existsSync)(generatedDir)) {\n      require("fs").mkdirSync(generatedDir, { recursive: true });\n    }\n    $2`,
      );
      modified = true;
      console.log('✓ Fixed: Added directory existence check');
    }
  } else {
    console.log('✓ Already fixed: Directory check exists');
  }

  // 修复 3: --watch 改为 --watch=always
  if (content.includes('"--watch"') && !content.includes('"--watch=always"')) {
    content = content.replace(/"--watch"/g, '"--watch=always"');
    modified = true;
    console.log('✓ Fixed: Changed --watch to --watch=always');
  } else if (content.includes('"--watch=always"')) {
    console.log('✓ Already fixed: Using --watch=always');
  }

  if (modified) {
    fs.writeFileSync(PLUGIN_PATH, content, 'utf8');
    console.log('✅ Tailwind CSS plugin fixes applied successfully!');
  } else {
    console.log('✅ All fixes already applied, no changes needed.');
  }
}

try {
  fixTailwindcssPlugin();
} catch (error) {
  console.error('❌ Error fixing Tailwind CSS plugin:', error.message);
  process.exit(1);
}
