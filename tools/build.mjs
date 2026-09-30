#!/usr/bin/env node
// Mo's Feed 建置:src/app.jsx (JSX) → app.js (純 JS,瀏覽器直接跑,不再載入 Babel)。
//
// 用法(在 repo 根目錄):
//   node tools/build.mjs          編譯並更新 index.html 裡 app.js 的快取戳記(?b=...)
//   node tools/build.mjs --check  只檢查 app.js 是不是最新、語法是否可解析(不寫檔),用於驗證
//
// esbuild 不放在 repo 裡(node_modules 有幾千個小檔,會讓 Google Drive 同步出問題)。
// 預設從 C:\repos\mosfeed-build 找(裡面 npm install esbuild 一次即可),
// 也可用環境變數 MOSFEED_BUILD_DIR 指到別處。
//
// 注意:index.html 只放每日資料(CARDS、DISCUSS_PROMPT、CAPITOL_ROSTER、CHANNELS、BRIEF_ID、APP_META);
// 元件程式在 src/app.jsx。每日排程只改 index.html,不會、也不需要跑這個建置。
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const BUILD_DIR = process.env.MOSFEED_BUILD_DIR || 'C:\\repos\\mosfeed-build';
const check = process.argv.includes('--check');

let esbuild;
try {
  esbuild = createRequire(path.join(BUILD_DIR, 'noop.js'))('esbuild');
} catch (e) {
  console.error('找不到 esbuild。請先執行:  cd ' + BUILD_DIR + ' && npm install esbuild\n(或設定 MOSFEED_BUILD_DIR)');
  process.exit(2);
}

const src = fs.readFileSync(path.join(ROOT, 'src', 'app.jsx'), 'utf8');
const out = esbuild.transformSync(src, {
  loader: 'jsx',
  jsx: 'transform',          // React.createElement / React.Fragment(React 是全域 UMD)
  format: 'iife',            // 包成 IIFE:不污染全域;index.html 的每日資料常數仍可當自由變數讀到
  target: ['safari13', 'chrome80', 'firefox78'],
  charset: 'utf8',
  legalComments: 'none',
  sourcefile: 'src/app.jsx',
});
const banner = '/* 由 tools/build.mjs 從 src/app.jsx 編譯,請勿手改。 */\n';
const js = banner + out.code;
const hash = crypto.createHash('sha1').update(js).digest('hex').slice(0, 8);
const appPath = path.join(ROOT, 'app.js');

if (check) {
  const cur = fs.existsSync(appPath) ? fs.readFileSync(appPath, 'utf8') : '';
  if (cur !== js) { console.error('app.js 不是最新(src/app.jsx 有改動但沒重新建置)'); process.exit(1); }
  console.log('app.js 是最新, hash', hash);
  process.exit(0);
}

fs.writeFileSync(appPath, js, 'utf8');

// 更新 index.html 裡 app.js 的快取戳記(只動這一個屬性,其他一概不碰)
const htmlPath = path.join(ROOT, 'index.html');
let html = fs.readFileSync(htmlPath, 'utf8');
const re = /<script src="app\.js\?b=[0-9a-f]*"><\/script>/;
if (!re.test(html)) { console.error('index.html 找不到 <script src="app.js?b=..."></script>'); process.exit(3); }
html = html.replace(re, '<script src="app.js?b=' + hash + '"></script>');
fs.writeFileSync(htmlPath, html, 'utf8');
console.log('built app.js (' + js.length + ' bytes), hash ' + hash);
