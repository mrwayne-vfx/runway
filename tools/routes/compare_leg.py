#!/usr/bin/env python3
"""Side by side: booklet map (left) vs routed line over OSM tiles (right). Usage: compare_leg.py N [N...]"""
import json, math, sys, pathlib, urllib.request, time
from PIL import Image, ImageDraw
ROOT = pathlib.Path(__file__).parent
R = json.load(open(ROOT/"routes.json"))
OUT = ROOT/"compare"; OUT.mkdir(exist_ok=True)
TC = pathlib.Path("/tmp/claude-0/-home-claude/05d08b47-82ff-5b0e-8e04-080e6693fd3a/scratchpad/tiles"); TC.mkdir(exist_ok=True)
def t2(lat, lng, z): n=2**z; x=(lng+180)/360*n; la=math.radians(lat); y=(1-math.log(math.tan(la)+1/math.cos(la))/math.pi)/2*n; return x, y
def tile(z,x,y):
    f = TC/f"{z}_{x}_{y}.png"
    if not f.exists():
        req = urllib.request.Request(f"https://tile.openstreetmap.org/{z}/{x}/{y}.png", headers={"User-Agent":"RunwayRelayTracker/1.0 (waynebrinton@gmail.com)"})
        with urllib.request.urlopen(req, timeout=30) as r: f.write_bytes(r.read())
        time.sleep(0.12)
    return Image.open(f).convert("RGB")
def mine(n, W=820, H=460):
    rec = R[str(n)]; line = rec["run"]; prev = R[str(n-1)]["end"] if n>1 else [43.6517326,-79.3826236]
    lats=[p[0] for p in line]+[prev[0]]; lngs=[p[1] for p in line]+[prev[1]]
    # choose zoom so the route fits W x H with margin
    for z in range(16,10,-1):
        x0,y0=t2(max(lats),min(lngs),z); x1,y1=t2(min(lats),max(lngs),z)
        if (x1-x0)*256 <= W-60 and (y1-y0)*256 <= H-60: break
    cx,cy=(x0+x1)/2,(y0+y1)/2
    left=cx-W/512; top=cy-H/512
    img=Image.new("RGB",(W,H),(220,220,220))
    for tx in range(int(math.floor(left)), int(math.floor(left+W/256))+1):
        for ty in range(int(math.floor(top)), int(math.floor(top+H/256))+1):
            try: img.paste(tile(z,tx,ty),(int((tx-left)*256),int((ty-top)*256)))
            except Exception: pass
    d=ImageDraw.Draw(img)
    def px(p): x,y=t2(p[0],p[1],z); return ((x-left)*256,(y-top)*256)
    d.line([px(p) for p in line], fill=(255,0,120), width=5)
    for p,c in ((prev,(0,0,0)),(rec["end"],(255,0,120))):
        x,y=px(p); d.ellipse((x-8,y-8,x+8,y+8),fill=c,outline=(255,255,255),width=2)
    d.rectangle((0,0,230,20),fill=(255,255,255)); d.text((6,4), f"leg {n}  routed {rec['runKm']} km  (z{z})", fill=(0,0,0))
    return img
def compose(n):
    pdf = Image.open(ROOT/"pdfimg"/f"leg{n:02d}.png").convert("RGB").resize((820,460))
    m = mine(n)
    out = Image.new("RGB",(820*2+8,460),(40,40,40)); out.paste(pdf,(0,0)); out.paste(m,(828,0))
    p = OUT/f"leg{n:02d}.png"; out.save(p); print(p)
for a in sys.argv[1:]: compose(int(a))
