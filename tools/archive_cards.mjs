#!/usr/bin/env node
// Mo's Feed 晨報歸檔:把 index.html 目前的 CARDS 存成 archive/cards_YYYYMMDD.json,
// 並更新 archive/index.json(App 的「過去」分頁靠它列日期)。
//
// 每日排程用法(在 repo 根目錄,「patch 之前」跑一次):
//     node tools/archive_cards.mjs
//   此刻 index.html 還是昨天的晨報,日期取自檔內的 "updated MM/DD/YYYY",所以存下來的就是昨天那份。
//   同一天重複跑只會覆寫同一個檔,不會重複。跑完之後 commit 要一併 git add archive/
//
// 其他用法:
//     node tools/archive_cards.mjs --from-git 20260912 20260930
//   回填歷史:掃 index.html 的 git 歷史,同一天有多個 commit 時取最後一個(含事後修正版),
//   把日期落在區間內的每一天存進 archive/(只用在補檔,平常不需要)。
//
// 只用 Node 內建模組,沒有任何相依套件。
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const HTML = path.join(ROOT, 'index.html');
const DIR = path.join(ROOT, 'archive');

function parseHtml(html) {
  const dm = /updated (\d\d)\/(\d\d)\/(\d{4})/.exec(html);
  if (!dm) throw new Error('index.html 找不到 "updated MM/DD/YYYY"');
  const date = dm[3] + dm[1] + dm[2];
  const m = /const CARDS = (\[\r?\n[\s\S]*?\r?\n\]);/.exec(html);
  if (!m) throw new Error('index.html 找不到 CARDS 陣列');
  let cards;
  try { cards = JSON.parse(m[1]); }
  catch (e) { cards = JSON.parse(m[1].replace(/,\s*\]$/, ']')); }   // 手改過的舊版可能有尾逗號
  if (!Array.isArray(cards) || cards.length === 0) throw new Error('CARDS 是空的');
  return { date, cards };
}

function writeArchive(date, cards) {
  fs.mkdirSync(DIR, { recursive: true });
  // 一張卡一行,git diff 好讀
  const body = '[\n' + cards.map((c) => '  ' + JSON.stringify(c)).join(',\n') + '\n]\n';
  fs.writeFileSync(path.join(DIR, 'cards_' + date + '.json'), body, 'utf8');
}

function rebuildIndex() {
  const dates = fs.readdirSync(DIR)
    .map((f) => /^cards_(\d{8})\.json$/.exec(f))
    .filter(Boolean).map((m) => m[1]).sort();
  fs.writeFileSync(path.join(DIR, 'index.json'), JSON.stringify({ dates }, null, 1) + '\n', 'utf8');
  return dates;
}

const args = process.argv.slice(2);
if (args[0] === '--from-git') {
  const from = args[1], to = args[2];
  if (!/^\d{8}$/.test(from || '') || !/^\d{8}$/.test(to || '')) { console.error('用法: --from-git YYYYMMDD YYYYMMDD'); process.exit(2); }
  const revs = execFileSync('git', ['log', '--reverse', '--format=%H', '--', 'index.html'], { cwd: ROOT, encoding: 'utf8', maxBuffer: 1 << 28 })
    .split('\n').filter(Boolean);
  const byDate = new Map();   // 後面的 commit 覆蓋前面的(同一天以最後一版為準)
  for (const rev of revs) {
    let html;
    try { html = execFileSync('git', ['show', rev + ':index.html'], { cwd: ROOT, encoding: 'utf8', maxBuffer: 1 << 28 }); } catch (e) { continue; }
    try {
      const { date, cards } = parseHtml(html);
      if (date >= from && date <= to) byDate.set(date, { cards, rev: rev.slice(0, 7) });
    } catch (e) { /* 舊格式的版本解析不了就跳過 */ }
  }
  for (const [date, { cards, rev }] of [...byDate].sort()) {
    writeArchive(date, cards);
    console.log('archived', date, cards.length + ' cards', '(commit ' + rev + ')');
  }
  console.log('index:', rebuildIndex().length, 'days');
} else {
  const { date, cards } = parseHtml(fs.readFileSync(HTML, 'utf8'));
  writeArchive(date, cards);
  const dates = rebuildIndex();
  console.log('archived ' + date + ' (' + cards.length + ' cards); archive now has ' + dates.length + ' days');
}
