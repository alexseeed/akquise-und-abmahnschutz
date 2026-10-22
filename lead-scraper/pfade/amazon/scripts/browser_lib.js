// Amazon-Leadliste: Browser-Bibliothek
// Per javascript_tool in eine amazon.de-Seite injizieren. Danach stehen bereit:
//   __feedInput()        - liest die hochgeladene Todo-Datei ein
//   __start(n)           - Seller-ID-Suche mit n Workern
//   __startImpressum(n)  - Impressum-Abruf mit n Workern
//   __stat()             - Fortschritt
//   __save(name)         - Ergebnis als Download
//   __toStorage()/__fromStorage() - Transfer in frischen Tab (2. Download)
//
// Warum die Dinge so sind, wie sie sind: siehe referenzen/browser-technik.md

(() => {
  const norm = s => (s || '').toLowerCase().replace(/[^a-z0-9]/g, '');
  const dec = s => { const t = document.createElement('textarea'); t.innerHTML = s; return t.value.trim(); };

  // Fetch mit Timeout. Ohne das blockiert ein einziger haengender Request
  // seinen Worker dauerhaft und der Durchsatz faellt auf null.
  const get = async (url) => {
    const ac = new AbortController();
    const t = setTimeout(() => ac.abort(), 15000);
    try {
      const r = await fetch(url, { credentials: 'include', signal: ac.signal });
      clearTimeout(t);
      return r.ok ? await r.text() : null;
    } catch (e) { clearTimeout(t); return null; }
  };

  // Verkaeufer aus Produktseite. Bewusst Regex statt DOMParser:
  // Amazon-Produktseiten sind ~1,8 MB. Nach ein paar hundert DOMParser-Aufrufen
  // friert der Renderer ein und selbst `1` als Ausdruck laeuft in ein CDP-Timeout.
  const sellerOf = (html) => {
    const k = html.indexOf('sellerProfileTriggerId');
    if (k < 0) return null;
    // Das href steht VOR dem id-Attribut -> rueckwaerts suchen, letzten Treffer nehmen.
    const back = html.slice(Math.max(0, k - 900), k);
    const fwd = html.slice(k, k + 600);
    const ids = [...back.matchAll(/seller=([A-Z0-9]{10,16})/g)];
    const id = ids.length ? ids[ids.length - 1][1] : null;
    const nm = (fwd.match(/>\s*([^<>]{1,80}?)\s*<\/a>/) || [])[1];
    return id ? { id, name: (nm || '').trim() } : null;
  };

  const lookup = async (brand, dominant) => {
    const out = { brand, dominant, sellerId: null, sellerName: null, method: null, checked: 0 };
    const s = await get('https://www.amazon.de/s?k=' + encodeURIComponent(brand));
    if (!s) { out.method = 'search_fail'; return out; }
    const bn = norm(brand);
    const asins = []; const seen = new Set();
    const re = /data-asin="([A-Z0-9]{10})"/g; let m;
    while ((m = re.exec(s))) {
      if (seen.has(m[1])) continue; seen.add(m[1]);
      // Treffer, die die Brand im Umfeld nennen, zuerst pruefen -> spart Seitenabrufe
      asins.push({ a: m[1], hit: norm(s.slice(m.index, m.index + 3000)).includes(bn) });
    }
    const order = [...asins.filter(x => x.hit), ...asins.filter(x => !x.hit)].slice(0, 6);
    for (const { a } of order) {
      out.checked++;
      const p = await get('https://www.amazon.de/dp/' + a);
      if (!p) continue;
      const sel = sellerOf(p);
      if (!sel) continue;
      // Nur exakter Name zaehlt. Suchergebnisse sind voller Fremdprodukte.
      if (norm(sel.name) === norm(dominant)) {
        out.sellerId = sel.id; out.sellerName = sel.name; out.method = 'exact_dominant';
        return out;
      }
      await new Promise(r => setTimeout(r, 120));
    }
    out.method = 'no_name_match';
    return out;
  };

  // Impressum. Die Feldnamen variieren je Verkaeufer, darum generisch alle
  // Label:Wert-Paare einsammeln statt feste Felder zu suchen.
  const impressum = async (id) => {
    const o = { id };
    const h = await get('https://www.amazon.de/sp?seller=' + id);
    if (!h) { o.err = 'fetch_fail'; return o; }
    let k = h.indexOf('Business-Verkäufer');
    if (k < 0) k = h.indexOf('Impressum');
    if (k < 0) { o.err = 'no_impressum_block'; return o; }
    const seg = h.slice(k, k + 5000);
    const nodes = [...seg.matchAll(/>\s*([^<>]{1,150}?)\s*</g)].map(m => dec(m[1])).filter(Boolean);
    const map = {};
    for (let j = 0; j < nodes.length; j++) {
      if (/:$/.test(nodes[j]) && nodes[j].length < 40) {
        const label = nodes[j].slice(0, -1);
        if (label === 'Geschäftsadresse') {
          map[label] = nodes.slice(j + 1, j + 6).filter(x => !/:$/.test(x)).join(', ').slice(0, 150);
        } else if (nodes[j + 1] && !/:$/.test(nodes[j + 1])) {
          map[label] = nodes[j + 1].slice(0, 150);
        }
      }
    }
    o.gname = map['Geschäftsname'] || null;
    o.gart = map['Geschäftsart'] || null;
    o.hr = map['Handelsregisternummer'] || null;
    o.addr = (map['Geschäftsadresse'] || '').replace(', Versandrichtlinien', '') || null;
    o.ustid = map['UStID'] || null;
    if (!o.gname) o.err = 'no_gname';
    return o;
  };

  window.__q = []; window.__out = [];

  const worker = async (fn) => {
    while (window.__q.length) {
      const job = window.__q.shift();
      try { window.__out.push(await fn(job)); }
      catch (e) { window.__out.push({ i: job.i, err: 'exception' }); }
      await new Promise(r => setTimeout(r, 120 + Math.random() * 200));
    }
  };

  // Datei-Input fuer den Upload-Weg. Massendaten durchzupasten kostet
  // zehntausende Tokens - der Upload kostet drei Calls.
  window.__feedInput = () => {
    let inp = document.getElementById('__feed');
    if (!inp) {
      inp = document.createElement('input');
      inp.type = 'file'; inp.id = '__feed';
      inp.style.cssText = 'position:fixed;top:0;left:0;z-index:999999';
      document.body.appendChild(inp);
      inp.addEventListener('change', async () => { window.__fed = JSON.parse(await inp.files[0].text()); });
    }
    return 'input bereit - jetzt file_upload auf dieses Element';
  };

  window.__start = (n = 6) => {
    if (!window.__fed) return 'FEHLER: keine Daten. Erst __feedInput() + file_upload.';
    // Erwartet [[index, brand, dominantSeller], ...]
    window.__q = window.__fed.map(x => ({ i: x[0], b: x[1], d: x[2] }));
    window.__out = []; window.__t0 = Date.now();
    for (let k = 0; k < Math.min(n, 8); k++) worker(async j => { const r = await lookup(j.b, j.d); r.i = j.i; return r; });
    return { queued: window.__q.length, workers: Math.min(n, 8) };
  };

  window.__startImpressum = (n = 6) => {
    if (!window.__fed) return 'FEHLER: keine Daten. Erst __feedInput() + file_upload.';
    // Erwartet ["SELLERID", ...]
    window.__q = window.__fed.map(id => ({ id }));
    window.__out = []; window.__t0 = Date.now();
    for (let k = 0; k < Math.min(n, 8); k++) worker(j => impressum(j.id));
    return { queued: window.__q.length, workers: Math.min(n, 8) };
  };

  window.__stat = () => ({
    done: window.__out.length,
    queued: window.__q.length,
    treffer: window.__out.filter(x => x.sellerId || x.gname).length,
    secs: window.__t0 ? Math.round((Date.now() - window.__t0) / 1000) : 0
  });

  window.__save = (name) => {
    const b = new Blob([JSON.stringify(window.__out)], { type: 'application/json' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(b); a.download = name;
    document.body.appendChild(a); a.click(); a.remove();
    return { exportiert: window.__out.length, datei: name };
  };

  // Chrome blockt den zweiten automatischen Download pro Tab stillschweigend.
  // Fuer weitere Downloads: __toStorage(), frischen Tab auf amazon.de oeffnen,
  // dort __fromStorage('name.json').
  window.__toStorage = () => {
    localStorage.setItem('__leaddata', JSON.stringify(window.__out));
    return { gesichert: window.__out.length };
  };
  window.__fromStorage = (name) => {
    const d = localStorage.getItem('__leaddata');
    if (!d) return 'FEHLER: nichts im localStorage';
    const b = new Blob([d], { type: 'application/json' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(b); a.download = name;
    document.body.appendChild(a); a.click(); a.remove();
    return { zeichen: d.length, datei: name };
  };

  return 'browser_lib bereit: __feedInput, __start, __startImpressum, __stat, __save';
})()
