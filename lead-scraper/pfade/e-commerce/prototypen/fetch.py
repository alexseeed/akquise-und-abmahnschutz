#!/usr/bin/env python3
"""Polite fetcher: robots.txt + homepage per domain (stdlib only).

Stores raw responses (headers + gzip body) under raw/<domain>/ so the
classifier can be re-run offline without new requests.
Usage: python3 fetch.py sample.csv [--workers 8]
       python3 fetch.py --extra <domain> <path>   (one system-specific request)
"""
import csv, gzip, http.client, json, socket, ssl, sys, time, zlib, os
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlsplit, urljoin

UA = "Mozilla/5.0 (compatible; research-check/1.0)"
UA_TOKEN = "research-check"
BASE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(BASE, "raw")
LOG = os.path.join(BASE, "requests.jsonl")
MAX_BYTES = 3 * 1024 * 1024
CONNECT_TIMEOUT, READ_TIMEOUT = 10, 20
CTX = ssl.create_default_context()


def log(rec):
    with open(LOG, "a") as f:
        f.write(json.dumps(rec) + "\n")


def one_request(url, domain, kind):
    """Single HTTP GET without auto-redirect. Returns dict with timing/bytes."""
    u = urlsplit(url)
    host, port = u.hostname, u.port or (443 if u.scheme == "https" else 80)
    path = (u.path or "/") + (("?" + u.query) if u.query else "")
    rec = {"domain": domain, "kind": kind, "url": url, "t_start": time.time()}
    t0 = time.perf_counter()
    try:
        t_dns0 = time.perf_counter()
        socket.getaddrinfo(host, port, proto=socket.IPPROTO_TCP)
        rec["t_dns"] = round(time.perf_counter() - t_dns0, 4)
        if u.scheme == "https":
            conn = http.client.HTTPSConnection(host, port, timeout=CONNECT_TIMEOUT, context=CTX)
        else:
            conn = http.client.HTTPConnection(host, port, timeout=CONNECT_TIMEOUT)
        t_c0 = time.perf_counter()
        conn.connect()
        rec["t_connect_tls"] = round(time.perf_counter() - t_c0, 4)
        conn.sock.settimeout(READ_TIMEOUT)
        conn.putrequest("GET", path, skip_accept_encoding=True)
        conn.putheader("User-Agent", UA)
        conn.putheader("Accept", "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8")
        conn.putheader("Accept-Encoding", "gzip, deflate")
        conn.putheader("Accept-Language", "de-DE,de;q=0.9,en;q=0.5")
        conn.endheaders()
        resp = conn.getresponse()
        rec["t_ttfb"] = round(time.perf_counter() - t0, 4)
        rec["status"] = resp.status
        rec["headers"] = [(k, v) for k, v in resp.getheaders()]
        body = b""
        while len(body) < MAX_BYTES:
            chunk = resp.read(65536)
            if not chunk:
                break
            body += chunk
        rec["truncated"] = len(body) >= MAX_BYTES
        conn.close()
        rec["wire_bytes"] = len(body)
        enc = (resp.getheader("Content-Encoding") or "").lower()
        try:
            if "gzip" in enc:
                body = gzip.decompress(body) if not rec["truncated"] else zlib.decompressobj(16 + zlib.MAX_WBITS).decompress(body)
            elif "deflate" in enc:
                body = zlib.decompress(body)
        except Exception as e:  # keep raw
            rec["decode_error"] = str(e)
        rec["body_bytes"] = len(body)
        rec["hdr_bytes"] = sum(len(k) + len(v) + 4 for k, v in rec["headers"])
        rec["_body"] = body
    except Exception as e:
        rec["error"] = f"{type(e).__name__}: {e}"
    rec["t_total"] = round(time.perf_counter() - t0, 4)
    return rec


def get(url, domain, kind, max_redirects=5):
    """GET with manual redirect following; every hop is logged as one request."""
    hops = []
    for _ in range(max_redirects + 1):
        r = one_request(url, domain, kind)
        body = r.pop("_body", b"")
        log({k: v for k, v in r.items()})
        hops.append(r)
        if r.get("status") in (301, 302, 303, 307, 308):
            loc = dict((k.lower(), v) for k, v in r["headers"]).get("location")
            if not loc:
                break
            url = urljoin(url, loc)
            continue
        return hops, body, url
    return hops, b"", url


