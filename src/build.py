import json, pathlib, re
root = pathlib.Path(__file__).parent
app = (root/"app.html").read_text()
data = (root/"data.js").read_text()
routes = (root/"routes.js").read_text() if (root/"routes.js").exists() else "const ROUTES = {};"
routes += "\n" + (root/"team.js").read_text()
routes += "\n" + (root/"sprites.js").read_text()
import datetime, zoneinfo
stamp = datetime.datetime.now(zoneinfo.ZoneInfo("America/Toronto")).strftime("%b %d, %H:%M")
import base64 as _b64
_lg=lambda p: "data:image/png;base64,"+_b64.b64encode((root/p).read_bytes()).decode()
app = app.replace('src="SP_BLACK"', 'src="'+_lg("brand/sp-black.png")+'"').replace('src="SP_WHITE"', 'src="'+_lg("brand/sp-white.png")+'"')
app = app.replace("/*BUILD*/", stamp).replace("/*FONTS*/", (root/"fonts.css").read_text())
body = app.replace("/*DATA*/", data + "\n" + routes)
(root/"runway-artifact.html").write_text(body)
lcss = (root/"vendor-leaflet.css").read_text()
ljs = (root/"vendor-leaflet.js").read_text()
hosted_body = body.replace("<style>", "<style>" + lcss + "</style>\n<style>", 1).replace("<div id=\"app\">", "<script>" + ljs + "</script>\n<div id=\"app\">", 1)

manifest = {"name":"The Runway Tracker","short_name":"Runway","start_url":"./index.html","display":"standalone",
            "background_color":"#F4F3EF","theme_color":"#F4F3EF","icons":[]}
manifest_uri = "data:application/manifest+json," + json.dumps(manifest).replace('"','%22').replace(" ","%20")

head = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#F4F3EF">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Runway">
<link rel="manifest" href="{manifest_uri}">
<style>:root{{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}} img{{max-width:100%}} [hidden]{{display:none!important}}</style>
</head>
<body>
"""
sw_reg = """
<script>
if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("./sw.js").then(() => { window.__swState = "on - this page works with no signal"; })
    .catch(() => { window.__swState = "unavailable (needs https or localhost)"; });
}
</script>
"""
standalone = head + hosted_body + sw_reg + "\n</body>\n</html>\n"
dist = root/"dist"; dist.mkdir(exist_ok=True)
(dist/"index.html").write_text(standalone)
(dist/"sw.js").write_text("""const CACHE = "runway-v47";
const ASSETS = ["./", "./index.html", "./sw.js", "./follow.html"];
self.addEventListener("install", e => { e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)).then(() => self.skipWaiting())); });
self.addEventListener("activate", e => { e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE && k !== "runway-tiles").map(k => caches.delete(k)))).then(() => self.clients.claim())); });
self.addEventListener("fetch", e => {
  const url = new URL(e.request.url);
  if (url.origin === location.origin) {
    // the app pages: network first so a refresh always shows the newest build, cache when there is no signal
    e.respondWith(fetch(e.request).then(res => { const copy = res.clone(); caches.open(CACHE).then(c => c.put(e.request, copy)); return res; }).catch(() => caches.match(e.request)));
  } else if (url.hostname.endsWith("arcgisonline.com")) {
    // map tiles: saved tiles first, else network (and keep what we fetch)
    e.respondWith(caches.match(e.request).then(r => r || fetch(e.request).then(res => { const copy = res.clone(); caches.open("runway-tiles").then(c => c.put(e.request, copy)); return res; })));
  } else {
    // fonts: network first, fall back to cache, fail quietly
    e.respondWith(fetch(e.request).then(res => { const copy = res.clone(); caches.open(CACHE).then(c => c.put(e.request, copy)); return res; }).catch(() => caches.match(e.request)));
  }
});
""")
# friends page: same data and routes, Leaflet inlined
fol = (root/"follow.html").read_text()
import base64
def _uri(p): return "data:image/png;base64," + base64.b64encode((root/p).read_bytes()).decode()
fol = fol.replace("/*BUILD*/", stamp).replace("/*FONTS*/", (root/"fonts.css").read_text()).replace("/*LEAFLETCSS*/", lcss)
fol = fol.replace('src="SP_BLACK"', 'src="'+_uri("brand/sp-black.png")+'"').replace('src="SP_WHITE"', 'src="'+_uri("brand/sp-white.png")+'"').replace('src="RUNTOMTL_PNG"', 'src="'+_uri("brand/runtomtl.png")+'"').replace('NARRO_MARK', _uri("brand/narro-mark.png")).replace('NARRO_WORD', _uri("brand/narro-word.png")).replace("<script>/*LEAFLETJS*/</script>", "<script>"+ljs+"</script>").replace("<script>/*DATA*/</script>", "<script>"+data+"\n"+routes+"</script>")
(dist/"follow.html").write_text(fol)
print("artifact bytes", len(body), "standalone bytes", len(standalone), "follow bytes", len(fol))
