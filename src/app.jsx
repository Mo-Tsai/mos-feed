// 原始碼:src/app.jsx。編譯輸出:app.js(tools/build.mjs)。每日資料(CARDS 等)在 index.html,以全域常數讀入。
const { useState, useMemo } = React;

// ===== 共用小工具 =====
const ls = {   // localStorage 一律 try/catch 包好(無痕模式、被封鎖時會丟例外)
  get(k) { try { return localStorage.getItem(k); } catch(e) { return null; } },
  set(k, v) { try { localStorage.setItem(k, v); } catch(e) {} },
  del(k) { try { localStorage.removeItem(k); } catch(e) {} },
};
// 瀏覽器內建語音不一定存在(部分 WebView 沒有),不能直接呼叫
const HAS_TTS = typeof window !== 'undefined' && 'speechSynthesis' in window && typeof SpeechSynthesisUtterance !== 'undefined';

// ===== 主題(亮/暗):預設跟系統,手動切換存 localStorage;index.html 開頁前已先套用,避免閃白 =====
const THEME_KEY = 'mf_theme';
const THEME_BG = { light: '#f5f1ea', dark: '#0f0e0c' };
function currentTheme() { return document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light'; }
function applyTheme(t) {
  document.documentElement.setAttribute('data-theme', t);
  try { const m = document.querySelector('meta[name="theme-color"]'); if (m) m.setAttribute('content', THEME_BG[t]); } catch(e) {}
}
function useTheme() {
  const [t, setT] = useState(currentTheme);
  React.useEffect(() => {
    const obs = new MutationObserver(() => setT(currentTheme()));
    obs.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
    // 沒有手動選過就跟著系統走
    let mq = null, onChange = null;
    if (window.matchMedia) {
      mq = window.matchMedia('(prefers-color-scheme: dark)');
      onChange = (e) => { if (!ls.get(THEME_KEY)) applyTheme(e.matches ? 'dark' : 'light'); };
      if (mq.addEventListener) mq.addEventListener('change', onChange); else if (mq.addListener) mq.addListener(onChange);
    }
    return () => {
      obs.disconnect();
      if (mq && onChange) { if (mq.removeEventListener) mq.removeEventListener('change', onChange); else if (mq.removeListener) mq.removeListener(onChange); }
    };
  }, []);
  return t;
}

// ===== 對比:頻道色拿來當文字時,自動朝黑/白調到對背景 >= 4.6:1(色條、圓點仍用原色,保持辨識度) =====
const _hexRgb = (h) => [1, 3, 5].map(i => parseInt(h.slice(i, i + 2), 16));
const _lin = (c) => { c /= 255; return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4); };
const _lum = (h) => { const [r, g, b] = _hexRgb(h).map(_lin); return 0.2126 * r + 0.7152 * g + 0.0722 * b; };
function contrastRatio(a, b) { const x = _lum(a), y = _lum(b); return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05); }
const _readableCache = {};
function readableOn(hex, theme) {
  const key = hex + '|' + theme;
  if (_readableCache[key]) return _readableCache[key];
  const bg = THEME_BG[theme] || THEME_BG.light;
  const toward = theme === 'dark' ? [255, 255, 255] : [0, 0, 0];
  const base = _hexRgb(hex);
  let out = hex;
  for (let t = 0; t <= 1.0001; t += 0.04) {
    const c = '#' + base.map((v, i) => Math.round(v + (toward[i] - v) * t).toString(16).padStart(2, '0')).join('');
    out = c;
    if (contrastRatio(c, bg) >= 4.6) break;
  }
  _readableCache[key] = out;
  return out;
}

// ===== 單字翻譯快取(Map + localStorage,上限 300 筆,超過丟最舊;失敗不快取) =====
const TRANS_KEY = 'mf_trans_cache', TRANS_MAX = 300;
const _transCache = (() => {
  const m = new Map();
  try { (JSON.parse(ls.get(TRANS_KEY) || '[]') || []).forEach(p => { if (Array.isArray(p) && p.length === 2) m.set(p[0], p[1]); }); } catch(e) {}
  return m;
})();
function transGet(word) {
  const k = word.toLowerCase();
  if (!_transCache.has(k)) return null;
  const v = _transCache.get(k);
  _transCache.delete(k); _transCache.set(k, v);   // 命中就移到最新
  return v;
}
function transPut(word, val) {
  const k = word.toLowerCase();
  _transCache.delete(k); _transCache.set(k, val);
  while (_transCache.size > TRANS_MAX) _transCache.delete(_transCache.keys().next().value);
  ls.set(TRANS_KEY, JSON.stringify(Array.from(_transCache.entries())));
}

// ===== 收藏:存整張卡(每日卡片會被換掉,只存 id 會找不回來),長期保留、跟 BRIEF_ID 無關 =====
const FAV_KEY = 'mf_favs';
function loadFavs() {
  try { const a = JSON.parse(ls.get(FAV_KEY) || '[]'); return Array.isArray(a) ? a : []; } catch(e) { return []; }
}
function saveFavs(a) { ls.set(FAV_KEY, JSON.stringify(a)); }
const cardUid = (c) => (c._date || '') + '|' + c.id;

// ===== 複製為「忽視雷達池」格式(Notion 欄位:代號/公司/忽視原因/拐點證據/風險/下一個驗證點/來源/入池日/狀態) =====
// 卡片 zh 的分段標題每天寫法略有不同,這裡盡力切;切不出「忽視原因」就把整段原文放進「備註」,不丟資訊。
const RADAR_LABELS = [
  ['who', /(?:這家公司)?做什麼[:：]/],
  ['ign', /(?:為什麼被忽視|它被忽視的原因|被忽視的原因)[:：]/],
  ['chg', /(?:什麼正在改變|正在改變的是|正在改變的有[^:：]{0,12}|正在改變)[:：]/],
  ['risk', /風險與反方論點[:：]/],
];
function splitRadarZh(zh) {
  const hits = [];
  RADAR_LABELS.forEach(([k, re]) => { const m = re.exec(zh); if (m) hits.push({ k, s: m.index, e: m.index + m[0].length }); });
  hits.sort((a, b) => a.s - b.s);
  const out = { pre: (hits.length ? zh.slice(0, hits[0].s) : zh).trim() };
  hits.forEach((h, i) => { out[h.k] = zh.slice(h.e, i + 1 < hits.length ? hits[i + 1].s : zh.length).trim(); });
  return out;
}
function radarText(card) {
  const clean = (s) => (s || '').replace(/這是研究線索[，,]\s*不是投資建議。?/g, '').replace(/\s+/g, ' ').trim();
  const iso = (d8) => /^\d{8}$/.test(d8 || '') ? d8.slice(0, 4) + '-' + d8.slice(4, 6) + '-' + d8.slice(6, 8) : '';
  const stocks = card.stocks || [];
  const L = [];
  L.push('代號：' + (stocks.map(s => s.t).filter(Boolean).join('、') || '(無)'));
  const sp = splitRadarZh(card.zh || '');
  const structured = !!sp.ign;
  if (structured) {
    const who = sp.who || sp.pre;
    if (who) L.push('公司：' + clean(who));
    L.push('忽視原因：' + clean(sp.ign));
    if (sp.chg) L.push('拐點證據：' + clean(sp.chg));
    if (sp.risk) L.push('風險：' + clean(sp.risk));
  } else {
    if (stocks.length) L.push('公司：' + stocks.map(s => s.t + ' ' + (s.n || '')).join('；').trim());
    L.push('備註：' + clean(card.zh));
  }
  const vm = /下一個驗證點\s*(.+)$/.exec(card.status || '');
  if (vm) L.push('下一個驗證點：' + vm[1].trim());
  if (card.url) L.push('來源：' + card.url);
  L.push('入池日：' + (iso(card._date) || iso(metaDateIso())));
  L.push('狀態：雷達中');
  L.push('(卡片：' + [card.channel, card.tag].filter(Boolean).join('／') + ')');
  return L.join('\n');
}
function radarTextAll(cards) { return cards.map(radarText).join('\n\n---\n\n'); }
// 寫入剪貼簿:先用 Clipboard API,失敗或不支援就退回隱藏 textarea + execCommand;都失敗回 false
function copyText(text) {
  const fallback = () => {
    try {
      const ta = document.createElement('textarea');
      ta.value = text; ta.setAttribute('readonly', ''); ta.style.cssText = 'position:fixed;top:0;left:0;opacity:0;';
      document.body.appendChild(ta); ta.select(); ta.setSelectionRange(0, text.length);
      const ok = document.execCommand('copy'); document.body.removeChild(ta); return ok;
    } catch (e) { return false; }
  };
  if (navigator.clipboard && navigator.clipboard.writeText) {
    return navigator.clipboard.writeText(text).then(() => true).catch(() => fallback());
  }
  return Promise.resolve(fallback());
}
function CopyButton({ label, getText, ariaLabel, className }) {
  const [state, setState] = React.useState(null);   // null | 'ok' | 'fail'
  const timer = React.useRef(null);
  React.useEffect(() => () => clearTimeout(timer.current), []);
  const onClick = (e) => {
    e.stopPropagation();
    copyText(getText()).then(ok => {
      setState(ok ? 'ok' : 'fail');
      clearTimeout(timer.current);
      timer.current = setTimeout(() => setState(null), 2000);
    });
  };
  return (
    <button className={className || 'copy-btn'} aria-label={ariaLabel || label} onPointerDown={e => e.stopPropagation()} onClick={onClick}>
      {state === 'ok' ? '✓ 已複製' : state === 'fail' ? '複製失敗' : label}
      <span className="sr-only" aria-live="polite">{state === 'ok' ? '已複製到剪貼簿' : state === 'fail' ? '複製失敗，請再試一次' : ''}</span>
    </button>
  );
}

