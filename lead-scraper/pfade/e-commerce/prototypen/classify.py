#!/usr/bin/env python3
"""Offline shop-system classifier over stored raw responses (stdlib only).

python3 classify.py sample.csv [--fp 1|2] [--limit-bytes N]
--fp 1 = rules as written in fingerprints.md (baseline)
--fp 2 = improved rules after validation (08.10.2026)
--limit-bytes = only look at the first N bytes of decoded HTML (stage-1 simulation)
"""
import csv, gzip, json, os, re, sys, datetime
BASE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(BASE, "raw")

# (system, where, regex, weight, fp_versions)  where: html|hdr|cookie|robots|dns
RULES = [
    # --- Shopware 6 (classic storefront) ---
    ("shopware6", "html", r"/theme/[0-9a-f]{32}/(?:css|js|assets)/", 5, {1, 2}),
    ("shopware6", "html", r"window\.(?:salesChannelId|themeAssetsPublicPath)\b", 4, {1, 2}),
    ("shopware6", "html", r"window\.router\s*=", 2, {1, 2}),
    ("shopware6", "html", r"window\.shopwareAnalytics", 2, {1, 2}),
    ("shopware6", "html", r"/bundles/storefront/", 4, {2}),           # v2: SW6 with custom asset build (nomos)
    ("shopware6", "hdr", r"^sw-(?:context-token|invalidation-states|version-id|language-id)", 3, {1}),
    ("shopware6", "hdr", r"^sw-(?:context-token|invalidation-states|version-id|language-id|currency-id)", 5, {2}),  # v2: 4/4 SW6 classic, also behind Cloudflare
    # --- Shopware 6 headless (Shopware Frontends / Nuxt) ---
    ("shopware6", "html", r"SWSC[A-Z0-9]{22}", 5, {1, 2}),
    ("shopware6", "html", r"salesChannelId", 2, {2}),                # v2: plain key in Nuxt payload
    ("shopware6", "html", r"/store-api/", 2, {1, 2}),
    ("shopware6", "html", r"shopwareEndpoint|shopwareAccessToken", 4, {2}),  # v2: Shopware Frontends config
    ("shopware6", "extra", r"sw-access-key", 8, {2}),                         # v2: 401 from /store-api/context
    # --- Shopware 5 ---
    ("shopware5", "html", r"/web/cache/\d{10}_[0-9a-f]+\.(?:css|js)", 6, {1, 2}),
    ("shopware5", "html", r"/themes/Frontend/[A-Za-z0-9_]+/", 4, {1, 2}),
    ("shopware5", "html", r"/engine/Shopware/|jquery\.shopware", 3, {1, 2}),
    ("shopware5", "cookie", r"^(?:session-\d+|__csrf_token-\d+)=", 2, {1}),
    ("shopware5", "cookie", r"^(?:session-\d+|__csrf_token-\d+|x-cache-context-hash)=", 4, {2}),  # v2: SW6 sets "session-" without id
    ("shopware5", "html", r'<meta name="application-name" content="Shopware"', 2, {1, 2}),
    ("shopware5", "hdr", r"^x-shopware-cache-id", 2, {1, 2}),
    # --- Shopify ---
    ("shopify", "hdr", r"^powered-by: shopify", 6, {1, 2}),
    ("shopify", "html", r"cdn\.shopify\.com/", 4, {1, 2}),
    ("shopify", "html", r"Shopify\.shop\s*=", 5, {1, 2}),
    ("shopify", "cookie", r"^_shopify_|^cart_currency=", 3, {1, 2}),
    ("shopify", "robots", r"#\s*we use Shopify|Shopify storefront", 4, {1, 2}),
    ("shopify", "dns", r"^A:23\.227\.3[89]\.|^CNAME:.*myshopify\.com", 6, {1, 2}),
    ("shopify", "dns", r"^SUB:(?:checkout|shop)\.\S+ .*myshopify\.com", 5, {2}),  # v2: headless Shopify
    # --- WooCommerce / WordPress ---
    ("woocommerce", "html", r"/wp-content/plugins/woocommerce/", 5, {1, 2}),
    ("woocommerce", "html", r"woocommerce-no-js|wc_add_to_cart_params|woocommerce_params", 4, {1, 2}),
    ("woocommerce", "html", r'generator" content="WooCommerce', 4, {1, 2}),
    ("woocommerce", "html", r"\bWooCommerce\b", 2, {1}),             # v1-naiv: Textnennung (1und1-Falle)
    ("wordpress", "html", r"/wp-content/|/wp-includes/", 2, {1}),
    ("wordpress", "html", r"/wp-content/|/wp-includes/", 4, {2}),          # v2: label WP non-shops
    # --- Magento ---
    ("magento2", "html", r"/static/version\d+/frontend/", 5, {1, 2}),
    ("magento2", "html", r'type="text/x-magento-init"', 5, {1, 2}),
    ("magento2", "cookie", r"^mage-", 2, {1, 2}),
    ("magento2", "hdr", r"^x-magento-", 3, {1, 2}),
    ("magento1", "html", r"/skin/frontend/|Mage\.Cookies", 4, {2}),
    # --- JTL ---
    ("jtl", "cookie", r"^JTLSHOP=", 6, {1, 2}),
    ("jtl", "html", r"jtl_token", 5, {1, 2}),
    ("jtl", "html", r"/templates/(?:NOVA|Evo)/", 4, {1, 2}),
    ("jtl", "html", r"JtlHelpers|jtl\.io|/includes/plugins/jtl_", 3, {2}),
    # --- Gambio ---
    ("gambio", "html", r"templates/gambio|gm_javascript\.js\.php|Shopsoftware by Gambio", 5, {1, 2}),
    ("gambio", "html", r"/GXModules/|/public/theme/styles/system/|gambio_hub|GambioHub", 5, {2}),
    ("gambio", "cookie", r"^GXsid", 4, {2}),
    # --- others ---
    ("oxid", "html", r"/out/[a-z0-9_]+/src/|oxid eshop|oxid esales", 4, {1, 2}),
    ("oxid", "cookie", r"^sid_key=oxid", 5, {1, 2}),
    ("prestashop", "html", r"var prestashop\s*=|/modules/ps_", 5, {1, 2}),
    ("prestashop", "cookie", r"^PrestaShop-", 5, {1, 2}),
    ("plentyshop", "hdr", r"^x-plenty", 6, {1, 2}),
    ("plentyshop", "html", r"plenty\.shop\.min\.js|plentymarkets|/plugin/ceres/", 4, {1, 2}),
    ("xtcommerce", "html", r'generator" content="xt:Commerce|XT\.version', 5, {1, 2}),
    ("modified", "html", r"modified eCommerce|tpl_modified", 5, {2}),
    ("sfcc", "html", r"demandware\.static|/on/demandware\.store/", 6, {1, 2}),
    ("bigcommerce", "html", r"cdn\d*\.bigcommerce\.com|bigcommerce_config", 5, {1, 2}),
    ("commercetools", "html", r'\\?"type\\?":\\?"commercetools|\.commercetools\.com', 4, {2}),
    ("wix", "hdr", r"^x-wix-request-id", 6, {1, 2}),
    ("squarespace", "hdr", r"^server: squarespace", 6, {1, 2}),
    ("jimdo", "hdr", r"^x-jimdo", 6, {1, 2}),
    ("epages", "hdr", r"^x-epages", 6, {1, 2}),
]
SHOP_SYSTEMS = {"shopware6", "shopware5", "shopify", "woocommerce", "magento2", "magento1", "jtl",
                "gambio", "oxid", "prestashop", "plentyshop", "xtcommerce", "modified", "sfcc",
                "bigcommerce", "commercetools", "wix", "squarespace", "jimdo", "epages"}
