"""Host-level union of CrUX DE/AT/CH (www stripped) vs registrable domains; subdomain shop hosts."""
import gzip, csv, sys, re, collections
from urllib.parse import urlparse
SL2 = {"co.at","or.at","ac.at","gv.at"}
def reg(h):
    p = h.split('.')
    return '.'.join(p[-3:]) if len(p) >= 3 and '.'.join(p[-2:]) in SL2 else '.'.join(p[-2:])
hosts = {}; schemes = collections.Counter()
for path in sys.argv[1:]:
    with gzip.open(path, 'rt') as f:
        for row in csv.DictReader(f):
            u = urlparse(row['origin']); h = (u.hostname or '')
            schemes[u.scheme] += 1
            h2 = re.sub(r'^www\d?\.', '', h)
            r = int(row['rank'])
            if h2 not in hosts or r < hosts[h2]: hosts[h2] = r
regs = collections.defaultdict(list)
for h in hosts: regs[reg(h)].append(h)
multi = sum(1 for v in regs.values() if len(v) > 1)
sub = [h for h in hosts if h != reg(h)]
shopsub = [h for h in sub if re.match(r'^(shop|store|onlineshop|webshop|b2b|b2c)\.', h)]
print('origins schemes', dict(schemes))
print('unique hosts (www stripped)', len(hosts), ' registrable', len(regs), ' regs with >1 host', multi)
print('non-apex hosts', len(sub), ' of which shop./store./onlineshop./webshop./b2b./b2c.', len(shopsub))
print('example shop subdomains', shopsub[:8])
