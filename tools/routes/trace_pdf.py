#!/usr/bin/env python3
"""Trace the blue dotted route in each booklet screenshot into lat/lng.
Georeference: map centre from the URL (pdf_centers.json) sits at the centre of the map viewport;
scale solved so the end pin lands on the known end coordinate (pdf_points.json)."""
import json, math, sys, pathlib
import numpy as np
from PIL import Image
ROOT = pathlib.Path(__file__).parent
P = json.load(open(ROOT/"pdf_points.json")); C = json.load(open(ROOT/"pdf_centers.json"))
# Map viewport inside the 1366x768 screenshot: below the browser chrome (~y=60) to above the taskbar (~y=740).
# Google centres the map on the viewport; the right-hand controls don't shift the centre.
MAP = (0, 60, 1366, 740)
CX, CY = (MAP[0]+MAP[2])/2, (MAP[1]+MAP[3])/2

def merc(lat, lng):
    return (lng+180)/360, (1-math.log(math.tan(math.radians(lat))+1/math.cos(math.radians(lat)))/math.pi)/2
def unmerc(x, y):
    return math.degrees(math.atan(math.sinh(math.pi*(1-2*y)))), x*360-180

def masks(im):
    a = np.asarray(im.convert("RGB")).astype(int); r, g, b = a[...,0], a[...,1], a[...,2]
    blue = (np.abs(r - 0) < 45) & (np.abs(g - 176) < 45) & (np.abs(b - 248) < 35)
    red = (r > 190) & (g < 100) & (b < 100)
    return blue, red

def trace(n, scale_override=None):
    im = Image.open(ROOT/"pdfimg"/f"leg{n:02d}.png")
    blue, red = masks(im)
    s_ll, e_ll = P[str(n)], P[str(n+1)]; c_ll = C[str(n)]
    cm, em, sm = np.array(merc(*c_ll)), np.array(merc(*e_ll)), np.array(merc(*s_ll))
    ys, xs = np.nonzero(blue)
    sel = (ys > MAP[1]) & (ys < MAP[3]) & (xs < 1290)
    xs, ys = xs[sel], ys[sel]
    if len(xs) < 50: return None, "no blue"
    g = {}
    for x, y in zip(xs, ys): g.setdefault((x//4, y//4), []).append((x, y))
    nodes = np.array([np.mean(v, axis=0) for v in g.values()])
    # Candidate scales for Google zoom 12..14.1 at 256px tiles: px per mercator unit = 256 * 2^z
    best = None
    for z in np.arange(11.5, 15.01, 0.01):
        scale = 256 * 2**z
        sp = (sm - cm) * scale + np.array([CX, CY]); ep = (em - cm) * scale + np.array([CX, CY])
        ds = np.linalg.norm(nodes - sp, axis=1).min(); de = np.linalg.norm(nodes - ep, axis=1).min()
        err = ds + de
        if best is None or err < best[0]: best = (err, scale, sp, ep, ds, de)
    err, scale, sp, ep, ds, de = best
    def px2ll(x, y): return unmerc(cm[0] + (x-CX)/scale, cm[1] + (y-CY)/scale)
    # keep nodes in the corridor
    lo = np.minimum(sp, ep) - 250; hi = np.maximum(sp, ep) + 250
    keep = np.all((nodes >= lo) & (nodes <= hi), axis=1); nodes = nodes[keep]
    # Order dots by distance along a smoothed spine: run a nearest-neighbour walk, then validate by
    # projecting every node onto the walk; unreached nodes are appended by projection on the start->end axis.
    order = []; used = np.zeros(len(nodes), bool)
    cur = int(np.argmin(np.linalg.norm(nodes - sp, axis=1)))
    endi = int(np.argmin(np.linalg.norm(nodes - ep, axis=1)))
    for _ in range(len(nodes)):
        order.append(cur); used[cur] = True
        if cur == endi: break
        d = np.linalg.norm(nodes - nodes[cur], axis=1); d[used] = 1e9
        nxt = int(d.argmin())
        if d[nxt] > 60: break
        cur = nxt
    if cur != endi:
        # fallback: order all nodes by projection onto the start->end axis
        axis = ep - sp; axis = axis / (np.linalg.norm(axis) + 1e-9)
        t = (nodes - sp) @ axis
        order = list(np.argsort(t))
        # drop nodes far off the corridor (>160px from the segment) which are UI or other blue
        perp = np.abs((nodes - sp) @ np.array([-axis[1], axis[0]]))
        order = [i for i in order if perp[i] < 160]
    path = [px2ll(*nodes[i]) for i in order]
    end_err = np.linalg.norm(nodes[order[-1]] - ep)
    out = [list(s_ll)] + [[round(a, 6), round(b, 6)] for a, b in path] + [list(e_ll)]
    return out, f"ok {len(out)} pts, fit {ds:.0f}+{de:.0f}px, end err {end_err:.0f}px, z {math.log2(scale/256):.2f}"

if __name__ == "__main__":
    out = json.loads((ROOT/"pdf_trace.json").read_text()) if (ROOT/"pdf_trace.json").exists() else {}
    legs = [int(a) for a in sys.argv[1:]] or range(1, 68)
    for n in legs:
        path, why = trace(n); print(n, why)
        if path: out[str(n)] = path
    (ROOT/"pdf_trace.json").write_text(json.dumps(out))