FRAMEWORK = [("nextjs", r"/_next/static/"), ("nuxt", r"/_nuxt/|window\.__NUXT__")]
SHOPPY = re.compile(r'in den warenkorb|add[-_ ]to[-_ ]cart|"@type"\s*:\s*"(?:Product|Offer)"|/checkout|warenkorb|basket', re.I)


def load(domain, name):
    p = os.path.join(RAW, domain, name + ".json")
    if not os.path.exists(p):
        return None, b""
    meta = json.load(open(p))
    body = gzip.open(os.path.join(RAW, domain, name + ".body.gz")).read()
    return meta, body


def decode_escapes(s):
    # SW 6.7 renders window.features as JSON.parse('{"V6_7_0_0":true...')
    return re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), s)


def classify(domain, dns, fp=2, limit_bytes=None):
    out = {"domain": domain, "fp_version": fp, "evidence": [], "scores": {}}
    hmeta, hbody = load(domain, "home")
    rmeta, rbody = load(domain, "robots")
    html = hbody.decode("utf-8", "replace")
    if limit_bytes:
        html = html[:limit_bytes]
    robots = rbody.decode("utf-8", "replace") if rmeta and rmeta["hops"][-1].get("status") == 200 else ""
    hdr_lines, cookies = [], []
    for meta in (hmeta, rmeta):
        if not meta:
            continue
        for hop in meta["hops"]:
            for k, v in hop.get("headers", []):
                hdr_lines.append(f"{k.lower()}: {v.lower()}")
                if k.lower() == "set-cookie":
                    cookies.append(v.split(";", 1)[0])
    dns_lines = []
    if dns:
        dns_lines += ["A:" + a for a in dns.get("A", []) + dns.get("www_A", [])]
        dns_lines += ["CNAME:" + c for c in dns.get("www_CNAME", [])]
        dns_lines += ["SUB:" + s for s in dns.get("sub", [])] if fp == 2 else []
    extra = []
    for fn in os.listdir(os.path.join(RAW, domain)) if os.path.isdir(os.path.join(RAW, domain)) else []:
        if fn.startswith("extra_") and fn.endswith(".body.gz"):
            extra.append(gzip.open(os.path.join(RAW, domain, fn)).read().decode("utf-8", "replace")[:5000])
    sources = {"html": [html], "hdr": hdr_lines, "cookie": cookies, "robots": [robots], "dns": dns_lines, "extra": extra}
    for system, where, rx, w, vers in RULES:
        if fp not in vers:
            continue
        r = re.compile(rx, re.I if where in ("hdr", "robots", "dns") or system in ("oxid",) else 0)
        for item in sources[where]:
            if item and r.search(item):
                out["scores"][system] = out["scores"].get(system, 0) + w
                out["evidence"].append(f"{system}:{where}:{rx[:40]}")
                break
    # v2: WooCommerce implies WordPress -> drop wordpress score; a text-only mention is no shop
    sc = out["scores"]
    status = (hmeta or {"hops": [{}]})["hops"][-1].get("status") if hmeta else None
    out["http_status"] = status
    out["final_url"] = hmeta["final_url"] if hmeta else None
    sub_only = [e for e in out["evidence"] if ":dns:^SUB" in e]
    if fp == 2 and sub_only:
        html_systems = {k for k, v in sc.items() if k != "shopify" and v >= 4 and k in SHOP_SYSTEMS}
        if html_systems and sc.get("shopify", 0) <= 5:   # subdomain is only a hint when the main site shows another platform
            sc["shopify"] -= 5
            out["notes"] = "Shopify nur auf Subdomain (checkout/shop) - Hauptseite anderes System"
    best = max(sc.items(), key=lambda kv: kv[1]) if sc else (None, 0)
    if fp == 2 and best[0] == "shopware6" and sc.get("shopware5", 0) >= 6:
        best = ("shopware5", sc["shopware5"])  # SW5 asset cache is unambiguous
    if fp == 2 and best[0] == "wordpress" and sc.get("woocommerce"):
        best = ("woocommerce", sc["woocommerce"])
    system = best[0] if best[1] >= 4 else None
    if system == "wordpress":
        system = "wordpress (kein Shop-Plugin)"
    out["system"] = system or ("unbekannt" if html else "kein_abruf")
    out["confidence"] = "hoch" if best[1] >= 8 else ("mittel" if best[1] >= 4 else "niedrig")
    out["frameworks"] = [n for n, rx in FRAMEWORK if re.search(rx, html)]
    out["headless"] = bool(out["frameworks"]) and system not in (None, "shopify") or ("SWSC" in html)
    out["shop_signals"] = len(SHOPPY.findall(html[:2_000_000]))
    # --- Shopware 6 details ---
    if system == "shopware6":
        dec = decode_escapes(html) if fp == 2 else html
        flags = re.findall(r'"?V6_(\d+)_0_0"?\s*:\s*(true|false)', dec)
        trues = [int(m) for m, v in flags if v == "true"]
        if trues:
            out["sw6_major"] = f"6.{max(trues)}"
            out["sw6_has_flag_6_9"] = any(m == "9" for m, _ in flags)
        elif fp == 2:
            if re.search(r"/theme/[0-9a-f]{32}/js/storefront/storefront\.js", html):
                out["sw6_major"] = ">=6.6 (per-bundle JS)"
            elif re.search(r"/theme/[0-9a-f]{32}/js/all\.js", html):
                out["sw6_major"] = "<=6.5 (all.js)"
        out["sw6_plugins"] = sorted(set(re.findall(r"/theme/[0-9a-f]{32}/js/([a-z0-9-]+)/", html)) - {"storefront"})
        out["sw6_bundles"] = sorted(set(re.findall(r"/bundles/([a-z0-9]+)/", html)) - {"storefront"})
        ts = re.findall(r"/theme/[0-9a-f]{32}/(?:css|js)/[^\"'?]+\?(\d{10})", html) or \
             re.findall(r"/bundles/[^\"'?]+\?(\d{10})", html)
        if ts:
            out["theme_build"] = datetime.datetime.utcfromtimestamp(int(max(ts))).strftime("%Y-%m-%d")
        out["sw_access_keys"] = len(set(re.findall(r"SWSC[A-Z0-9]{22}", html)))
    if system == "shopware5":
        ts = re.findall(r"/web/cache/(\d{10})_", html)
        if ts:
            out["theme_build"] = datetime.datetime.utcfromtimestamp(int(max(ts))).strftime("%Y-%m-%d")
        out["sw5_theme"] = sorted(set(re.findall(r"/themes/Frontend/([A-Za-z0-9_]+)/", html)))
        out["sw5_plugins"] = sorted(set(re.findall(r"/custom/plugins/([A-Za-z0-9_]+)/", html)))
    if system == "shopify":
        m = re.search(r'Shopify\.shop\s*=\s*"([^"]+)"', html)
        out["myshopify"] = m.group(1) if m else None
        m = re.search(r'Shopify\.theme\s*=\s*(\{.*?\});', html)
        if m:
            tsid = re.search(r'"theme_store_id":(null|\d+)', m.group(1))
            out["theme_store_id"] = tsid.group(1) if tsid else None
    return out


def main():
    args = sys.argv[1:]
    fp = int(args[args.index("--fp") + 1]) if "--fp" in args else 2
    lim = int(args[args.index("--limit-bytes") + 1]) if "--limit-bytes" in args else None
    dns = {}
    for l in open(os.path.join(BASE, "dns.jsonl")):
        r = json.loads(l)
        dns[r["domain"]] = r
    if os.path.exists(os.path.join(BASE, "dns_sub.jsonl")):
        for l in open(os.path.join(BASE, "dns_sub.jsonl")):
            r = json.loads(l)
            dns.setdefault(r["domain"], {})["sub"] = r["sub"]
    for row in csv.DictReader(open(args[0])):
        res = classify(row["domain"], dns.get(row["domain"]) if fp == 2 or True else None, fp, lim)
        res["expected"] = row["expected"]
        print(json.dumps(res, ensure_ascii=False))


if __name__ == "__main__":
    main()
