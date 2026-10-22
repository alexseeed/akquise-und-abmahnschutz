"""Crawl-plan sizing on CrUX DE/AT/CH 202608 at host level (offline): apex vs non-apex hosts, rank buckets.
Simplified PSL (2-label + common 3-label suffixes) as in crux_hosts.py -> approximate."""
import gzip, csv, sys, re, collections
from urllib.parse import urlparse
SL2 = {"co.at","or.at","ac.at","gv.at","co.uk","com.au","co.jp","com.br","com.tr","co.za","com.cn","co.in","com.mx"}
def reg(h):
    p = h.split('.')
    return '.'.join(p[-3:]) if len(p) >= 3 and '.'.join(p[-2:]) in SL2 else '.'.join(p[-2:])
hosts = {}; http_only = set(); https = set()
for path in sys.argv[1:]:
    with gzip.open(path, 'rt') as f:
        for row in csv.DictReader(f):
            u = urlparse(row['origin']); h = re.sub(r'^www\d?\.', '', u.hostname or '')
            if not h: continue
            (https if u.scheme == 'https' else http_only).add(h)
            r = int(row['rank'])
            if h not in hosts or r < hosts[h]: hosts[h] = r
apex = {h for h in hosts if h == reg(h)}
non_apex = [h for h in hosts if h != reg(h)]
orphan = [h for h in non_apex if reg(h) not in apex]       # subdomain whose company apex is NOT in CrUX
shopish = re.compile(r'^(shop|store|onlineshop|webshop|b2b|b2c|haendler|bestellen|order|kaufen|outlet)\.')
shop_sub = [h for h in non_apex if shopish.match(h)]
plan = apex | set(orphan) | set(shop_sub)
print('hosts', len(hosts), ' apex', len(apex), ' non-apex', len(non_apex))
print('non-apex whose apex not in CrUX (orphan)', len(orphan), ' shop-like non-apex', len(shop_sub))
print('PLAN = apex + orphan + shop-like non-apex:', len(plan), f'({len(plan)/len(hosts):.1%} of hosts)')
print('http-only hosts (no https origin):', len(http_only - https))
b = collections.Counter(hosts[h] for h in plan); cum = 0
for r in sorted(b):
    cum += b[r]; print(f'  plan rank<={r:>8}: {b[r]:>8}  cum {cum:>8}')
dach = sum(1 for h in plan if h.rsplit('.',1)[-1] in ('de','at','ch'))
print('plan hosts on .de/.at/.ch:', dach)
