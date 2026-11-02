#!/usr/bin/env python3
"""For every leg, check that the routed run line passes along each street named in the booklet directions."""
import json, re, math, sys, pathlib, subprocess
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import route_build as rb

R = json.load(open(rb.ROOT/"routes.json"))
STOP = {"the","waterfront","trail","path","road","street","st","rd","ave","avenue","drive","dr","left","right","straight","north","south","east","west","toward","towards","onto","on","to","stay","continue","turn","head","run","for","and","then","you","will","in","at","a","of","is","it","be","this","that","your","with","exchange","transition","zone","point","lot","parking"}
# words that begin a street reference
PAT = re.compile(r"(?:onto|on|along|up|down|toward|towards|into|at|over|cross|continue onto|becomes|stay on|take)\s+(?:the\s+)?((?:[A-Z]|\d+e\s)[\w'’\-\.]*(?:\s+(?:de|du|des|la|le|of|and|St\.?|Ste\.?|[A-Z][\w'’\-\.]*))*)")
SKIP_WORDS = {"Waterfront","Trail","Path","Transition","Exchange","Lake","Ontario","Google","Toronto","GPS","Kingston","Highway","RV","Once","Turn","Run","Cross","Continue","Stay","Head","Take","Follow","Right","Left","Hwy","Route","Rd","Hill","Guildwood","Beach","Lakeshore","If","There","This","The","Water","Lots","Fun","Meeting","Looks","Another","After","Later","Regional","Seasonal","ENTERING","Quebec","Bonjour","Pollywogs","DO","NOT","You","Keep","Exchange","FINISH","START","Don","Watch","Km","KM"}

def streets(leg):
    names = []
    for d in leg["dirs"]:
        for m in PAT.finditer(d):
            n = m.group(1).split(". ")[0].strip(" .,;:()")
            n = re.sub(r"\s+(for|and|run|which|then|in|at|is|until|toward|towards|heading|only|about|to)\b.*$", "", n)
            n = re.sub(r"\s*/.*$", "", n)
            if len(n) < 5: continue
            if n.split()[0] in SKIP_WORDS and len(n.split()) == 1: continue
            if not re.search(r"(Road|Rd|Street|St|Avenue|Ave|Drive|Dr|Boulevard|Blvd|Crescent|Cres|Parkway|Pkwy|Lane|Court|Ct|Terrace|Place|Pl|Way|Quay|Rue|Chemin|Montée|Heights|Hills|Promenade|Esplanade|Circle|Gardens|Park|Marina|Causeway|Bridge|Square)", n): continue
            if n not in names: names.append(n)
    return names

def norm(n):
    n = n.replace("St.", "Street").replace(" St ", " Street ").replace(" Rd", " Road").replace(" Dr", " Drive").replace(" Ave", " Avenue").replace(" Blvd", " Boulevard").replace(" Pkwy", " Parkway").replace(" Cres", " Crescent").replace(" Ct", " Court").replace(" Pl", " Place")
    n = re.sub(r"\bSt$", "Street", n); n = re.sub(r"\bRd$", "Road", n); n = re.sub(r"\bDr$", "Drive", n); n = re.sub(r"\bAve$", "Avenue", n); n = re.sub(r"\bBlvd$", "Boulevard", n); n = re.sub(r"\bPkwy$", "Parkway", n)
    return n.strip()

def min_dist(line, pts):
    best = 1e9
    step = max(1, len(pts)//150)
    P = pts[::step]
    for i in range(len(line)-1):
        a, b = line[i], line[i+1]
        for p in P:
            d, _ = rb.pt_seg_dist(p, a, b)
            if d < best: best = d
    return best

report = {}
for L in rb.LEGS:
    n = L["n"]; rec = R[str(n)]; line = rec["run"]
    bbox = rb.leg_bbox(n, pad=0.03)
    res = []
    for s in streets(L):
        q = norm(s)
        geom = rb.street_geom(q, bbox)
        if not geom:
            res.append((s, None)); continue
        d = min_dist(line, geom)
        res.append((s, round(d)))
    report[n] = res
    hit = [r for r in res if r[1] is not None and r[1] <= 80]
    miss = [r for r in res if r[1] is not None and r[1] > 80]
    unk = [r for r in res if r[1] is None]
    print(f"leg {n}: {len(hit)}/{len(hit)+len(miss)} named streets on the line" + (f"; MISSED: {', '.join(f'{m[0]} ({m[1]} m)' for m in miss)}" if miss else "") + (f"; not found in map data: {', '.join(u[0] for u in unk)}" if unk else ""), flush=True)
json.dump(report, open(rb.ROOT/"verify.json", "w"))