// ===== 日期:APP_META.updated = "updated MM/DD/YYYY" =====
function metaDateIso() {
  const m = /(\d\d)\/(\d\d)\/(\d{4})/.exec(APP_META.updated);
  return m ? m[3] + m[1] + m[2] : '';   // YYYYMMDD
}
function fmtDate(d8, withWeek) {
  const y = +d8.slice(0, 4), mo = +d8.slice(4, 6), da = +d8.slice(6, 8);
  const wd = '日一二三四五六'[new Date(y, mo - 1, da).getDay()];
  return String(mo).padStart(2, '0') + '/' + String(da).padStart(2, '0') + (withWeek ? ' 週' + wd : '');
}

// ===== AZURE TTS(依顯示語系切換嗓音) =====
let _azToken = null, _azTokenExp = 0, _azAbort = null, _azAudio = null, _azEl = null;
// 每個語系一組預設嗓音 + localStorage key,朗讀時依當下顯示語言自動挑選
const VOICE_CONF = {
  zh: { locale:'zh-TW', lsKey:'mf_azureVoice_zh', fallback:'zh-TW-HsiaoChenNeural', styleKey:'mf_azureStyle_zh',
        sysVoices:["Microsoft HsiaoChen Online (Natural) - Chinese (Taiwan)","Google 國語（臺灣）","Meijia","Tingting","Google 普通话（中国大陆）"] },
  en: { locale:'en-US', lsKey:'mf_azureVoice',    fallback:'en-US-AriaNeural',       styleKey:'mf_azureStyle_en',
        sysVoices:["Google US English","Microsoft Aria Online (Natural) - English (United States)","Microsoft Guy Online (Natural) - English (United States)","Samantha","Alex"] },
};
// 支援 express-as 語氣的嗓音(台灣腔 zh-TW 系列不支援,設了也會被忽略)
const STYLE_VOICES = new Set(['zh-CN-XiaoxiaoNeural','zh-CN-YunyangNeural','zh-CN-YunxiNeural','zh-CN-YunjianNeural',
  'en-US-AriaNeural','en-US-JennyNeural','en-US-GuyNeural','en-US-DavisNeural','en-US-TonyNeural']);

