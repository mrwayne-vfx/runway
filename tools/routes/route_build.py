#!/usr/bin/env python3
"""Resolve exchange points and build run/drive route geometry for every leg.
Sources: Nominatim (geocoding, 1 req/s) and OSRM public demo (routing).
Output: routes.json (raw) and routes.js (embedded in the app)."""
import json, math, re, sys, time, pathlib, urllib.parse, urllib.request

ROOT = pathlib.Path(__file__).parent
CACHE = ROOT / "geocache.json"
UA = "RunwayRelayTracker/1.0 (waynebrinton@gmail.com)"
cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
def save_cache(): CACHE.write_text(json.dumps(cache))

# --- load leg data from data.js ---
src = (ROOT / "data.js").read_text()
import subprocess
legs = json.loads(subprocess.check_output(["node", "-e", src + ";console.log(JSON.stringify({RACE,LEGS}))"]))
RACE, LEGS = legs["RACE"], legs["LEGS"]
by_n = {l["n"]: l for l in LEGS}
def start_pt(n): return RACE["startPt"] if n == 1 else by_n[n-1]["pt"]

last_nom = 0
def nominatim(params):
    global last_nom
    key = "N:" + json.dumps(params, sort_keys=True)
    if key in cache: return cache[key]
    wait = 1.4 - (time.time() - last_nom)
    if wait > 0: time.sleep(wait)
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=30) as r: data = json.loads(r.read())
            break
        except Exception as e:
            print("  nominatim retry", e, file=sys.stderr); time.sleep(5*(attempt+1)); data = None
    last_nom = time.time()
    if data is None: return []
    cache[key] = data; save_cache()
    return data

def osrm(profile, coords, steps=False):
    key = "O2:" + profile + ":" + json.dumps(coords) + str(steps)
    if key in cache: return cache[key]
    s = ";".join(f"{lng},{lat}" for lat, lng in coords)
    base = "https://routing.openstreetmap.de/routed-foot/route/v1/driving/" if profile == "foot" else "https://router.project-osrm.org/route/v1/car/"
    url = f"{base}{s}?overview=full&geometries=geojson&steps={'true' if steps else 'false'}"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as r: data = json.loads(r.read())
            break
        except Exception as e:
            print("  osrm retry", e, file=sys.stderr); time.sleep(2*(attempt+1)); data = {"code": "error"}
    cache[key] = data; save_cache()
    return data

def coords_of(feature):
    g = feature.get("geojson")
    out = []
    def walk(c):
        if isinstance(c[0], (int, float)): out.append((c[1], c[0]))
        else:
            for x in c: walk(x)
    if g: walk(g["coordinates"])
    else: out.append((float(feature["lat"]), float(feature["lon"])))
    return out

def hav(a, b):
    R = 6371000; t = math.radians
    h = math.sin(t(b[0]-a[0])/2)**2 + math.cos(t(a[0]))*math.cos(t(b[0]))*math.sin(t(b[1]-a[1])/2)**2
    return 2*R*math.asin(math.sqrt(h))

def pt_seg_dist(p, a, b):
    # planar approx in metres
    kx = math.cos(math.radians(p[0])) * 111320; ky = 110540
    px, py = (p[1]-a[1])*kx, (p[0]-a[0])*ky; bx, by = (b[1]-a[1])*kx, (b[0]-a[0])*ky
    L2 = bx*bx + by*by
    t = 0 if L2 == 0 else max(0, min(1, (px*bx+py*by)/L2))
    cx, cy = a[1] + (b[1]-a[1])*t, a[0] + (b[0]-a[0])*t
    return math.hypot((p[1]-cx)*kx, (p[0]-cy)*ky), (cy, cx)

def viewbox(bbox):  # bbox = (minlat, minlng, maxlat, maxlng) -> nominatim viewbox lon1,lat1,lon2,lat2
    return f"{bbox[1]},{bbox[2]},{bbox[3]},{bbox[0]}"

def street_geom(name, bbox):
    res = nominatim({"q": name, "format": "jsonv2", "polygon_geojson": 1, "limit": 50, "viewbox": viewbox(bbox), "bounded": 1})
    pts = []
    for f in res:
        if f.get("category") in ("highway", "waterway", "railway", "route") or f.get("osm_type") == "way":
            pts.extend(coords_of(f))
    return pts

