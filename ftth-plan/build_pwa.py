"""Đóng gói viewer thành PWA (mini app): thư mục pwa/ + ftth-pwa.zip. Chạy sau build_html.py."""
import hashlib, json, os, shutil, zipfile
from PIL import Image, ImageDraw

OUT = 'pwa'
shutil.rmtree(OUT, ignore_errors=True); os.makedirs(OUT)

# ---- icon: 1 sợi vào splitter, tách thành 4 nhánh ----
def icon(size, pad=0.0):
    im = Image.new('RGB', (size, size), '#1f3a5f')
    d = ImageDraw.Draw(im)
    s = size * (1 - 2 * pad); o = size * pad
    X = lambda v: o + v * s
    w = max(2, int(s * 0.045))
    cy = 0.5
    d.line([(X(0.14), X(cy)), (X(0.40), X(cy))], fill='#ffffff', width=w)
    ys = [0.2, 0.4, 0.6, 0.8]
    for i, y in enumerate(ys):
        d.line([(X(0.40), X(cy)), (X(0.62), X(y)), (X(0.84), X(y))], fill=['#6ea1ff', '#f2a14b', '#5cc28a', '#e58bb6'][i], width=w, joint='curve')
        r = s * 0.035; d.ellipse([X(0.84) - r, X(y) - r, X(0.84) + r, X(y) + r], fill='#ffffff')
    r = s * 0.06; d.ellipse([X(0.40) - r, X(cy) - r, X(0.40) + r, X(cy) + r], fill='#ffffff')
    return im
big = icon(1024)
big.resize((512, 512), Image.LANCZOS).save(f'{OUT}/icon-512.png')
big.resize((192, 192), Image.LANCZOS).save(f'{OUT}/icon-192.png')
big.resize((180, 180), Image.LANCZOS).save(f'{OUT}/icon-180.png')
icon(1024, 0.12).resize((512, 512), Image.LANCZOS).save(f'{OUT}/icon-maskable-512.png')

# ---- index.html từ bản responsive ----
h = open('ftth_viewer.html', encoding='utf-8').read()
h = h.replace('<meta name="viewport" content="width=device-width,initial-scale=1">', '''<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#1f3a5f">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="FTTH Phố Đông">
<link rel="manifest" href="manifest.webmanifest">
<link rel="apple-touch-icon" href="icon-180.png">
<link rel="icon" type="image/png" href="icon-192.png">''', 1)
h = h.replace('</style>', 'header{padding-top:calc(10px + env(safe-area-inset-top,0px))}\n#info{top:env(safe-area-inset-top,0px)}\n</style>', 1)
h = h.replace('</body>', "<script>if('serviceWorker' in navigator){window.addEventListener('load',()=>navigator.serviceWorker.register('sw.js').catch(()=>{}))}</script>\n</body>", 1)
open(f'{OUT}/index.html', 'w', encoding='utf-8').write(h)

json.dump({
    'name': 'FTTH Phố Đông – Sơ đồ phối quang', 'short_name': 'FTTH Phố Đông', 'description': 'Tra đường quang căn hộ, tủ, ODF, PON',
    'start_url': './index.html', 'scope': './', 'display': 'standalone', 'orientation': 'any',
    'background_color': '#0f1620', 'theme_color': '#1f3a5f', 'lang': 'vi',
    'icons': [{'src': 'icon-192.png', 'sizes': '192x192', 'type': 'image/png'},
              {'src': 'icon-512.png', 'sizes': '512x512', 'type': 'image/png'},
              {'src': 'icon-maskable-512.png', 'sizes': '512x512', 'type': 'image/png', 'purpose': 'maskable'}],
}, open(f'{OUT}/manifest.webmanifest', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

ver = hashlib.sha1(h.encode()).hexdigest()[:10]
open(f'{OUT}/sw.js', 'w').write(f'''// Service worker: lưu sẵn mọi tệp để chạy offline. Phiên bản đổi theo nội dung index.html.
const CACHE = 'ftth-{ver}';
const FILES = ['./', './index.html', './manifest.webmanifest', './icon-180.png', './icon-192.png', './icon-512.png', './icon-maskable-512.png'];
self.addEventListener('install', e => {{ e.waitUntil(caches.open(CACHE).then(c => c.addAll(FILES)).then(() => self.skipWaiting())); }});
self.addEventListener('activate', e => {{ e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim())); }});
self.addEventListener('fetch', e => {{
  if (e.request.method !== 'GET') return;
  e.respondWith(caches.match(e.request, {{ignoreSearch: true}}).then(r => r || fetch(e.request).then(res => {{
    const copy = res.clone(); caches.open(CACHE).then(c => c.put(e.request, copy)); return res;
  }}).catch(() => caches.match('./index.html'))));
}});
''')

with zipfile.ZipFile('ftth-pwa.zip', 'w', zipfile.ZIP_DEFLATED) as z:
    for f in sorted(os.listdir(OUT)): z.write(f'{OUT}/{f}', f)
print('pwa ok', ver, sorted(os.listdir(OUT)))