def robots_allows(robots_txt, path):
    """Minimal RFC 9309 check for our UA token (fallback '*'); supports * and $."""
    import re
    groups, cur, last_was_ua = [], None, False
    for line in robots_txt.splitlines():
        line = line.split("#", 1)[0].strip()
        if ":" not in line:
            continue
        k, v = [x.strip() for x in line.split(":", 1)]
        k = k.lower()
        if k == "user-agent":
            if not last_was_ua:
                cur = {"agents": [], "rules": []}
                groups.append(cur)
            cur["agents"].append(v.lower())
            last_was_ua = True
        elif k in ("allow", "disallow") and cur is not None:
            cur["rules"].append((k, v))
            last_was_ua = False
        else:
            last_was_ua = False
    mine = [g for g in groups if any(UA_TOKEN in a for a in g["agents"])]
    if not mine:
        mine = [g for g in groups if "*" in g["agents"]]
    rules = [r for g in mine for r in g["rules"]]
    best = None
    for k, v in rules:
        if not v:
            continue
        pat = "^" + re.escape(v).replace(r"\*", ".*")
        if pat.endswith(r"\$"):
            pat = pat[:-2] + "$"
        if re.match(pat, path):
            if best is None or len(v) > len(best[1]) or (len(v) == len(best[1]) and k == "allow"):
                best = (k, v)
    return best is None or best[0] == "allow"


def save(domain, name, hops, body, final_url):
    d = os.path.join(RAW, domain)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, name + ".json"), "w") as f:
        json.dump({"final_url": final_url, "hops": hops}, f, indent=1)
    with gzip.open(os.path.join(d, name + ".body.gz"), "wb") as f:
        f.write(body)


def crawl_domain(domain):
    t0 = time.perf_counter()
    hops, body, final = get(f"https://{domain}/robots.txt", domain, "robots")
    if not hops[-1].get("status") and not hops[-1].get("error", "").startswith("HTTP"):
        # https failed completely -> try www
        hops2, body2, final2 = get(f"https://www.{domain}/robots.txt", domain, "robots")
        hops, body, final = hops + hops2, body2, final2
    save(domain, "robots", hops, body, final)
    st = hops[-1].get("status")
    robots_txt = body.decode("utf-8", "replace") if st == 200 else ""
    if st in (403, 429, 430, 503):
        return {"domain": domain, "skipped": f"robots status {st}", "t": time.perf_counter() - t0}
    if robots_txt and not robots_allows(robots_txt, "/"):
        return {"domain": domain, "skipped": "robots disallow /", "t": time.perf_counter() - t0}
    base = urlsplit(final)
    host_url = f"{base.scheme}://{base.netloc}/" if base.netloc else f"https://{domain}/"
    time.sleep(1.0)  # politeness gap per host
    hops, body, final = get(host_url, domain, "home")
    save(domain, "home", hops, body, final)
    return {"domain": domain, "final": final, "t": round(time.perf_counter() - t0, 2)}


def main():
    if sys.argv[1] == "--extra":
        domain, url = sys.argv[2], sys.argv[3]
        hops, body, final = get(url, domain, "extra")
        name = "extra_" + urlsplit(url).path.strip("/").replace("/", "_")
        save(domain, name, hops, body, final)
        print(json.dumps({"status": hops[-1].get("status"), "final": final, "body": body[:400].decode("utf-8", "replace")}))
        return
    rows = list(csv.DictReader(open(sys.argv[1])))
    workers = int(sys.argv[3]) if len(sys.argv) > 3 else 8
    t0 = time.perf_counter()
    with ThreadPoolExecutor(workers) as ex:
        for res in ex.map(crawl_domain, [r["domain"] for r in rows]):
            print(json.dumps(res))
    print("TOTAL_WALL", round(time.perf_counter() - t0, 2))


if __name__ == "__main__":
    main()
