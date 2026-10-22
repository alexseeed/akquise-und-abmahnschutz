#!/usr/bin/env python3
"""DNS-only stage: A/CNAME/NS/MX + PTR per domain via dig (no HTTP)."""
import csv, json, subprocess, sys, time

def dig(name, rtype):
    t0 = time.perf_counter()
    out = subprocess.run(["dig", "+short", "+time=3", "+tries=1", name, rtype],
                         capture_output=True, text=True).stdout.split()
    return out, time.perf_counter() - t0

# DNS-level platform hints (A record ranges / CNAME targets / PTR names)
A_HINTS = [("23.227.38.", "shopify"), ("23.227.37.", "shopify")]
CNAME_HINTS = [("myshopify.com", "shopify"), ("shopware.store", "shopware-saas"),
               ("wixdns.net", "wix"), ("squarespace.com", "squarespace"),
               ("jimdo", "jimdo"), ("bigcommerce.com", "bigcommerce"),
               ("plentymarkets", "plenty"), ("epages", "epages"), ("demandware.net", "sfcc")]
PTR_HINTS = [("maxcluster", "hoster:maxcluster(SW/Magento-Spezialist)"),
             ("timmehosting", "hoster:timme(SW/JTL-Spezialist)"),
             ("creoline", "hoster:creoline(Shopware-Spezialist)"),
             ("profihost", "hoster:profihost"), ("hetzner", "hoster:hetzner"),
             ("your-server.de", "hoster:hetzner"), ("ionos", "hoster:ionos"),
             ("1and1", "hoster:ionos"), ("strato", "hoster:strato"),
             ("cloudflare", "cdn:cloudflare"), ("amazonaws", "cloud:aws"),
             ("googleusercontent", "cloud:gcp"), ("akamai", "cdn:akamai"),
             ("mittwald", "hoster:mittwald"), ("all-inkl", "hoster:all-inkl"),
             ("jtl", "hoster:jtl"), ("gambio", "hoster:gambio"), ("plenty", "plenty"),
             ("shopify", "shopify"), ("shopware", "shopware-saas")]

def probe(domain):
    t0 = time.perf_counter()
    res = {"domain": domain}
    res["A"], _ = dig(domain, "A")
    res["www_CNAME"], _ = dig("www." + domain, "CNAME")
    res["www_A"], _ = dig("www." + domain, "A")
    res["NS"], _ = dig(domain, "NS")
    res["MX"], _ = dig(domain, "MX")
    ip = next((x for x in res["A"] + res["www_A"] if x[0].isdigit()), None)
    res["PTR"] = dig(ip + "", "PTR")[0] if False else []
    if ip:
        out = subprocess.run(["dig", "+short", "+time=3", "+tries=1", "-x", ip],
                             capture_output=True, text=True).stdout.split()
        res["PTR"] = out
    hints = set()
    for a in res["A"] + res["www_A"]:
        for p, h in A_HINTS:
            if a.startswith(p):
                hints.add(h)
    for c in res["www_CNAME"] + res["www_A"] + res["A"]:
        for p, h in CNAME_HINTS:
            if p in c.lower():
                hints.add(h)
    for p in res["PTR"] + res["NS"]:
        for k, h in PTR_HINTS:
            if k in p.lower():
                hints.add(h)
    res["dns_hints"] = sorted(hints)
    res["alive_dns"] = bool([x for x in res["A"] + res["www_A"] if x[0].isdigit()])
    res["t_dns_total"] = round(time.perf_counter() - t0, 3)
    return res

if __name__ == "__main__":
    rows = list(csv.DictReader(open(sys.argv[1])))
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(8) as ex:
        for r in ex.map(probe, [r["domain"] for r in rows]):
            print(json.dumps(r))
