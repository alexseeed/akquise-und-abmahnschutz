#!/usr/bin/env python3
"""DNS stage 1b: shop subdomains (checkout/shop/store) -> CNAME targets; wildcard-safe."""
import csv, json, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor
def q(name, t):
    return subprocess.run(["dig", "+short", "+time=2", "+tries=1", name, t], capture_output=True, text=True).stdout.split()
def probe(domain):
    t0 = time.perf_counter()
    wild = q("zz-wildcard-probe-7311." + domain, "A")
    sub = []
    for s in ("checkout", "shop", "store"):
        c = q(f"{s}.{domain}", "CNAME")
        a = q(f"{s}.{domain}", "A")
        if wild and a and set(a) <= set(wild) and not c:
            continue  # wildcard answer, no information
        if c or a:
            sub.append(f"{s}.{domain} " + " ".join(c + a))
    return {"domain": domain, "wildcard": bool(wild), "sub": sub, "t": round(time.perf_counter() - t0, 3)}
rows = list(csv.DictReader(open(sys.argv[1])))
with ThreadPoolExecutor(8) as ex:
    for r in ex.map(probe, [r["domain"] for r in rows]):
        print(json.dumps(r))
