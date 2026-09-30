/* Mo's Feed service worker
 *
 * 目標:離線也能開;但「每日更新」絕對不能被舊快取卡住。
 *  - 會每天變的東西(index.html、app.js、archive/*.json)→ network-first:有網路一律拿最新(強制向伺服器重新驗證,
 *    不吃瀏覽器 HTTP 快取),只有網路失敗或逾時才用快取。
 *  - 不會變的靜態資源(vendor/ 的 React、icon、manifest)→ cache-first。
 *  - 跨網域(TradingView 嵌入、Azure TTS、MyMemory 翻譯、unpkg…)一律不攔截,不進快取。
 *
 * 改了靜態資源清單、或要強制所有裝置換新快取時,把 SW_VERSION 加 1(sw.js 位元組一變,瀏覽器就會更新 SW)。
 * 每日排程只改 index.html,不需要動這支檔案。
 */
const SW_VERSION = 1;
const STATIC_CACHE = 'mosfeed-static-v' + SW_VERSION;
const FRESH_CACHE = 'mosfeed-fresh-v' + SW_VERSION;
const NETWORK_TIMEOUT_MS = 4000;

const STATIC_ASSETS = [
  'vendor/react-18.3.1.production.min.js',
  'vendor/react-dom-18.3.1.production.min.js',
  'apple-touch-icon.png',
  'manifest.json',
];
const FRESH_ASSETS = ['index.html', 'app.js', 'archive/index.json'];

self.addEventListener('install', (event) => {
  event.waitUntil((async () => {
    const st = await caches.open(STATIC_CACHE);
    await st.addAll(STATIC_ASSETS.map((u) => new Request(u, { cache: 'reload' })));
    const fr = await caches.open(FRESH_CACHE);
    // 預載失敗(例如 archive/index.json 還不存在)不擋安裝
    await Promise.all(FRESH_ASSETS.map(async (u) => {
      try {
        const res = await fetch(new Request(u, { cache: 'reload' }));
        if (res.ok) await fr.put(new Request(u), res);
      } catch (e) { /* ignore */ }
    }));
    await self.skipWaiting();
  })());
});

self.addEventListener('activate', (event) => {
  event.waitUntil((async () => {
    const keep = new Set([STATIC_CACHE, FRESH_CACHE]);
    for (const k of await caches.keys()) {
      if (k.indexOf('mosfeed-') === 0 && !keep.has(k)) await caches.delete(k);
    }
    await self.clients.claim();
  })());
});

function isFreshPath(url) {
  const p = url.pathname;
  return p.endsWith('/') || p.endsWith('/index.html') || p.endsWith('/app.js') || p.indexOf('/archive/') >= 0;
}

async function networkFirst(request, url) {
  const cache = await caches.open(FRESH_CACHE);
  // 快取 key 去掉網址參數(app.js?b=xxx → app.js);打開網頁本身(導覽請求或目錄網址)一律以 index.html 為 key
  const isNav = request.mode === 'navigate' || url.pathname.endsWith('/');
  const keyUrl = isNav && !url.pathname.endsWith('/index.html')
    ? new URL('index.html', self.registration.scope).href
    : url.origin + url.pathname;
  const key = new Request(keyUrl);
  try {
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), NETWORK_TIMEOUT_MS);
    // cache:'no-cache' = 每次都向伺服器驗證(ETag/Last-Modified,沒變就 304),不會被 HTTP 快取的舊檔騙到
    const res = await fetch(new Request(request.url, { cache: 'no-cache', credentials: 'same-origin' }), { signal: ctrl.signal });
    clearTimeout(timer);
    if (res && res.ok) {
      cache.put(key, res.clone());
      return res;
    }
    return (await cache.match(key)) || res;   // 伺服器回錯誤(404/5xx)時,有舊的就先用舊的
  } catch (e) {
    const cached = await cache.match(key);    // 離線或逾時
    if (cached) return cached;
    throw e;
  }
}

async function cacheFirst(request) {
  const cache = await caches.open(STATIC_CACHE);
  const hit = await cache.match(request, { ignoreSearch: true });
  if (hit) return hit;
  const res = await fetch(request);
  if (res && res.ok) cache.put(request, res.clone());
  return res;
}

self.addEventListener('fetch', (event) => {
  const request = event.request;
  if (request.method !== 'GET') return;
  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;                 // 跨網域:不碰
  if (!url.pathname.startsWith(new URL(self.registration.scope).pathname)) return;
  if (url.pathname.endsWith('/sw.js')) return;
  if (request.mode === 'navigate' || isFreshPath(url)) {
    event.respondWith(networkFirst(request, url));
  } else {
    event.respondWith(cacheFirst(request));
  }
});
