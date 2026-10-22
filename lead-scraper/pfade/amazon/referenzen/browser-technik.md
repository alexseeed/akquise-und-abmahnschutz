# Browser-Technik: warum die Pipeline so gebaut ist

Alles hier ist teuer erkauft. Wer davon abweicht, landet in denselben Sackgassen.

## Inhalt

- [Der Grundtrick: same-origin](#der-grundtrick-same-origin)
- [Daten rein: Datei-Upload statt Paste](#daten-rein)
- [Daten raus: Download in den Downloads-Ordner](#daten-raus)
- [Der zweite Download wird geblockt](#der-zweite-download-wird-geblockt)
- [Warum Regex statt DOMParser](#warum-regex-statt-domparser)
- [Der eingefrorene Renderer](#der-eingefrorene-renderer)
- [Das href steht vor der id](#das-href-steht-vor-der-id)
- [CORS: was NICHT geht](#cors-was-nicht-geht)
- [Polling-Rhythmus](#polling-rhythmus)

## Der Grundtrick: same-origin

Der Chrome-MCP kann JavaScript im Kontext einer Seite ausführen. Steht diese Seite auf `amazon.de`, darf sie beliebig viele `fetch()`-Aufrufe an `amazon.de` machen — dieselbe Origin, kein CORS, und die Amazon-Session-Cookies gehen automatisch mit.

Das dreht das Kostenmodell um. Statt „ein Tool-Call pro Seite" wird daraus „ein Tool-Call pro *Batch*": Ein Worker-Pool in der Seite arbeitet hunderte Brands ab, parst im Seitenkontext und behält nur die extrahierten Felder. Amazon-Produktseiten sind ~1,8 MB — die dürfen nie in dein Kontextfenster.

Gemessen: ~1.500 Brands in ~30 Minuten mit ~40 Tool-Calls. Der naive Weg (navigate + read_page pro Seite) wären >4.000 Calls und Millionen Tokens.

**Voraussetzung:** Der Tab muss auf einer echten amazon.de-Seite stehen. `about:blank` oder `chrome://newtab` haben eine andere Origin und alle fetches scheitern.

## Daten rein

1.500 Brands in einen `javascript_tool`-Aufruf zu pasten kostet ~40k Tokens. Der Umweg über einen Datei-Upload kostet drei Calls:

1. `__feedInput()` legt ein `<input type="file">` in die Seite.
2. `mcp__claude-in-chrome__find` mit einer Query wie `input type file element` — der Treffer heißt z.B. `ref_2496`. `read_page` funktioniert auf Amazon-Seiten **nicht**, die sind zu groß für das Limit.
3. `mcp__claude-in-chrome__file_upload` mit `ref` und dem **Host-Pfad** der Datei (`/Users/<name>/Downloads/todo.json`), nicht dem Sandbox-Pfad.

Die Datei muss in einem verbundenen Ordner liegen. Notfalls den Downloads-Ordner für diese Sitzung freigeben lassen (Ordnerzugriff anfragen).

## Daten raus

Der Rückkanal von `javascript_tool` ist auf **~1.000 Zeichen** begrenzt und schneidet danach hart ab. Für 1.500 Ergebnisse völlig unbrauchbar.

Lösung: `__save('name.json')` erzeugt einen Blob-Download. Die Datei landet im Downloads-Ordner des Users. Ist der als Cowork-Ordner verbunden, liest man sie direkt per bash. Deshalb Downloads früh einbinden.

## Der zweite Download wird geblockt

Chrome erlaubt pro Tab **einen** automatischen Download. Der zweite wird stillschweigend verworfen — kein Fehler, keine Meldung, die Datei erscheint einfach nicht. Das kostet garantiert Zeit, wenn man es nicht weiß.

Umweg für jeden weiteren Export:

```js
__toStorage()                    // im Arbeits-Tab
```
Dann neuen Tab öffnen, auf `https://www.amazon.de/robots.txt` navigieren (winzige Seite, gleiche Origin), dort:
```js
__fromStorage('name.json')
```

`localStorage` ist origin-weit geteilt, der frische Tab hat sein eigenes Download-Kontingent. Prüf nach jedem Export mit `ls`, ob die Datei wirklich da ist.

## Warum Regex statt DOMParser

`new DOMParser().parseFromString(html)` auf einer 1,8-MB-Seite ist bequem und funktioniert — für die ersten paar hundert Aufrufe. Danach frisst der Speicherdruck den Renderer auf: Der Durchsatz fällt von ~4/s auf ~0,1/s, und irgendwann läuft selbst `1` als Ausdruck in ein CDP-Timeout.

Das sieht aus wie Amazon-Throttling. Ist es aber nicht — ein frischer Tab holt dieselbe Seite in 900 ms. Regex auf dem HTML-String hat dieses Problem nicht.

**Wenn der Durchsatz einbricht:** Nicht auf Amazon schimpfen. Frischen Tab öffnen und dort weitermachen. Vorher `__toStorage()` oder `__save()`, sonst sind die Ergebnisse weg.

## Der eingefrorene Renderer

Mehr als ~8 Worker parallel bringen keinen Durchsatz mehr, sondern frieren den Tab ein. Bei 6 ist es stabil.

Friert er trotzdem ein: 40-60 Sekunden warten, ohne neue Calls zu feuern. Meist kommt er zurück. Dann sofort exportieren.

## Das href steht vor der id

Auf der Produktseite sieht der Verkäufer-Link so aus:

```html
<a href="/sp?...seller=A1H05RYQWRY6GC..." id="sellerProfileTriggerId">GreatStarTools</a>
```

Das `href` steht **vor** dem `id`-Attribut. Wer ab `sellerProfileTriggerId` vorwärts nach `seller=` sucht, findet nichts und bekommt stumm null Treffer bei voller Trefferquote-Illusion. Also: rückwärts nach der ID suchen, vorwärts nach dem Namen.

Als Gegenprobe taugt `"merchantId":"..."` im Seiten-JSON — das ist der Buy-Box-Verkäufer.

## CORS: was NICHT geht

Der same-origin-Trick endet an der Domain-Grenze. Aus einer amazon.de-Seite heraus schlägt jedes `fetch()` auf fremde Hosts fehl — getestet mit Firmenwebsites, DuckDuckGo und Bing, alle `TypeError: Failed to fetch`. `mode: 'no-cors'` liefert eine opake Antwort, die man nicht lesen kann.

Deshalb läuft Phase 4 über Subagenten und nicht über den Browser. Nicht versuchen, das zu umgehen.

## Polling-Rhythmus

Der CDP-Aufruf läuft nach **45 Sekunden** in ein Timeout. Ein `await new Promise(r => setTimeout(r, 35000))` gefolgt von `__stat()` passt sicher darunter.

Das Timeout ist harmlos — die Worker laufen in der Seite weiter. Einfach nochmal `__stat()` abfragen.