def intersection(a, b, bbox, tol=500):
    A, B = street_geom(a, bbox), street_geom(b, bbox)
    if not A or not B: return None, f"missing {'A' if not A else 'B'}"
    best = (1e9, None)
    # A nodes against B segments and vice versa
    def scan(P, Q):
        nonlocal best
        for i in range(len(Q)-1):
            for p in P:
                d, c = pt_seg_dist(p, Q[i], Q[i+1])
                if d < best[0]: best = (d, c)
    if len(A)*len(B) > 400000:  # thin out huge sets
        A = A[::max(1, len(A)//600)]; B = B[::max(1, len(B)//600)]
    scan(A, B); scan(B, A)
    if best[0] > tol: return None, f"too far {best[0]:.0f}m"
    return (round(best[1][0], 6), round(best[1][1], 6)), f"int {best[0]:.0f}m"

def place(q, bbox):
    res = nominatim({"q": q, "format": "jsonv2", "limit": 5, "viewbox": viewbox(bbox), "bounded": 1})
    if not res: return None, "no place"
    f = res[0]
    return (round(float(f["lat"]), 6), round(float(f["lon"]), 6)), "place:" + f.get("display_name", "")[:60]

def resolve(spec, bbox, tol=500):
    """spec: ('int', A, B) | ('place', q) | ('alt', spec, spec, ...) | ('fixed', lat, lng)"""
    kind = spec[0]
    if kind == "fixed": return (spec[1], spec[2]), "fixed"
    if kind == "int": return intersection(spec[1], spec[2], bbox, tol)
    if kind == "along": return None, "along"
    if kind == "place": return place(spec[1], bbox)
    if kind == "bbox": return resolve(spec[2], spec[1], tol)
    if kind == "alt":
        for s in spec[1:]:
            p, why = resolve(s, bbox, tol)
            if p: return p, why
        return None, "all alternatives failed"
    raise ValueError(spec)

I = lambda a, b: ("int", a, b)
P = lambda q: ("place", q)
ALT = lambda *s: ("alt",) + s
BB = lambda bbox, s: ("bbox", bbox, s)

# --------- per-leg spec: end = exchange point resolver (None keeps booklet GPS), via = ordered waypoints ---------
SPEC = {
 1: dict(dots=3, end=None, via=[]),
 2: dict(dots=3, end=None, via=[]),
 3: dict(dots=3, end=None, via=[]),
 4: dict(dots=3, end=None, via=[]),
 5: dict(dots=3, end=None, via=[]),
 6: dict(dots=3, end=None, via=[]),
 7: dict(dots=3, end=None, via=[]),
 8: dict(dots=3, end=None, via=[]),
 9: dict(dots=3, end=None, via=[]),
 10: dict(dots=3, end=None, via=[]),
 11: dict(dots=3, end=I("Lakeshore Road","Newtonville Road"), via=[]),
 12: dict(dots=3, end=I("Lakeshore Road","Port Britain Road"), via=[]),
 13: dict(dots=3, end=I("Madison Street","Mill Street South"), via=[]),
 14: dict(dots=3, end=ALT(P("Long & McQuade"), I("County Road 2","Bob Carr Road"), I("Toronto Road","Bob Carr Road"), I("County Road 2","Apple Orchard Road")), via=[]),
 15: dict(dots=3, end=P("Lucas Point Park"), via=[]),
 16: dict(dots=3, end=("fixed",43.9681,-78.0240), via=[]),
 17: dict(dots=3, end=None, via=[]),
 18: dict(dots=3, end=ALT(I("County Road 2","Blyth Park Road"), I("Blyth Park Road","Highway 2"), I("Blyth Park Road","Northumberland County Road 2"), I("Blyth Road","County Road 2"), I("Blyth Park Road","King Street East")), via=[]),
 19: dict(dots=3, end=I("Lakeshore Road","Lakehurst Street"), via=[]),
 20: dict(dots=3, end=ALT(I("County Road 64","Murray Canal"), I("Brighton Road","Murray Canal")), via=[]),
 21: dict(dots=3, end=I("Loyalist Parkway","Smokes Point Road"), via=[]),
 22: dict(dots=3, end=I("Loyalist Parkway","Station Road"), via=[]),
 23: dict(dots=3, end=None, via=[]),
 24: dict(dots=3, end=ALT(I("Main Street","Wights Street"), I("Bloomfield Main Street","Wights Street"), I("Main Street","Wight Street")), via=[]),
 25: dict(dots=3, end=ALT(I("Main Street","Washburn Street"), I("Picton Main Street","Washburn Street"), I("Loyalist Parkway","Washburn Street")), via=[]),
 26: dict(dots=3, end=None, via=[]),
 27: dict(dots=3, end=ALT(P("Bergeron Estate Winery"), I("Loyalist Parkway","33A Road"), I("Loyalist Parkway","County Road 33A"), I("Loyalist Parkway","33 A Road"), P("Loyalist Barkway")), via=[]),
 28: dict(dots=3, end=ALT(P("St. Paul's Anglican Church"), P("St Paul's Church"), I("Loyalist Parkway","Richmond Street")), via=[]),
 29: dict(dots=3, end=ALT(P("Finkle's Shore Park"), P("Finkle Shore Park")), via=[]),
 30: dict(dots=3, end=ALT(P("Parrott's Bay Conservation Area"), P("Parrotts Bay Conservation Area")), via=[]),
 31: dict(dots=3, end=ALT(P("The Boat Warehouse"), P("Boat Warehouse"), P("Collins Bay Marina"), I("Bath Road","Collins Bay Road")), via=[]),
 32: dict(dots=3, end=None, via=[]),
 33: dict(dots=3, end=ALT(I("Highway 2","Niagara Park"), I("Highway 2 East","Niagara Park"), I("Highway 2","Niagara Park Drive")), via=[]),
 34: dict(dots=3, end=ALT(P("Treasure Island Marina"), P("Treasure Island")), via=[]),
 35: dict(dots=3, end=ALT(I("Highway 2","Sandy Beach Lane"), I("Highway 2 East","Sandy Beach Lane")), via=[]),
 36: dict(dots=3, end=ALT(P("Colonial Resort"), I("King Street West","Garfield Street")), via=[]),
 37: dict(dots=3, end=None, via=[]),
 38: dict(end=ALT(I("Thousand Islands Parkway","Escott Rockport Road"), I("1000 Islands Parkway","Escott Rockport Road"), I("Thousand Islands Parkway","Escott-Rockport Road")), via=[]),
 39: dict(dots=3, end=ALT(P("Mallorytown Landing"), P("Thousand Islands National Park")), via=[]),
 40: dict(dots=3, end=ALT(P("Island Marine Canvas"), I("Brockmere Cliff Drive","County Road 2"), I("Brockmere Cliff Drive","Highway 2"), I("Brockmere Cliff Drive","Leeds and Grenville County Road 2"), I("Brockmere Cliff Drive","King Street West"), P("Butternut Bay")), via=[]),
 41: dict(dots=3, end=ALT(P("St. Lawrence Park"), P("St Lawrence Park")), via=[]),
 42: dict(dots=3, end=ALT(I("King Street East","Wood Street"), I("Highway 2","Wood Street"), I("County Road 2","Wood Street")), via=[]),
 43: dict(dots=3, end=ALT(I("Sophia Street","Water Street West"), I("Sophia Street","Water Street"), I("Sophia Street","King Street West")), via=[]),
 44: dict(dots=3, end=ALT(P("Grenville Park"), I("Shoreline Road","County Road 2")), via=[]),
 45: dict(dots=3, end=ALT(P("Home Hardware"), I("Walker Street","Dundas Street"), I("Walker Street","County Road 2")), via=[]),
 46: dict(dots=3, end=ALT(I("Carman Road","Dundas Street"), I("County Road 1","Dundas Street")), via=[]),
 47: dict(dots=3, end=ALT(P("Arlor Campground"), P("Arlor Haven"), I("Lakeshore Drive","Flagg Road")), via=[]),
 48: dict(dots=3, end=ALT(P("Riverside Cedar Campground"), P("Riverside-Cedar Campground"), P("Riverside Cedar Park")), via=[]),
 49: dict(dots=3, end=None, via=[]),
 50: dict(dots=3, end=None, via=[]),
 51: dict(dots=3, end=BB((44.99,-74.93,45.06,-74.84), ALT(I("Long Sault Parkway","County Road 2"), I("Long Sault Parkway","Highway 2"), I("Long Sault Parkway","Stormont, Dundas and Glengarry County Road 2"), I("Long Sault Parkway","Mille Roches Road"), P("Long Sault Parkway East Gate"))), via=[]),
 52: dict(dots=3, end=I("Second Street West","Power Dam Drive"), via=[]),
 53: dict(dots=3, end=ALT(P("St. Lawrence College"), P("St Lawrence College")), via=[]),
 54: dict(dots=3, end=BB((45.03,-74.66,45.09,-74.56), I("County Road 2","Orchard Road")), via=[]),
 55: dict(dots=3, end=P("Charlottenburgh Park"), via=[]),
 56: dict(dots=3, end=ALT(P("Glengarry Campground"), P("Glengarry Park")), via=[]),
 57: dict(dots=3, end=ALT(I("5th Line Road","County Road 2"), I("Fifth Line Road","County Road 2"), I("5th Line Road","Highway 2")), via=[]),
 58: dict(dots=3, end=I("26e Avenue","20e Rue"), via=[]),
 59: dict(dots=3, end=ALT(I("Chemin Saint-Emmanuel","Canal de Soulanges"), I("Chemin Saint-Emmanuel","Chemin du Vieux Canal")), via=[]),
 60: dict(dots=3, end=None, via=[]),
 61: dict(dots=3, end=None, via=[]),
 62: dict(dots=3, end=None, via=[]),
 63: dict(dots=3, end=None, via=[]),
 64: dict(dots=3, end=None, via=[]),
 65: dict(dots=3, end=None, via=[]),
 66: dict(dots=3, end=None, via=[]),
 67: dict(dots=3, end=None, via=[]),
}

def leg_bbox(n, pad=0.05):
    a, b = start_pt(n), by_n[n]["pt"]
    return (min(a[0], b[0])-pad, min(a[1], b[1])-pad, max(a[0], b[0])+pad, max(a[1], b[1])+pad)

def run(only=None):
    out = json.loads((ROOT/"routes.json").read_text()) if (ROOT/"routes.json").exists() else {}
    PDF = json.loads((ROOT/"pdf_points.json").read_text())
    for L in LEGS:
        L["pt"] = PDF[str(L["n"]+1)]
    RACE["startPt"] = PDF["1"]
    for L in LEGS:
        out.setdefault(str(L["n"]), {})["end"] = L["pt"]; out[str(L["n"])]["endSrc"] = "booklet gps"
    if False:
      for L in LEGS:
          n = L["n"]
          if only and n not in only: continue
          spec = SPEC[n]
          bbox = leg_bbox(n)
          end, why = (None, "booklet gps")
          if spec["end"] is not None:
              end, why = resolve(spec["end"], bbox, tol=250)
          if end and hav(end, L["pt"]) > 6000:
              print(f"leg {n}: resolved end {end} is {hav(end,L['pt'])/1000:.1f} km from estimate, keeping estimate ({why})")
              end, why = None, "rejected: " + why
          if end: by_n[n]["pt"] = list(end)
          out.setdefault(str(n), {})["end"] = by_n[n]["pt"]; out[str(n)]["endSrc"] = why
          print(f"leg {n}: end {by_n[n]['pt']} ({why})")
    # pass 1b: ends given as "km along the leg" (needs the next leg's end resolved first)
    for L in LEGS:
        n = L["n"]
        if only and n not in only: continue
        spec = SPEC[n]
        if True: continue
        target = by_n[n+1]["pt"]
        via = [list(resolve(v, leg_bbox(n))[0] or []) for v in spec["via"]]
        pts_ = [start_pt(n)] + [v for v in via if v] + [target]
        r = osrm("foot", pts_)
        if r.get("code") != "Ok": print(f"leg {n}: along failed"); continue
        geom = [(c[1], c[0]) for c in r["routes"][0]["geometry"]["coordinates"]]
        want = spec["along"]*1000; acc = 0; endpt = geom[-1]
        for k in range(len(geom)-1):
            d = hav(geom[k], geom[k+1])
            if acc + d >= want:
                f = (want-acc)/d; endpt = (geom[k][0]+(geom[k+1][0]-geom[k][0])*f, geom[k][1]+(geom[k+1][1]-geom[k][1])*f); break
            acc += d
        by_n[n]["pt"] = [round(endpt[0], 6), round(endpt[1], 6)]
        out[str(n)]["end"] = by_n[n]["pt"]; out[str(n)]["endSrc"] = f"int along {spec['along']} km"
        print(f"leg {n}: end {by_n[n]['pt']} (along {spec['along']} km toward exchange {n+1})")
    # pass 2: routes
    for L in LEGS:
        n = L["n"]
        if only and n not in only: continue
        spec = SPEC[n]; bbox = leg_bbox(n)
        pts = [start_pt(n)]; via_log = []
        TR = json.loads((ROOT/"pdf_trace.json").read_text()) if (ROOT/"pdf_trace.json").exists() else {}
        DD = json.loads((ROOT/"pdf_dots.json").read_text()) if (ROOT/"pdf_dots.json").exists() else {}
        if spec.get("dots") and str(n) in DD:
            line = DD[str(n)][1:-1]; step = spec["dots"]
            for k in range(step//2, len(line), step): pts.append([round(line[k][0],6), round(line[k][1],6)])
            via_log.append(f"ok dots {len(pts)-1} wps")
        if spec.get("trace") and str(n) in TR:
            line = TR[str(n)]; acc = 0; nxt = spec["trace"]
            for k in range(1, len(line)-1):
                acc += hav(line[k-1], line[k])
                if acc >= nxt: pts.append([round(line[k][0],6), round(line[k][1],6)]); nxt += spec["trace"]
            via_log.append(f"ok trace {len(pts)-1} wps")
        if spec.get("midcar"):
            d0 = osrm("car", [start_pt(n), by_n[n]["pt"]])
            if d0.get("code") == "Ok":
                g = [(c[1], c[0]) for c in d0["routes"][0]["geometry"]["coordinates"]]
                for f in spec["midcar"]:
                    pts.append(list(g[int(f*(len(g)-1))])); via_log.append(f"ok midcar {f}")
        for v in spec["via"]:
            p, why = resolve(v, bbox)
            if p and hav(p, pts[-1]) < 25000: pts.append(list(p)); via_log.append(f"ok {why}")
            else: via_log.append(f"skip {v} {why}")
        pts.append(by_n[n]["pt"])
        r = osrm("foot", pts, steps=True)
        rec = out.setdefault(str(n), {})
        if r.get("code") == "Ok":
            route = r["routes"][0]
            rec["run"] = [[round(c[1], 5), round(c[0], 5)] for c in route["geometry"]["coordinates"]]
            rec["runKm"] = round(route["distance"]/1000, 2)
            steps = []
            for lg in route["legs"]:
                for s in lg["steps"]:
                    m = s["maneuver"]; t = m.get("type", ""); mod = m.get("modifier", "")
                    if t in ("depart", "arrive") or s["distance"] == 0 and t not in ("depart", "arrive"): pass
                    if t == "depart": label = "Start"
                    elif t == "arrive": label = "Exchange"
                    else: label = (t.replace("_", " ") + (" " + mod if mod else "")).strip()
                    steps.append([round(m["location"][1], 5), round(m["location"][0], 5), label, s.get("name", ""), round(s["distance"])])
            rec["steps"] = steps
        else:
            rec["run"] = None; rec["runKm"] = None; rec["steps"] = []
        d = osrm("car", [start_pt(n), by_n[n]["pt"]])
        if d.get("code") == "Ok":
            route = d["routes"][0]
            rec["drive"] = [[round(c[1], 5), round(c[0], 5)] for c in route["geometry"]["coordinates"]]
            rec["driveKm"] = round(route["distance"]/1000, 1); rec["driveMin"] = round(route["duration"]/60)
        else:
            rec["drive"] = None
        rec["via"] = via_log
        ratio = (rec["runKm"] or 0)/L["km"]
        flag = "" if 0.9 <= ratio <= 1.12 else "  <-- CHECK"
        print(f"leg {n}: run {rec['runKm']} km vs booklet {L['km']} (x{ratio:.2f}){flag}; drive {rec.get('driveKm')} km {rec.get('driveMin')} min; via ok {sum(1 for v in via_log if v.startswith('ok'))}/{len(via_log)}")
        for v in via_log:
            if v.startswith("skip"): print("    ", v)
        (ROOT/"routes.json").write_text(json.dumps(out))
    # emit routes.js
    js = "const ROUTES = " + json.dumps(out, separators=(",", ":")) + ";\n"
    (ROOT/"routes.js").write_text(js)
    print("wrote routes.js", len(js), "bytes")

if __name__ == "__main__":
    only = [int(x) for x in sys.argv[1:]] or None
    run(only)