// 中文縮寫/符號的唸法對照。TTS 把 "Fed"「3.50-3.75%」「8/3」直接吐出來時最像機器人,
// 先換成人會唸的樣子,比換嗓音有感得多。
const ZH_READ_MAP = [
  [/S\s*&\s*P\s*500/gi, '標普 500'], [/S\s*&\s*P/gi, '標普'], [/&/g, '和'],
  [/\bFed\b/g, '聯準會'], [/\bFOMC\b/g, 'F O M C'], [/\bCPI\b/g, 'C P I'], [/\bPCE\b/g, 'P C E'],
  [/\bGDP\b/g, 'G D P'], [/\bETFs?\b/g, 'E T F'], [/\bEPS\b/g, 'E P S'], [/\bIPO\b/g, 'I P O'],
  [/\bREITs?\b/g, 'R E I T'], [/\bAI\b/g, 'A I'], [/\bNIM\b/g, 'N I M'], [/\bJOLTS\b/g, 'JOLTS'],
  [/\bYoY\b/gi, '年增'], [/\bQoQ\b/gi, '季增'], [/\bbps\b/gi, '個基點'],
  [/\bQ([1-4])\b/g, (m, n) => '第' + ['一','二','三','四'][n-1] + '季'],
  [/\bH([12])\b/g, (m, n) => '上下'[n-1] + '半年'],
];
function normalizeForSpeech(text, speakLang) {
  if (speakLang !== 'zh') return text;
  let t = text;
  t = t.replace(/(\d{4})-(\d{1,2})-(\d{1,2})/g, '$1年$2月$3日');   // 2026-08-02
  t = t.replace(/(\d)\s*[-–—~～]\s*(\d)/g, '$1 到 $2');            // 3.50-3.75% / 60-80%
  t = t.replace(/(\d{1,2})\/(\d{1,2})(?!\d)/g, '$1月$2日');        // 8/3
  ZH_READ_MAP.forEach(([re, to]) => { t = t.replace(re, to); });
  t = t.replace(/\b[A-Z]{2,5}\b/g, m => m.split('').join(' '));    // 股票代號逐字母唸,AHRT → A H R T
  return t;
}
// 依句號切句,句與句之間插 break,讓語氣有停頓、不會一路衝到底
function _splitSentences(text) {
  const out = []; let cur = '';
  for (const ch of text) {
    cur += ch;
    if ('。！？!?；;'.indexOf(ch) >= 0) { out.push(cur); cur = ''; }
  }
  if (cur.trim()) out.push(cur);
  return out.filter(s => s.trim());
}
function speakLangOf(card, lang) { return lang === "en" ? "en" : "zh"; }
function speakTextOf(card, lang) {
  const L = speakLangOf(card, lang);
  if (L === "en") return card.en || "";
  return card.zh;
}
function _xmlEsc(s) { return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
async function _getAzToken(key, region, signal) {
  const now = Date.now();
  if (_azToken && now < _azTokenExp) return _azToken;
  const res = await fetch(`https://${region}.api.cognitive.microsoft.com/sts/v1.0/issueToken`, { method:'POST', headers:{'Ocp-Apim-Subscription-Key':key}, signal });
  if (!res.ok) throw new Error('Token ' + res.status);
  _azToken = await res.text();
  _azTokenExp = now + 9*60*1000;
  return _azToken;
}
// 持久播放器:iOS 只放行「使用者手勢解鎖過的元素」。連續播放每張卡若都 new Audio(),
// 第二張起就不是手勢觸發、會被 iOS 擋下 → 停播。改成同一顆元素換 src 續播就不會被擋。
function _azPlayer() {
  if (!_azEl) { _azEl = new Audio(); _azEl.preload = 'auto'; }
  return _azEl;
}
const _SILENT_WAV = 'data:audio/wav;base64,UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA';
function azureUnlock() {   // 必須在點擊/按鍵等使用者手勢裡呼叫
  try {
    const a = _azPlayer();
    if (a._unlocked) return;
    a.src = _SILENT_WAV;
    const p = a.play();
    if (p && p.then) p.then(() => { a._unlocked = true; }).catch(() => {});
  } catch(e) {}
}
function azureStop() {
  if (_azAbort) { _azAbort.abort(); _azAbort = null; }
  if (_azAudio) {
    const a = _azAudio; _azAudio = null;
    try { a.onended = null; a.onerror = null; a.pause(); } catch(e) {}
    if (a.src && a.src.indexOf('blob:') === 0) { try { URL.revokeObjectURL(a.src); } catch(e) {} }
  }
  if (HAS_TTS) { try { speechSynthesis.cancel(); } catch(e) {} }
}
// 只合成、不播放:回傳音訊 blob URL。連續播放靠它「唸這張的同時預抓下一張」,
// 唸完才能零延遲接播 — iOS 背景會凍結 timer 與網路,唸完後再打 API 就來不及了。
async function _azSynthUrl(text, { rate='0%', speakLang='en', tailMs=0, signal }={}) {
  const key = ls.get('mf_azureKey') || '';
  if (!key) return null;
  const region = ls.get('mf_azureRegion') || 'eastus';
  const conf = VOICE_CONF[speakLang] || VOICE_CONF.en;
  const voice = ls.get(conf.lsKey) || conf.fallback;
  const token = await _getAzToken(key, region, signal);
  const style = ls.get(conf.styleKey) || '';
  const useStyle = style && STYLE_VOICES.has(voice);
  const body = _splitSentences(text).map(_xmlEsc).join(`<break time='260ms'/>`);
  const inner = `<prosody rate='${rate}'>${body}</prosody>`;
  const styled = useStyle ? `<mstts:express-as style='${style}'>${inner}</mstts:express-as>` : inner;
  // xml:lang 跟著嗓音本身的 locale 走(選了大陸腔就該是 zh-CN,不是介面的 zh-TW)
  const vLocale = (voice.match(/^[a-z]{2}-[A-Z]{2}/) || [conf.locale])[0];
  // 卡與卡之間的停頓直接燒進音檔尾端:背景時 setTimeout 會被 iOS 凍結,不能靠 timer 停頓
  const silence = tailMs > 0 ? `<mstts:silence type='Tailing-exact' value='${tailMs}ms'/>` : '';
  const ssml = `<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xmlns:mstts='http://www.w3.org/2001/mstts' xml:lang='${vLocale}'><voice name='${voice}'>${silence}${styled}</voice></speak>`;
  const res = await fetch(`https://${region}.tts.speech.microsoft.com/cognitiveservices/v1`, {
    method:'POST', signal,
    headers:{'Authorization':'Bearer '+token,'Content-Type':'application/ssml+xml','X-Microsoft-OutputFormat':'audio-16khz-128kbitrate-mono-mp3'},
    body:ssml
  });
  if (!res.ok) throw new Error('TTS ' + res.status);
  const blob = await res.blob();
  return URL.createObjectURL(blob);
}
async function azureSpeak(text, { rate='0%', speakLang='en', tailMs=0, preUrl=null, onStart, onEnd, onError }={}) {
  if (!preUrl && !(ls.get('mf_azureKey') || '')) return false;
  azureStop();
  const ctrl = new AbortController(); _azAbort = ctrl;
  try {
    const url = preUrl || await _azSynthUrl(text, { rate, speakLang, tailMs, signal: ctrl.signal });
    if (!url) return false;
    if (ctrl.signal.aborted) { try { URL.revokeObjectURL(url); } catch(e) {} return true; }
    const audio = _azPlayer();
    audio.src = url;
    _azAudio = audio;
    if (onStart) onStart(audio);
    audio.onended = () => { URL.revokeObjectURL(url); audio.onended = null; audio.onerror = null; if (_azAudio === audio) _azAudio = null; if (onEnd) onEnd(); };
    audio.onerror = () => { URL.revokeObjectURL(url); audio.onended = null; audio.onerror = null; if (_azAudio === audio) _azAudio = null; if (onError) onError(); };
    await audio.play();
    return true;
  } catch(e) {
    if (e.name === 'AbortError') return true;
    _azToken = null;
    return false;   // 不呼叫 onError:讓 speakSmart 退回瀏覽器 TTS 接手,連續播放不因 Azure 失敗而中斷
  }
}

// 預先合成下一張的音訊(不播放、不動當前播放的 abort controller);失敗回 null,播放時會再試或退回瀏覽器 TTS
async function speakPrefetch(rawText, { speakLang='zh', azRate='0%', tailMs=0 }={}) {
  try { return await _azSynthUrl(normalizeForSpeech(rawText, speakLang), { rate: azRate, speakLang, tailMs }); }
  catch(e) { _azToken = null; return null; }
}

// 統一朗讀入口:Azure 優先,沒 key 或失敗就退回瀏覽器 TTS;兩者都依 speakLang 挑對應語系嗓音
async function speakSmart(rawText, { speakLang='zh', azRate='0%', sysRate=1.0, tailMs=0, preUrl=null, onStart, onEnd, onError }={}) {
  const conf = VOICE_CONF[speakLang] || VOICE_CONF.en;
  const text = normalizeForSpeech(rawText, speakLang);
  const ok = await azureSpeak(text, { rate:azRate, speakLang, tailMs, preUrl, onStart, onEnd, onError });
  if (ok) return;
  if (!HAS_TTS) { if (onError) onError(); return; }   // 沒有瀏覽器語音:不丟例外,交給呼叫端收尾
  speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(text);
  u.lang = conf.locale; u.rate = sysRate; u.pitch = 1.0; u.volume = 1.0;
  const pick = () => {
    const voices = speechSynthesis.getVoices();
    const byName = conf.sysVoices.map(n => voices.find(v => v.name === n)).find(Boolean);
    const norm = s => (s || '').replace('_','-').toLowerCase();
    const byLang = voices.find(v => norm(v.lang) === conf.locale.toLowerCase())
                || voices.find(v => norm(v.lang).startsWith(conf.locale.slice(0,2)));
    const picked = byName || byLang;
    if (picked) u.voice = picked;
  };
  if (speechSynthesis.getVoices().length > 0) pick();
  else await new Promise(r => { speechSynthesis.onvoiceschanged = () => { pick(); speechSynthesis.onvoiceschanged = null; r(); }; setTimeout(r, 600); });
  u.onend = () => { if (onEnd) { if (tailMs > 0) setTimeout(onEnd, tailMs); else onEnd(); } };   // 瀏覽器 TTS 沒有音檔尾端靜音,停頓用 timer 補(僅前景有效)
  u.onerror = () => { if (onError) onError(); };
  if (onStart) onStart(null);
  speechSynthesis.speak(u);
}

// 「資金流向」「政要績效」是特殊分頁,不吃 CARDS、卡片版型完全不適用;「收藏」「過去」吃自己的卡片來源
const FLOW_TAB = "資金流向", PERF_TAB = "政要績效", FAV_TAB = "收藏", PAST_TAB = "過去";
const TODAY_SUBS = ["全部", ...CHANNELS.map(c => c.key), FLOW_TAB, PERF_TAB, FAV_TAB, PAST_TAB];

const lsKeyFor = (sub) => "mosfeed_" + BRIEF_ID + "_" + sub;

function WordPopup({ popup, onSpeak }) {
  if (!popup) return null;
  const popupX = Math.min(popup.x, window.innerWidth - 270);
  const popupY = popup.y + 120 > window.innerHeight ? popup.y - 80 : popup.y;
  return ReactDOM.createPortal(
    <div className="word-popup" role="dialog" aria-label="單字翻譯" style={{ left: popupX + "px", top: popupY + "px" }} onClick={e => e.stopPropagation()}>
      <div className="word-popup-word">
        {popup.word}
        <button className="speak-btn" aria-label={"播放發音：" + popup.word} onClick={() => onSpeak(popup.word)} title="播放發音">🔊</button>
      </div>
      <div className="word-popup-trans">{popup.loading ? "翻譯中..." : popup.translation}</div>
      <div style={{ fontFamily:"'Courier New',monospace", fontSize:"11px", color:"var(--text-tertiary)", marginTop:"8px" }}>powered by MyMemory · 翻譯僅供參考</div>
    </div>,
    document.body
  );
}

function CardView({ card, idx, total, onManualSpeak, isFav, onToggleFav, showCopy }) {
  const [lang, setLang] = useState(null);
  const [popup, setPopup] = useState(null);
  const [speaking, setSpeaking] = useState(false);
  const abortRef = React.useRef(null);
  const audioRef = React.useRef(null);
  const toggle = (target) => setLang(lang === target ? null : target);
  const isOpen = lang !== null;
  const theme = useTheme();
  const cc = readableOn(card.color, theme);   // 頻道色當文字時用的版本(對比 >= 4.6);色條/圓點仍用原色
  const showDate = card._date && card._date !== metaDateIso();

  // 英文展開區高度:依實際內容(scrollHeight)量,不寫死上限;內容或寬度變動時重量
  const enOuterRef = React.useRef(null), enInnerRef = React.useRef(null);
  const [enH, setEnH] = useState(0);
  React.useLayoutEffect(() => {
    const outer = enOuterRef.current, inner = enInnerRef.current;
    if (!outer) return;
    const measure = () => setEnH(outer.scrollHeight);
    measure();
    let ro = null;
    if (window.ResizeObserver && inner) { ro = new ResizeObserver(measure); ro.observe(inner); }
    window.addEventListener('resize', measure);
    return () => { if (ro) ro.disconnect(); window.removeEventListener('resize', measure); };
  }, [card.en, isOpen]);

  // 單字發音永遠是英文(點的是英文原文裡的單字)
  const speakWord = React.useCallback((word) => {
    azureUnlock();
    speakSmart(word, { speakLang:'en', azRate:'-15%', sysRate:0.82 });
  }, []);

  // 朗讀全文:語系跟著畫面走 — 沒展開=中文主文、展開 English=英文
  const speakAll = React.useCallback(async (e) => {
    e.stopPropagation();
    if (speaking) { azureStop(); audioRef.current = null; setSpeaking(false); return; }
    if (onManualSpeak) onManualSpeak();   // 手動朗讀時先停掉連續播放,避免兩個聲音疊在一起
    azureUnlock();
    setSpeaking(true);
    const L = speakLangOf(card, lang);
    await speakSmart(speakTextOf(card, lang), {
      speakLang: L,
      azRate: L === 'zh' ? '-8%' : '-5%',
      sysRate: L === 'zh' ? 0.95 : 0.88,
      onStart: (audio) => { audioRef.current = audio; },
      onEnd: () => { audioRef.current = null; setSpeaking(false); },
      onError: () => { audioRef.current = null; setSpeaking(false); }
    });
  }, [card, lang, speaking, onManualSpeak]);

  const speakingRef = React.useRef(false);
  React.useEffect(() => { speakingRef.current = speaking; }, [speaking]);

  // 換卡時關掉 popup 與翻譯請求;只有「手動朗讀中」才停聲音,不然會誤殺連續播放
  React.useEffect(() => {
    return () => {
      if (speakingRef.current) { azureStop(); }
      audioRef.current = null;
      setSpeaking(false);
      setPopup(null);
      if (abortRef.current) abortRef.current.abort();
    };
  }, [cardUid(card)]);

  const handleWordClick = React.useCallback(async (e, rawWord) => {
    e.stopPropagation();
    const clean = rawWord.replace(/[^a-zA-Z'-]/g, "");
    if (!clean || clean.length < 2) return;
    // Abort previous in-flight request
    if (abortRef.current) abortRef.current.abort();
    const rect = e.target.getBoundingClientRect();
    const cached = transGet(clean);   // 同字不重打 MyMemory
    if (cached) { setPopup({ word: clean, x: rect.left, y: rect.bottom + 6, translation: cached, loading: false }); return; }
    const ctrl = new AbortController();
    abortRef.current = ctrl;
    setPopup({ word: clean, x: rect.left, y: rect.bottom + 6, translation: null, loading: true });
    try {
      const res = await fetch("https://api.mymemory.translated.net/get?q=" + encodeURIComponent(clean) + "&langpair=en|zh-TW", { signal: ctrl.signal });
      const data = await res.json();
      const t = data && data.responseData && data.responseData.translatedText;
      const good = res.ok && data && String(data.responseStatus) === "200" && t && !/MYMEMORY WARNING|INVALID|QUERY LENGTH/i.test(t);
      if (good) transPut(clean, t);   // 失敗不快取,下次點還會重試
      setPopup(p => p && p.word === clean ? { ...p, translation: good ? t : "(翻譯失敗)", loading: false } : p);
    } catch (err) {
      if (err.name !== "AbortError") {
        setPopup(p => p && p.word === clean ? { ...p, translation: "(翻譯失敗)", loading: false } : p);
      }
    }
  }, []);

  // Close popup on outside click
  React.useEffect(() => {
    if (!popup) return;
    const close = () => setPopup(null);
    const timer = setTimeout(() => window.addEventListener("click", close), 10);
    return () => { clearTimeout(timer); window.removeEventListener("click", close); };
  }, [popup]);

  const words = useMemo(() => (card.en || "").split(/(\s+)/).map((chunk, i) => {
    if (/^\s+$/.test(chunk)) return chunk;
    return <span key={i} className="clickable-word" onPointerDown={e => e.stopPropagation()} onClick={(e) => handleWordClick(e, chunk)}>{chunk}</span>;
  }), [card.en, handleWordClick]);

  const monoLabel = { fontFamily:"'Courier New',monospace", fontSize:"11px", letterSpacing:"0.12em", textTransform:"uppercase" };

  return (
    <div style={{ padding:"10px 32px 32px" }}>
      <div style={{ height:"2px", background:card.color, opacity:0.6, margin:"-10px -32px 14px", width:"calc(100% + 64px)" }} />
      <div style={{ display:"flex", alignItems:"center", flexWrap:"wrap", gap:"4px 10px", marginBottom:"10px" }}>
        <span style={{ display:"inline-block", width:"18px", height:"1px", background:card.color, flexShrink:0 }} />
        <span style={{ ...monoLabel, color:cc }}>{card.channel}</span>
        <span style={{ ...monoLabel, color:"var(--text-tertiary)" }}>{card.tag}</span>
        {showDate && <span style={{ ...monoLabel, color:"var(--text-tertiary)", border:"1px solid var(--divider)", padding:"0 6px" }}>{fmtDate(card._date)}</span>}
        <span style={{ marginLeft:"auto", display:"flex", alignItems:"center", gap:"2px" }}>
          <span style={{ ...monoLabel, color:"var(--text-tertiary)" }}>{ {zh:"中文",en:"EN"}[speakLangOf(card, lang)] }</span>
          {showCopy && <CopyButton label="複製這張" ariaLabel="複製這張為雷達池格式" getText={() => radarText(card)} />}
          {onToggleFav && (
            <button className={"speak-btn" + (isFav ? " active" : "")} aria-label={isFav ? "取消收藏" : "加入收藏"} aria-pressed={!!isFav} title={isFav ? "取消收藏" : "加入收藏"}
              onPointerDown={e => e.stopPropagation()} onClick={e => { e.stopPropagation(); onToggleFav(card); }}>{isFav ? "★" : "☆"}</button>
          )}
          <button className={"speak-btn" + (speaking ? " active" : "")} aria-label={speaking ? "停止朗讀" : "朗讀這張卡"} onPointerDown={e => e.stopPropagation()} onClick={speakAll} title={speaking ? "停止朗讀" : "朗讀（依目前顯示語言）"}>{speaking ? "■" : "🔊"}</button>
        </span>
      </div>
      <p style={{ fontFamily:"system-ui,-apple-system,'PingFang TC','Hiragino Sans',sans-serif", fontSize:"19px", lineHeight:1.9, color:"var(--text)", margin:0, maxWidth:"36ch", fontWeight:400, letterSpacing:"0.01em" }}>{card.zh}</p>
      {card.stocks && card.stocks.length > 0 && (
        <div style={{ marginTop:"16px", paddingTop:"12px", borderTop:"1px dashed var(--divider)", display:"flex", flexDirection:"column", gap:"7px" }}>
          <span style={{ ...monoLabel, letterSpacing:"0.14em", color:"var(--text-tertiary)" }}>相關個股</span>
          {card.stocks.map(s => (
            <a key={s.t} href={"https://www.tradingview.com/symbols/" + s.t + "/"} target="_blank" rel="noopener noreferrer" onPointerDown={e => e.stopPropagation()} onClick={e => e.stopPropagation()} style={{ display:"flex", alignItems:"baseline", gap:"12px", textDecoration:"none" }}>
              <span style={{ fontFamily:"'Courier New',monospace", fontSize:"12px", fontWeight:700, letterSpacing:"0.08em", color:cc, minWidth:"56px", flexShrink:0 }}>{s.t}</span>
              <span style={{ fontFamily:"system-ui,-apple-system,'PingFang TC',sans-serif", fontSize:"12.5px", lineHeight:1.6, color:"var(--text-secondary)", fontWeight:300 }}>{s.n}</span>
            </a>
          ))}
        </div>
      )}
      <WordPopup popup={popup} onSpeak={speakWord} />
      <div ref={enOuterRef} aria-hidden={!isOpen} style={{ overflow:"hidden", maxHeight:isOpen ? (enH + 2) + "px" : "0px", transition:"max-height 0.45s cubic-bezier(0.4,0,0.2,1)" }}>
        <div ref={enInnerRef} style={{ marginTop:"16px", paddingTop:"14px", borderTop:"1px solid var(--divider)" }}>
          <p style={{ fontFamily:"Georgia,'Times New Roman',serif", fontSize:"16px", lineHeight:1.8, color:"var(--text-secondary)", margin:0, maxWidth:"52ch", letterSpacing:"-0.01em" }}>{words}</p>
        </div>
      </div>
      <div className="expand-row" style={{ marginTop:"6px" }}>
        <button type="button" className="text-btn" aria-expanded={isOpen} onPointerDown={e => e.stopPropagation()} onClick={e => { e.stopPropagation(); toggle("en"); }}
          style={{ ...monoLabel, letterSpacing:"0.1em", color: lang==="en" ? "var(--text-secondary)" : "var(--text-tertiary)" }}>{lang==="en" ? "close ↑" : "English ↓"}</button>
        {card.url && (<a href={card.url} target="_blank" rel="noopener noreferrer" onPointerDown={e => e.stopPropagation()} onClick={e => e.stopPropagation()} className="source-link">source ↗</a>)}
      </div>
      {card.status && (
        <div style={{ marginTop:"12px", border:"1px solid "+card.color, padding:"10px 14px", display:"flex", alignItems:"center", gap:"10px" }}>
          <span style={{ width:"6px", height:"6px", borderRadius:"50%", background:card.color, flexShrink:0 }} />
          <span style={{ ...monoLabel, letterSpacing:"0.1em", color:cc }}>{card.status}</span>
        </div>
      )}
      <div style={{ position:"relative", marginTop:"16px" }}>
        <div style={{ height:"1px", background:"var(--divider)" }} />
        <div style={{ position:"absolute", top:0, left:0, height:"1px", background:"var(--text-tertiary)", width:((idx+1)/total*100)+"%", transition:"width 0.3s" }} />
      </div>
    </div>
  );
}

function EndScreen({ onPrev, onTop, showDiscuss = true }) {
  const [copied, setCopied] = React.useState(false);
  const copyPrompt = () => {
    const done = () => { setCopied(true); setTimeout(() => setCopied(false), 2000); };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(DISCUSS_PROMPT).then(done).catch(() => {});
    } else {
      const ta = document.createElement("textarea");
      ta.value = DISCUSS_PROMPT; document.body.appendChild(ta); ta.select();
      document.execCommand("copy"); document.body.removeChild(ta); done();
    }
  };
  return (
    <div className="end-screen">
      <p style={{ fontFamily:"'Courier New',monospace", fontSize:"12px", letterSpacing:"0.14em", color:"var(--text-tertiary)", textTransform:"uppercase" }}>end of brief</p>
      <div style={{ display:"flex", gap:"12px", flexWrap:"wrap", justifyContent:"center" }}>
        <button className="end-btn" onClick={onPrev}>← Prev</button>
        <button className="end-btn" onClick={onTop}>⤒ 回第一張</button>
        {showDiscuss && <button className="end-btn" onClick={copyPrompt}>{copied ? "✓ 已複製" : "跟 Claude 討論"}</button>}
      </div>
      {showDiscuss && <p style={{ fontFamily:"'Courier New',monospace", fontSize:"11px", letterSpacing:"0.1em", color:"var(--text-tertiary)", maxWidth:"32ch", textAlign:"center", lineHeight:1.8 }}>複製今日摘要 prompt，貼進 Claude 開始復盤</p>}
    </div>
  );
}

function SettingsPanel({ open, onClose }) {
  const [key, setKey] = React.useState(() => ls.get('mf_azureKey') || '');
  const [region, setRegion] = React.useState(() => ls.get('mf_azureRegion') || 'eastus');
  const [voice, setVoice] = React.useState(() => ls.get('mf_azureVoice') || 'en-US-AriaNeural');
  const [voiceZh, setVoiceZh] = React.useState(() => ls.get('mf_azureVoice_zh') || 'zh-TW-HsiaoChenNeural');
  const [styleZh, setStyleZh] = React.useState(() => ls.get('mf_azureStyle_zh') || '');
  const [status, setStatus] = React.useState('');
  const save = () => {
    ls.set('mf_azureKey', key);
    ls.set('mf_azureRegion', region);
    ls.set('mf_azureVoice', voice);
    ls.set('mf_azureVoice_zh', voiceZh);
    ls.set('mf_azureStyle_zh', styleZh);
    _azToken = null;
  };
  const handleSave = () => { save(); setStatus('已儲存'); setTimeout(() => setStatus(''), 2000); };
  const handleTest = async () => {
    save(); setStatus('測試中…');
    // 用真實晨報句型試聽,才聽得出縮寫與數字唸法的差別
    const demo = normalizeForSpeech('聯準會以 9 比 3 維持利率在 3.50-3.75%，市場給 9 月升息約 60-80% 機率。忽視雷達今天鎖定 AHRT，8/5 公布 Q2 財報。', 'zh');
    const ok = await azureSpeak(demo, {
      speakLang: 'zh',
      onEnd: () => setStatus('✓ 連線成功'),
      onError: (e) => setStatus('✗ ' + (e?.message || '失敗'))
    });
    if (!ok) setStatus('✗ 請先填入 Azure Key');
  };
  if (!open) return null;
  return ReactDOM.createPortal(
    <>
      <div style={{ position:'fixed',inset:0,zIndex:149 }} onClick={onClose} />
      <div style={{ position:'fixed',top:0,right:0,bottom:0,width:'252px',background:'var(--bg-elevated)',borderLeft:'1px solid var(--divider)',zIndex:150,padding:'20px 18px',display:'flex',flexDirection:'column',gap:'14px',overflowY:'auto' }}>
        <div style={{ display:'flex',alignItems:'center',justifyContent:'space-between',marginBottom:'4px' }}>
          <span style={{ fontFamily:"'Courier New',monospace",fontSize:'11px',letterSpacing:'0.18em',textTransform:'uppercase',color:'var(--text-tertiary)' }}>Azure TTS 設定</span>
          <button onClick={onClose} aria-label="關閉設定" className="icon-btn" style={{ fontSize:'14px' }}>✕</button>
        </div>
        <div>
          <div style={{ fontFamily:"'Courier New',monospace",fontSize:'11px',letterSpacing:'0.14em',textTransform:'uppercase',color:'var(--text-tertiary)',marginBottom:'5px' }}>Subscription Key</div>
          <input type="password" className="az-input" value={key} onChange={e=>setKey(e.target.value)} placeholder="貼上 Azure Key…" />
        </div>
        <div>
          <div style={{ fontFamily:"'Courier New',monospace",fontSize:'11px',letterSpacing:'0.14em',textTransform:'uppercase',color:'var(--text-tertiary)',marginBottom:'5px' }}>Region</div>
          <input className="az-input" value={region} onChange={e=>setRegion(e.target.value)} placeholder="eastus" />
        </div>
        <div>
          <div style={{ fontFamily:"'Courier New',monospace",fontSize:'11px',letterSpacing:'0.14em',textTransform:'uppercase',color:'var(--text-tertiary)',marginBottom:'5px' }}>中文嗓音（主畫面 / 連續播放）</div>
          <select className="az-input" value={voiceZh} onChange={e=>setVoiceZh(e.target.value)} style={{ cursor:'pointer' }}>
            <option value="zh-TW-HsiaoChenNeural">曉臻（女）台灣腔・自然</option>
            <option value="zh-TW-HsiaoYuNeural">曉雨（女）台灣腔・清亮</option>
            <option value="zh-TW-YunJheNeural">雲哲（男）台灣腔・沉穩</option>
            <option value="zh-CN-XiaoxiaoNeural">曉曉（女）大陸腔・可調語氣</option>
            <option value="zh-CN-YunyangNeural">雲揚（男）大陸腔・專業播報</option>
            <option value="zh-CN-YunxiNeural">雲希（男）大陸腔・可調語氣</option>
          </select>
        </div>
        <div>
          <div style={{ fontFamily:"'Courier New',monospace",fontSize:'11px',letterSpacing:'0.14em',textTransform:'uppercase',color:'var(--text-tertiary)',marginBottom:'5px' }}>中文語氣</div>
          <select className="az-input" value={styleZh} onChange={e=>setStyleZh(e.target.value)} style={{ cursor:'pointer' }}>
            <option value="">一般</option>
            <option value="newscast">新聞播報</option>
            <option value="chat">聊天（放鬆）</option>
            <option value="gentle">溫柔</option>
            <option value="serious">嚴肅</option>
          </select>
          <div style={{ fontFamily:"'Courier New',monospace",fontSize:'11px',color:'var(--text-tertiary)',lineHeight:1.6,marginTop:'4px' }}>只有大陸腔嗓音支援語氣；<br/>台灣腔會忽略這一項</div>
        </div>
        <div>
          <div style={{ fontFamily:"'Courier New',monospace",fontSize:'11px',letterSpacing:'0.14em',textTransform:'uppercase',color:'var(--text-tertiary)',marginBottom:'5px' }}>English Voice</div>
          <select className="az-input" value={voice} onChange={e=>setVoice(e.target.value)} style={{ cursor:'pointer' }}>
            <option value="en-US-AriaNeural">Aria（女）自然流暢</option>
            <option value="en-US-JennyNeural">Jenny（女）清晰</option>
            <option value="en-US-GuyNeural">Guy（男）沉穩</option>
            <option value="en-US-DavisNeural">Davis（男）個性</option>
            <option value="en-US-TonyNeural">Tony（男）自信</option>
          </select>
        </div>
        <div style={{ display:'flex',gap:'8px' }}>
          <button onClick={handleSave} style={{ flex:1,padding:'12px 0',background:'none',border:'1px solid var(--divider)',color:'var(--text-tertiary)',fontFamily:"'Courier New',monospace",fontSize:'11px',letterSpacing:'0.12em',textTransform:'uppercase',cursor:'pointer' }}>儲存</button>
          <button onClick={handleTest} style={{ flex:1,padding:'12px 0',background:'none',border:'1px solid var(--text-secondary)',color:'var(--text-secondary)',fontFamily:"'Courier New',monospace",fontSize:'11px',letterSpacing:'0.12em',textTransform:'uppercase',cursor:'pointer' }}>測試</button>
        </div>
        {status && <div style={{ fontFamily:"'Courier New',monospace",fontSize:'11px',color:'var(--text-tertiary)',letterSpacing:'0.1em' }}>{status}</div>}
        <div style={{ marginTop:'auto',fontFamily:"'Courier New',monospace",fontSize:'11px',color:'var(--text-tertiary)',lineHeight:1.7,paddingTop:'8px',borderTop:'1px solid var(--divider)' }}>Key 存於 localStorage<br/><b>沒填 Key 會退回瀏覽器內建語音，<br/>那個聽起來就是很機械。</b><br/>要好聽請填 Azure Key。<br/><br/>朗讀語系跟著畫面走：<br/>主文中文→中文嗓音<br/>展開 English→英文嗓音</div>
      </div>
    </>,
    document.body
  );
}

function ThemeToggle() {
  const theme = useTheme();
  const dark = theme === 'dark';
  const [settingsOpen, setSettingsOpen] = React.useState(false);
  const toggle = () => { const next = dark ? 'light' : 'dark'; applyTheme(next); ls.set(THEME_KEY, next); };
  return (
    <>
      <button className="theme-toggle" style={{ right:'48px' }} onClick={toggle} aria-label={dark ? "切換為亮色模式" : "切換為深色模式"} title={dark ? "切換為亮色模式" : "切換為深色模式"}>{dark ? "○" : "●"}</button>
      <button className="theme-toggle" style={{ right:'4px' }} onClick={() => setSettingsOpen(o => !o)} aria-label="語音設定" aria-expanded={settingsOpen} title="語音設定">⚙</button>
      <SettingsPanel open={settingsOpen} onClose={() => setSettingsOpen(false)} />
    </>
  );
}

// ===== 資金流向(TradingView 官方嵌入元件,即時資料,每日排程不需更新) =====
function HeatmapView() {
  const ref = React.useRef(null);
  React.useEffect(() => {
    const container = ref.current;
    if (!container) return;
    const build = () => {
      const dark = document.documentElement.getAttribute("data-theme") === "dark";
      container.innerHTML = "";
      const inner = document.createElement("div");
      inner.className = "tradingview-widget-container__widget";
      inner.style.height = "100%";
      const script = document.createElement("script");
      script.src = "https://s3.tradingview.com/external-embedding/embed-widget-stock-heatmap.js";
      script.async = true;
      script.innerHTML = JSON.stringify({
        dataSource: "SPX500", grouping: "sector",
        blockSize: "market_cap_basic", blockColor: "change",
        locale: "zh_TW", colorTheme: dark ? "dark" : "light",
        hasTopBar: false, isDataSetEnabled: false, isZoomEnabled: true,
        hasSymbolTooltip: true, isMonoSize: false,
        width: "100%", height: "100%"
      });
      container.appendChild(inner);
      container.appendChild(script);
    };
    build();
    const obs = new MutationObserver(build);
    obs.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
    return () => { obs.disconnect(); container.innerHTML = ""; };
  }, []);
  return (
    <div style={{ height:"100%", display:"flex", flexDirection:"column", padding:"12px 16px 16px" }}>
      <div style={{ display:"flex", alignItems:"baseline", justifyContent:"space-between", padding:"0 16px 10px" }}>
        <span style={{ fontFamily:"'Courier New',monospace", fontSize:"11px", letterSpacing:"0.18em", textTransform:"uppercase", color:"var(--text-tertiary)" }}>S&P 500 · 即時資金流向</span>
        <a href="https://finviz.com/map?t=sec&st=d1" target="_blank" rel="noopener noreferrer" className="source-link">Finviz 完整版 ↗</a>
      </div>
      <div className="tradingview-widget-container" ref={ref} style={{ flex:1, minHeight:0 }} />
    </div>
  );
}

// ===== 政要績效(TradingView 官方嵌入元件,即時資料,每日排程不需更新) =====
// NANC = 民主黨籍國會申報交易 ETF、GOP = 共和黨籍(原 KRUZ,2025-03-21 改代號),兩檔都依 STOCK Act
// 申報建倉;拿它們跟 SPY 比,就是「照著政要申報買」的真實長期績效,不必自己算、也不會過期。
function PerfView() {
  const ref = React.useRef(null);
  React.useEffect(() => {
    const container = ref.current;
    if (!container) return;
    const build = () => {
      const dark = document.documentElement.getAttribute("data-theme") === "dark";
      container.innerHTML = "";
      const inner = document.createElement("div");
      inner.className = "tradingview-widget-container__widget";
      inner.style.height = "100%";
      const script = document.createElement("script");
      script.src = "https://s3.tradingview.com/external-embedding/embed-widget-symbol-overview.js";
      script.async = true;
      script.innerHTML = JSON.stringify({
        symbols: [["民主黨 NANC", "CBOE:NANC|12M"], ["共和黨 GOP", "CBOE:GOP|12M"], ["標普500 SPY", "AMEX:SPY|12M"]],
        chartOnly: false, locale: "zh_TW", colorTheme: dark ? "dark" : "light",
        autosize: true, showVolume: false, showMA: false,
        hideDateRanges: false, hideMarketStatus: true, hideSymbolLogo: false,
        scalePosition: "right", scaleMode: "Percentage",
        fontSize: "10", noTimeScale: false, valuesTracking: "1",
        changeMode: "price-and-percent", chartType: "area"
      });
      container.appendChild(inner);
      container.appendChild(script);
    };
    build();
    const obs = new MutationObserver(build);
    obs.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
    return () => { obs.disconnect(); container.innerHTML = ""; };
  }, []);
  const R = CAPITOL_ROSTER;
  const theme = useTheme();
  const cName = readableOn('#B5654D', theme), cBuy = readableOn('#6DB56D', theme), cSell = readableOn('#E05C5C', theme);
  const money = n => n >= 1000000 ? "$" + (n / 1000000).toFixed(1) + "M"
                   : n >= 1000 ? "$" + Math.round(n / 1000) + "k" : "$" + n;
  return (
    <div style={{ height:"100%", display:"flex", flexDirection:"column", padding:"12px 16px 16px", overflowY:"auto" }}>
      <div style={{ display:"flex", alignItems:"baseline", justifyContent:"space-between", padding:"0 16px 6px" }}>
        <span style={{ fontFamily:"'Courier New',monospace", fontSize:"11px", letterSpacing:"0.18em", textTransform:"uppercase", color:"var(--text-tertiary)" }}>政要交易 ETF · 近一年</span>
        <a href="https://www.quiverquant.com/congresstrading/" target="_blank" rel="noopener noreferrer" className="source-link">Quiver 排行 ↗</a>
      </div>
      <div style={{ padding:"0 16px 10px", fontSize:"12px", lineHeight:1.6, color:"var(--text-tertiary)" }}>
        NANC 跟著民主黨籍議員的申報建倉、GOP 跟著共和黨籍（原 KRUZ），兩檔都吃 45 天申報延遲後的資料。跟 SPY 的差距就是「照著政要申報買」的真實代價與報酬。
      </div>
      <div className="tradingview-widget-container" ref={ref} style={{ height:"300px", flexShrink:0 }} />

      {R.roster.length > 0 && (
        <div style={{ paddingTop:"20px" }}>
          <div style={{ display:"flex", alignItems:"baseline", justifyContent:"space-between", padding:"0 16px 6px" }}>
            <span style={{ fontFamily:"'Courier New',monospace", fontSize:"11px", letterSpacing:"0.18em", textTransform:"uppercase", color:"var(--text-tertiary)" }}>個別議員 · 近 {R.window} 天申報</span>
            <span style={{ fontSize:"11px", color:"var(--text-tertiary)" }}>更新 {R.updated}</span>
          </div>
          <div style={{ padding:"0 16px 12px", fontSize:"12px", lineHeight:1.6, color:"var(--text-tertiary)" }}>
            眾議院 STOCK Act 定期交易報告（PTR）原始申報書彙整，共 {R.filings} 份、其中 {R.skipped_scanned} 份是紙本掃描件無法解析。金額只有級距沒有數字，絕大多數落在最低的 $1,001–$15,000，所以下面顯示的是<span style={{ color:"var(--text-secondary, inherit)" }}>申報區間</span>而不是實際金額——別把它當成真實部位大小。點議員名字可看原始申報書。
          </div>
          <div style={{ overflowX:"auto", padding:"0 16px" }}>
            <table style={{ width:"100%", borderCollapse:"collapse", fontSize:"12px" }}>
              <thead>
                <tr style={{ color:"var(--text-tertiary)", fontFamily:"'Courier New',monospace", fontSize:"11px", letterSpacing:"0.1em", textTransform:"uppercase" }}>
                  <th style={{ textAlign:"left",  padding:"6px 8px 6px 0", borderBottom:"1px solid var(--border, rgba(128,128,128,0.25))", whiteSpace:"nowrap" }}>議員</th>
                  <th style={{ textAlign:"right", padding:"6px 8px", borderBottom:"1px solid var(--border, rgba(128,128,128,0.25))", whiteSpace:"nowrap" }}>筆數</th>
                  <th style={{ textAlign:"right", padding:"6px 8px", borderBottom:"1px solid var(--border, rgba(128,128,128,0.25))", whiteSpace:"nowrap" }}>買 / 賣</th>
                  <th style={{ textAlign:"right", padding:"6px 8px", borderBottom:"1px solid var(--border, rgba(128,128,128,0.25))", whiteSpace:"nowrap" }}>申報區間</th>
                  <th style={{ textAlign:"left",  padding:"6px 8px", borderBottom:"1px solid var(--border, rgba(128,128,128,0.25))", whiteSpace:"nowrap" }}>常見標的</th>
                  <th style={{ textAlign:"right", padding:"6px 0 6px 8px", borderBottom:"1px solid var(--border, rgba(128,128,128,0.25))", whiteSpace:"nowrap" }}>最新申報</th>
                </tr>
              </thead>
              <tbody>
                {R.roster.map(r => (
                  <tr key={r.name + r.dst}>
                    <td style={{ padding:"7px 8px 7px 0", borderBottom:"1px solid var(--border, rgba(128,128,128,0.12))", whiteSpace:"nowrap" }}>
                      <a href={r.url} target="_blank" rel="noopener noreferrer" style={{ color:cName, textDecoration:"none" }}>{r.name}</a>
                      <span style={{ color:"var(--text-tertiary)", fontSize:"11px", marginLeft:"6px" }}>{r.dst}</span>
                    </td>
                    <td style={{ padding:"7px 8px", borderBottom:"1px solid var(--border, rgba(128,128,128,0.12))", textAlign:"right", fontVariantNumeric:"tabular-nums" }}>{r.n}</td>
                    <td style={{ padding:"7px 8px", borderBottom:"1px solid var(--border, rgba(128,128,128,0.12))", textAlign:"right", fontVariantNumeric:"tabular-nums", whiteSpace:"nowrap" }}>
                      <span style={{ color:cBuy }}>{r.buy}</span>
                      <span style={{ color:"var(--text-tertiary)" }}> / </span>
                      <span style={{ color:cSell }}>{r.sell}</span>
                    </td>
                    <td style={{ padding:"7px 8px", borderBottom:"1px solid var(--border, rgba(128,128,128,0.12))", textAlign:"right", color:"var(--text-tertiary)", fontVariantNumeric:"tabular-nums", whiteSpace:"nowrap" }}>{money(r.lo)}–{money(r.hi)}</td>
                    <td style={{ padding:"7px 8px", borderBottom:"1px solid var(--border, rgba(128,128,128,0.12))", whiteSpace:"nowrap" }}>
                      {r.top.map(t => (
                        <a key={t} href={"https://www.tradingview.com/symbols/" + t + "/"} target="_blank" rel="noopener noreferrer"
                           style={{ color:"var(--text-secondary, inherit)", textDecoration:"none", marginRight:"7px", fontFamily:"'Courier New',monospace" }}>{t}</a>
                      ))}
                      <span style={{ color:"var(--text-tertiary)", fontSize:"11px" }}>共 {r.distinct} 檔</span>
                    </td>
                    <td style={{ padding:"7px 0 7px 8px", borderBottom:"1px solid var(--border, rgba(128,128,128,0.12))", textAlign:"right", color:"var(--text-tertiary)", whiteSpace:"nowrap" }}>{r.last}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div style={{ padding:"12px 16px 0", fontSize:"11px", lineHeight:1.6, color:"var(--text-tertiary)" }}>
            只涵蓋眾議院；參議院走另一套 efdsearch 系統，尚未納入。買＋賣不一定等於筆數，差額是交換（exchange）類交易。
          </div>
        </div>
      )}
    </div>
  );
}

function App() {
  const [todaySub, setTodaySub] = useState("全部");
  const [idx, setIdx] = useState(0);
  const [dir, setDir] = useState(0); // -1=left, 1=right, 0=none
  const touchRef = React.useRef(null);

  const todayIso = metaDateIso();
  const todayCards = useMemo(() => CARDS.map(c => ({ ...c, _date: todayIso })), []);

  // ===== 收藏:存整張卡到 localStorage(mf_favs),長期保留 =====
  const [favs, setFavs] = useState(loadFavs);
  const favSet = useMemo(() => new Set(favs.map(cardUid)), [favs]);
  const toggleFav = React.useCallback((card) => {
    setFavs(prev => {
      const uid = cardUid(card);
      const next = prev.some(f => cardUid(f) === uid) ? prev.filter(f => cardUid(f) !== uid) : [{ ...card }, ...prev];
      saveFavs(next);
      return next;
    });
  }, []);

  const isFlow = todaySub === FLOW_TAB;
  const isPerf = todaySub === PERF_TAB;
  const isFavTab = todaySub === FAV_TAB;
  const isPast = todaySub === PAST_TAB;
  const isEmbed = isFlow || isPerf;  // 兩個嵌入分頁都不吃 CARDS:停用滑動、朗讀與前後翻頁

  // 收藏分頁:進入時拍一份快照。在裡面取消收藏,卡片不會立刻消失(離開再回來才更新),點錯可以再點回去
  const favSnapRef = React.useRef([]);
  if (isFavTab && !favSnapRef.current._live) { const snap = favs.slice(); snap._live = true; favSnapRef.current = snap; }
  if (!isFavTab && favSnapRef.current._live) favSnapRef.current = [];

  // ===== 過去的晨報:archive/index.json 列日期,archive/cards_YYYYMMDD.json 是當天卡片(唯讀) =====
  const [pastList, setPastList] = useState(null);     // null=未載入;[]=沒有存檔
  const [pastErr, setPastErr] = useState(false);
  const [pastDate, setPastDate] = useState(null);
  const [pastData, setPastData] = useState(null);     // { date, cards } | null(載入中)
  const [pastFail, setPastFail] = useState(false);
  const pastMemo = React.useRef({});
  React.useEffect(() => {
    if (!isPast || pastList) return;
    let dead = false;
    fetch("archive/index.json", { cache: "no-cache" }).then(r => { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(j => {
        if (dead) return;
        const ds = ((j && j.dates) || []).filter(d => /^\d{8}$/.test(d) && d < todayIso).sort().reverse().slice(0, 14);
        setPastList(ds); setPastErr(false);
        setPastDate(cur => cur && ds.indexOf(cur) >= 0 ? cur : (ds[0] || null));
      })
      .catch(() => { if (!dead) setPastErr(true); });
    return () => { dead = true; };
  }, [isPast, pastList]);
  React.useEffect(() => {
    if (!isPast || !pastDate) return;
    let dead = false;
    setPastFail(false);
    if (pastMemo.current[pastDate]) { setPastData({ date: pastDate, cards: pastMemo.current[pastDate] }); return; }
    setPastData(null);
    fetch("archive/cards_" + pastDate + ".json", { cache: "no-cache" }).then(r => { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(arr => {
        if (dead) return;
        const cs = (Array.isArray(arr) ? arr : []).map(c => ({ ...c, _date: pastDate }));
        pastMemo.current[pastDate] = cs;
        setPastData({ date: pastDate, cards: cs });
      })
      .catch(() => { if (!dead) setPastFail(true); });
    return () => { dead = true; };
  }, [isPast, pastDate]);

  const cards = useMemo(() => {
    if (isFavTab) return favSnapRef.current;
    if (isPast) return (pastData && pastData.date === pastDate) ? pastData.cards : [];
    if (todaySub === "全部") return todayCards;
    return todayCards.filter(c => c.channel === todaySub);
  }, [todaySub, pastData, pastDate, isFavTab && favSnapRef.current]);

  const total = cards.length;
  const atEnd = idx >= total;
  const viewKey = isPast ? PAST_TAB + ":" + pastDate : todaySub;   // 換頻道或換日期都算換一份閱讀清單
  const persist = !isPast && !isFavTab;                            // 只有今天的頻道記閱讀進度
  const emptyText = isFavTab ? "還沒有收藏。點卡片右上角的 ☆,就會收進這裡(存在這支手機上,長期保留)。"
    : isPast ? (pastErr ? "讀不到過去的晨報存檔(可能離線,連上網路後再試)。"
              : pastList && pastList.length === 0 ? "還沒有過去的晨報存檔。"
              : pastFail ? "這一天的存檔讀不到(可能離線,連上網路後再試)。"
              : "載入中…")
    : "";

  const [resumeMsg, setResumeMsg] = useState(null);
  const [playing, setPlaying] = useState(false);
  // 連續播放的語言(與單卡 🔊 的「跟著畫面走」分開;開車時想聽英文就切這裡),記在 localStorage
  const [playLang, setPlayLang] = useState(() => {
    const v = ls.get('mf_playLang');
    return (v === 'en' || v === 'zh') ? v : 'zh';
  });
  const cyclePlayLang = () => {
    const next = { zh:'en', en:'zh' }[playLang];
    setPlayLang(next);
    try { ls.set('mf_playLang', next); } catch(e) {}
  };
  const lsKey = lsKeyFor(todaySub);
  const saveIdx = (i) => { if (persist) ls.set(lsKey, String(i)); };

  // 每日更新後清掉舊 brief 的閱讀進度,localStorage 不會越積越多
  React.useEffect(() => {
    try {
      const stale = [];
      for (let i = 0; i < localStorage.length; i++) {
        const k = localStorage.key(i);
        if (k && k.indexOf("mosfeed_") === 0 && k.indexOf(BRIEF_ID) !== 8) stale.push(k);
      }
      stale.forEach(k => ls.del(k));
    } catch(e) {}
  }, []);

  // Read localStorage on tab/sub change(換 brief 就沒有舊 key,自然從第 1 張開始)
  React.useEffect(() => {
    try {
      const saved = persist ? parseInt(ls.get(lsKeyFor(todaySub)), 10) : 0;
      if (saved > 0 && saved < cards.length) {
        setIdx(saved); setDir(0);
        setResumeMsg({ idx: saved, total: cards.length });
        setTimeout(() => setResumeMsg(null), 1500);
        return;
      }
    } catch(e) {}
    setIdx(0); setDir(0);
  }, [viewKey]);

  const go = (newIdx) => {
    if (newIdx < 0) return;
    if (newIdx > total) return;
    setDir(newIdx > idx ? 1 : -1);
    setIdx(newIdx);
    saveIdx(newIdx);
  };

  // 回到第一張(開車時單手可按;連續播放中按了就從頭再播)
  const goTop = () => { setDir(-1); setIdx(0); saveIdx(0); };

  // ===== 連續播放:唸完一張自動翻下一張,一路唸到最後 =====
  // v6.4 背景播放:整條鏈不再依賴 setTimeout、也不在唸完後才 fetch —
  // 唸這張的同時預抓下一張音訊,onended 立刻換 src 接播,卡間 0.6 秒停頓燒進音檔尾端。
  // iOS 背景會凍結 timer 與網路,但「音訊播完 → 馬上接著播下一顆」這條路是放行的。
  const playTokenRef = React.useRef(0);
  const idxRef = React.useRef(idx);
  React.useEffect(() => { idxRef.current = idx; }, [idx]);
  const flowCtlRef = React.useRef(null);   // 鎖屏 Media Session 的上一則/下一則用

  const stopPlay = React.useCallback(() => {
    playTokenRef.current++;   // 讓還在飛的 onEnd 失效,不會誤翻頁
    azureStop();
    setPlaying(false);
  }, []);

  React.useEffect(() => {
    if (!playing) return;
    if (isEmbed || atEnd || !cards[idxRef.current]) { setPlaying(false); return; }
    const token = ++playTokenRef.current;
    const alive = () => playTokenRef.current === token;
    let prefetch = null;   // { i, promise } 下一張的音訊 blob URL,唸完零延遲接播

    const azRate = playLang === 'zh' ? '-8%' : '-5%';
    const sysRate = playLang === 'zh' ? 0.95 : 0.88;
    // 開車情境:先報位置(中文再加頻道與標籤),讓耳朵知道現在是哪一則,再唸內文
    const textOf = (i) => {
      const card = cards[i];
      const body = playLang === 'en' ? (card.en || card.zh) : card.zh;
      const intro = playLang === 'en' ? `Number ${i + 1} of ${total}. `
                  : `第 ${i + 1} 則，${card.channel}，${card.tag || ""}。`;
      return intro + body;
    };
    const setMedia = (i) => {   // 鎖屏畫面顯示現在唸到哪一則
      if (!('mediaSession' in navigator)) return;
      try {
        const card = cards[i];
        navigator.mediaSession.metadata = new MediaMetadata({
          title: (i + 1) + "/" + total + "・" + card.channel + (card.tag ? "・" + card.tag : ""),
          artist: "Mo's Feed",
          artwork: [{ src: "apple-touch-icon.png", sizes: "180x180", type: "image/png" }]
        });
        navigator.mediaSession.playbackState = 'playing';
      } catch(e) {}
    };

    const playCard = async (i) => {
      if (!alive()) return;
      if (i >= total) { setPlaying(false); setDir(1); setIdx(total); saveIdx(total); return; }
      setDir(1); setIdx(i); idxRef.current = i;
      saveIdx(i);
      setMedia(i);
      let preUrl = null;
      if (prefetch && prefetch.i === i) preUrl = await prefetch.promise;
      prefetch = null;
      if (!alive()) { if (preUrl) { try { URL.revokeObjectURL(preUrl); } catch(e) {} } return; }
      if (i + 1 < total) prefetch = { i: i + 1, promise: speakPrefetch(textOf(i + 1), { speakLang: playLang, azRate, tailMs: 600 }) };
      speakSmart(textOf(i), {
        speakLang: playLang, azRate, sysRate, tailMs: 600, preUrl,
        onEnd: () => { if (alive()) playCard(i + 1); },
        onError: () => { if (alive()) setPlaying(false); }
      });
    };

    flowCtlRef.current = {   // 鎖屏的上一則/下一則:跳到目標卡重新接鏈,prefetch 對得上就直接用
      next: () => { if (alive()) playCard(Math.min(idxRef.current + 1, total)); },
      prev: () => { if (alive()) playCard(Math.max(idxRef.current - 1, 0)); },
    };
    playCard(idxRef.current);
    return () => {
      playTokenRef.current++;
      azureStop();
      flowCtlRef.current = null;
      const p = prefetch; prefetch = null;
      if (p) p.promise.then(u => { if (u) { try { URL.revokeObjectURL(u); } catch(e) {} } });
    };
  }, [playing, playLang, viewKey]);

  // 鎖屏/耳機控制:播放、暫停、上一則、下一則(開車時不用點亮螢幕)
  React.useEffect(() => {
    if (!('mediaSession' in navigator)) return;
    const ms = navigator.mediaSession;
    const set = (a, fn) => { try { ms.setActionHandler(a, fn); } catch(e) {} };
    if (!playing) {
      try { ms.playbackState = 'none'; } catch(e) {}
      ['play','pause','nexttrack','previoustrack'].forEach(a => set(a, null));
      return;
    }
    // 暫停/播放要看當下是哪條路在唸:Azure 音檔(_azAudio)或退回的瀏覽器語音(speechSynthesis)
    set('pause', () => { try {
      if (_azAudio && !_azAudio.paused) _azAudio.pause();
      else if (HAS_TTS && speechSynthesis.speaking && !speechSynthesis.paused) speechSynthesis.pause();
      ms.playbackState = 'paused';
    } catch(e) {} });
    set('play',  () => { try {
      if (_azAudio && _azAudio.paused) _azAudio.play();
      else if (HAS_TTS && speechSynthesis.paused) speechSynthesis.resume();
      ms.playbackState = 'playing';
    } catch(e) {} });
    set('nexttrack',     () => { if (flowCtlRef.current) flowCtlRef.current.next(); });
    set('previoustrack', () => { if (flowCtlRef.current) flowCtlRef.current.prev(); });
    return () => { ['play','pause','nexttrack','previoustrack'].forEach(a => set(a, null)); };
  }, [playing]);

  // 切頻道 / 進資金流向就停播
  React.useEffect(() => { stopPlay(); }, [viewKey]);

  // Keyboard
  React.useEffect(() => {
    const handler = (e) => {
      if (e.target && /^(INPUT|TEXTAREA|SELECT)$/.test(e.target.tagName)) return;
      if (e.key === "ArrowRight" || e.key === "ArrowDown") { stopPlay(); go(idx + 1); }
      if (e.key === "ArrowLeft" || e.key === "ArrowUp") { stopPlay(); go(idx - 1); }
      if (e.key === "Home") { stopPlay(); goTop(); }
      if (e.key === " ") { e.preventDefault(); if (playing) stopPlay(); else { azureUnlock(); setPlaying(true); } }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [idx, total, playing]);

  // Touch
  const onTouchStart = (e) => { touchRef.current = { x: e.touches[0].clientX, y: e.touches[0].clientY }; };
  const onTouchEnd = (e) => {
    if (!touchRef.current) return;
    const dx = e.changedTouches[0].clientX - touchRef.current.x;
    const dy = e.changedTouches[0].clientY - touchRef.current.y;
    if (Math.abs(dx) > Math.abs(dy) && Math.abs(dx) > 50) {
      stopPlay();                       // 手動滑動就接手控制權,停掉連續播放
      if (dx < 0) go(idx + 1);
      else go(idx - 1);
    }
    touchRef.current = null;
  };

  return (
    <div className="app-shell" style={{ maxWidth:"680px", margin:"0 auto", overflow:"hidden", display:"flex", flexDirection:"column" }}>
      <ThemeToggle />
      {/* Header */}
      <div style={{ flexShrink:0, background:"var(--bg)", paddingTop:"20px", zIndex:10 }}>
        <div style={{ padding:"0 32px", marginBottom:"12px" }}>
          <div style={{ marginBottom:"4px" }}>
            <h1 className="masthead-title" style={{ fontSize:"32px" }}>Mo's Feed</h1>
            <span className="running-header" style={{ display:"block", marginTop:"4px" }}><span>{APP_META.updated}</span><span style={{ marginLeft:"10px" }}>{APP_META.version}</span></span>
          </div>
          <div className="rule" />
        </div>
        <div style={{ display:"flex", alignItems:"baseline", justifyContent:"space-between", padding:"0 32px" }}>
          <div className="tab-nav" style={{ padding:0 }}>
            <span style={{ fontFamily:"Georgia,serif", fontSize:"26px", fontWeight:600, color:"var(--text)", letterSpacing:"-0.01em", lineHeight:1.2 }}>Today</span>
          </div>
        </div>
        <div className="sub-row" style={{ display:"flex", gap:"18px", padding:"4px 32px 0", overflowX:"auto" }}>
          {TODAY_SUBS.map(sub => (
            <button key={sub} className="sub-pill" aria-pressed={todaySub===sub} onClick={() => setTodaySub(sub)}
              style={{ color:todaySub===sub?"var(--text)":"var(--text-tertiary)", borderBottomColor:todaySub===sub?"var(--text-secondary)":"transparent" }}>
              {sub}{sub===FAV_TAB && favs.length > 0 ? " " + favs.length : ""}
            </button>
          ))}
        </div>
        {isPast && (
          <div className="sub-row" style={{ display:"flex", gap:"8px", padding:"6px 32px 4px", overflowX:"auto" }}>
            <button className="date-chip" onClick={() => setTodaySub("全部")} aria-label="回到今天的晨報">← 今天</button>
            {(pastList || []).map(d => (
              <button key={d} className={"date-chip" + (d === pastDate ? " on" : "")} aria-pressed={d === pastDate} onClick={() => setPastDate(d)}>{fmtDate(d, true)}</button>
            ))}
          </div>
        )}
        {isFavTab && total > 0 && (
          <div className="sub-row" style={{ display:"flex", alignItems:"center", gap:"10px", padding:"6px 32px 4px", flexWrap:"wrap" }}>
            <CopyButton label={"複製全部 " + total + " 張"} ariaLabel={"複製全部 " + total + " 張收藏為雷達池格式"} getText={() => radarTextAll(cards)} />
            <span className="running-header">雷達池格式 · 貼進 Notion</span>
          </div>
        )}
        <div style={{ padding:"0 32px", marginTop:"6px" }}><div className="rule" /></div>
        {resumeMsg && (
          <div className="running-header" style={{ padding:"6px 32px", animation:"fadeInOut 1.5s ease forwards" }}>
            繼續閱讀 {resumeMsg.idx + 1}/{resumeMsg.total}
          </div>
        )}
      </div>

      {/* Swipe area */}
      <div className="swipe-area" style={{ flex:1 }}
        onTouchStart={isEmbed ? undefined : onTouchStart} onTouchEnd={isEmbed ? undefined : onTouchEnd}
      >
        {isFlow ? (
          <HeatmapView />
        ) : isPerf ? (
          <PerfView />
        ) : total === 0 ? (
          <div className="card-slide" style={{ position:"relative", transform:"none" }}>
            <p className="empty-note" role="status">{emptyText || "這個頻道今天沒有卡片。"}</p>
          </div>
        ) : atEnd ? (
          <div className="card-slide" style={{ position:"relative", transform:"none" }}>
            <EndScreen onPrev={() => go(total - 1)} onTop={goTop} showDiscuss={!isPast && !isFavTab} />
          </div>
        ) : (
          <div className="card-slide" key={cardUid(cards[idx])} style={{ position:"relative", transform:"none" }}>
            <CardView card={cards[idx]} idx={idx} total={total} onManualSpeak={stopPlay} isFav={favSet.has(cardUid(cards[idx]))} onToggleFav={toggleFav} showCopy={isFavTab} />
          </div>
        )}
      </div>

      {/* Nav bar:← 播放語言 ▶連續播放 頁碼 ⤒回第一張 → */}
      <div className="nav-bar">
        <button className="nav-btn" aria-label="上一張" onClick={() => { stopPlay(); go(idx - 1); }} disabled={isEmbed || idx === 0}>←</button>
        <button className="nav-btn nav-btn-lang" onClick={cyclePlayLang} disabled={isEmbed}
          aria-label={"連續播放語言：" + {zh:"中文",en:"English"}[playLang] + "（點一下切換）"}
          title={"連續播放語言：" + {zh:"中文",en:"English"}[playLang] + "（點一下切換）"}>{ {zh:"中",en:"EN"}[playLang] }</button>
        <button className={"nav-btn nav-btn-icon" + (playing ? " playing" : "")} onClick={() => { if (playing) stopPlay(); else { azureUnlock(); setPlaying(true); } }}
          disabled={isEmbed || atEnd} aria-label={playing ? "停止連續播放" : "連續播放（" + {zh:"中文",en:"English"}[playLang] + "）"} aria-pressed={playing}
          title={playing ? "停止連續播放" : "連續播放（" + {zh:"中文",en:"English"}[playLang] + "）"}>{playing ? "❚❚" : "▶"}</button>
        <span className="nav-count" aria-live="polite">{isEmbed ? "live · tradingview" : atEnd ? `${total}/${total}` : `${idx + 1} / ${total}`}</span>
        <button className="nav-btn nav-btn-icon" aria-label="回到第一張" onClick={() => { stopPlay(); goTop(); }} disabled={isEmbed || idx === 0} title="回到第一張">⤒</button>
        <button className="nav-btn" aria-label="下一張" onClick={() => { stopPlay(); go(idx + 1); }} disabled={isEmbed || atEnd}>→</button>
      </div>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);

// ===== Service worker:離線可開;晨報 index.html 是 network-first,有網路永遠拿最新 =====
if ('serviceWorker' in navigator && (location.protocol === 'https:' || location.hostname === 'localhost' || location.hostname === '127.0.0.1')) {
  window.addEventListener('load', () => { navigator.serviceWorker.register('sw.js').catch(() => {}); });
}
