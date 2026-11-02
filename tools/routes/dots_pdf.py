#!/usr/bin/env python3
"""Extract the Google walking-route dots from each booklet screenshot, chain them in order, georeference, and emit
pdf_dots.json {leg: [[lat,lng],...]}. Dots are ~18 px apart; the chain walk uses that spacing."""
import json, math, sys, pathlib, re
import numpy as np
from PIL import Image
ROOT = pathlib.Path(__file__).parent
P = json.load(open(ROOT/"pdf_points.json")); C = json.load(open(ROOT/"pdf_centers.json"))
Z = {}
for line in open(ROOT/"trace.log"):
    m = re.search(r"^(\d+) ok .* z ([\d.]+)", line)
    if m: Z[int(m.group(1))] = float(m.group(2))
CX, CY = 683, 400   # viewport centre (map area y 60..740)

def merc(lat, lng): return (lng+180)/360, (1-math.log(math.tan(math.radians(lat))+1/math.cos(math.radians(lat)))/math.pi)/2
def unmerc(x, y): return math.degrees(math.atan(math.sinh(math.pi*(1-2*y)))), x*360-180

def dots_of(n):
    im = np.asarray(Image.open(ROOT/"pdfimg"/f"leg{n:02d}.png").convert("RGB")).astype(int)
    r, g, b = im[...,0], im[...,1], im[...,2]
    blue = (np.abs(r-0) < 45) & (np.abs(g-176) < 45) & (np.abs(b-248) < 35)
    ys, xs = np.nonzero(blue); sel = (ys > 60) & (ys < 740) & (xs < 1290); xs, ys = xs[sel], ys[sel]
    gr = {}
    for x, y in zip(xs, ys): gr.setdefault((x//3, y//3), []).append((x, y))
    cells = np.array([np.mean(v, axis=0) for v in gr.values()])
    dots = []; used = np.zeros(len(cells), bool)
    for i in range(len(cells)):
        if used[i]: continue
        d = np.linalg.norm(cells-cells[i], axis=1); grp = (d < 7) & (~used); used |= grp; dots.append(cells[grp].mean(axis=0))
    return np.array(dots)

def fit(n, dots):
    """Solve zoom and viewport-centre offset so the known start and end land on dots (least squares over a grid)."""
    s_ll, e_ll = P[str(n)], P[str(n+1)]; c = C[str(n)]
    cm, sm, em = np.array(merc(*c)), np.array(merc(*s_ll)), np.array(merc(*e_ll))
    best = None
    for z in np.arange(11.5, 15.01, 0.01):
        scale = 256*2**z
        # with centre at (CX,CY+dy): sp = (sm-cm)*scale + [CX, CY+dy]. Choose dy to minimise error over a small range.
        sp0 = (sm-cm)*scale + [CX, CY]; ep0 = (em-cm)*scale + [CX, CY]
        for dy in range(-40, 41, 4):
            for dx in range(-12, 13, 4):
                sp = sp0 + [dx, dy]; ep = ep0 + [dx, dy]
                err = np.linalg.norm(dots-sp, axis=1).min() + np.linalg.norm(dots-ep, axis=1).min()
                if best is None or err < best[0]: best = (err, scale, sp, ep, dx, dy)
    err, scale, sp, ep, dx, dy = best
    return err, scale, sp, ep, dx, dy

def chain(dots, sp, ep):
    used = np.zeros(len(dots), bool)
    cur = int(np.argmin(np.linalg.norm(dots-sp, axis=1))); endi = int(np.argmin(np.linalg.norm(dots-ep, axis=1)))
    order = [cur]; used[cur] = True; prev_dir = None
    for _ in range(len(dots)):
        if cur == endi: break
        d = np.linalg.norm(dots-dots[cur], axis=1); d[used] = 1e9
        cand = np.nonzero(d < 42)[0]
        if len(cand) == 0:
            cand = np.nonzero(d < 120)[0]   # gap under a tooltip/label
            if len(cand) == 0: break
        if prev_dir is not None and len(cand) > 1:
            v = dots[cand]-dots[cur]; vn = v/np.linalg.norm(v, axis=1)[:, None]
            score = d[cand]*(1.0 + 0.8*(1-(vn@prev_dir)))  # mild straight-ahead preference
            nxt = int(cand[np.argmin(score)])
        else:
            nxt = int(cand[np.argmin(d[cand])])
        step = dots[nxt]-dots[cur]; L = np.linalg.norm(step); prev_dir = step/L if L else prev_dir
        order.append(nxt); used[nxt] = True; cur = nxt
    return order, cur == endi

def run(n):
    dots = dots_of(n)
    if len(dots) < 5: return None, "no dots"
    err, scale, sp, ep, dx, dy = fit(n, dots)
    order, reached = chain(dots, sp, ep)
    c = C[str(n)]; cm = merc(*c)
    ll = [unmerc(cm[0]+(x-CX-dx)/scale, cm[1]+(y-CY-dy)/scale) for x, y in dots[order]]
    path = [list(P[str(n)])] + [[round(a, 6), round(b, 6)] for a, b in ll] + [list(P[str(n+1)])]
    return path, f"{'ok' if reached else 'PARTIAL'} dots {len(dots)} chained {len(order)} fit {err:.0f}px z {math.log2(scale/256):.2f}"

if __name__ == "__main__":
    out = json.loads((ROOT/"pdf_dots.json").read_text()) if (ROOT/"pdf_dots.json").exists() else {}
    for n in ([int(a) for a in sys.argv[1:]] or range(1, 68)):
        path, why = run(n); print(n, why)
        if path: out[str(n)] = path
    (ROOT/"pdf_dots.json").write_text(json.dumps(out))
