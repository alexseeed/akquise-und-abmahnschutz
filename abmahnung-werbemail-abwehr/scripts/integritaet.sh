#!/usr/bin/env bash
# SHA-256 über alle Dateien eines Beweispakets + zwei RFC-3161-Zeitstempel + Prüfanleitung.
# Aufruf: bash integritaet.sh <paket-ordner>
set -euo pipefail
PAKET="${1:?Paket-Ordner angeben}"
cd "$PAKET"
mkdir -p 03_integritaet
find . -type f ! -path "./03_integritaet/*" -print0 | sort -z | xargs -0 sha256sum > 03_integritaet/SHA256SUMS.txt
cd 03_integritaet
ANZ=$(wc -l < SHA256SUMS.txt)
SUM=$(sha256sum SHA256SUMS.txt | cut -d' ' -f1)
openssl ts -query -data SHA256SUMS.txt -sha256 -cert -out SHA256SUMS.tsq 2>/dev/null

# Zeitstempeldienste in Reihenfolge; die ersten zwei erfolgreichen werden verwendet
DIENSTE=("DFN|https://zeitstempel.dfn.de" "Sectigo|https://timestamp.sectigo.com" "SwissSign|https://tsa.swisssign.net" "aimoda|https://rfc3161.ai.moda")
OK=0; BERICHT=""
for d in "${DIENSTE[@]}"; do
  [ "$OK" -ge 2 ] && break
  N="${d%%|*}"; U="${d#*|}"
  if curl -sS --max-time 30 -H "Content-Type: application/timestamp-query" --data-binary @SHA256SUMS.tsq -o "SHA256SUMS_$N.tsr" "$U" \
     && openssl ts -reply -in "SHA256SUMS_$N.tsr" -text 2>/dev/null | grep -q "Status: Granted"; then
    openssl ts -reply -in "SHA256SUMS_$N.tsr" -token_out -out "tok_$N.der" 2>/dev/null
    openssl pkcs7 -inform DER -in "tok_$N.der" -print_certs -out "SHA256SUMS_${N}_zertifikatskette.pem" 2>/dev/null
    rm -f "tok_$N.der"
    ZEIT=$(openssl ts -reply -in "SHA256SUMS_$N.tsr" -text 2>/dev/null | sed -n 's/^Time stamp: //p')
    SER=$(openssl ts -reply -in "SHA256SUMS_$N.tsr" -text 2>/dev/null | sed -n 's/^Serial number: //p')
    # Prüfung: erst gegen System-Wurzeln, sonst gegen die mitgelieferte Kette (Wurzel-Fingerabdruck dann extern abgleichen)
    if openssl ts -verify -data SHA256SUMS.txt -in "SHA256SUMS_$N.tsr" -CAfile /etc/ssl/certs/ca-certificates.crt \
         -untrusted "SHA256SUMS_${N}_zertifikatskette.pem" >/dev/null 2>&1; then
      PRUEF="Verification: OK (öffentliche Wurzelzertifikate)"
      CMD="openssl ts -verify -data SHA256SUMS.txt -in SHA256SUMS_$N.tsr -CAfile /etc/ssl/certs/ca-certificates.crt -untrusted SHA256SUMS_${N}_zertifikatskette.pem"
    elif openssl ts -verify -data SHA256SUMS.txt -in "SHA256SUMS_$N.tsr" -CAfile "SHA256SUMS_${N}_zertifikatskette.pem" >/dev/null 2>&1; then
      FP=$(awk '/BEGIN/{i++} i==1' "SHA256SUMS_${N}_zertifikatskette.pem" | openssl x509 -noout -fingerprint -sha256 2>/dev/null | cut -d= -f2)
      PRUEF="Verification: OK (gegen mitgelieferte Kette; Wurzel-Fingerabdruck SHA-256 $FP beim Anbieter abgleichen)"
      CMD="openssl ts -verify -data SHA256SUMS.txt -in SHA256SUMS_$N.tsr -CAfile SHA256SUMS_${N}_zertifikatskette.pem"
    else
      PRUEF="Verifikation fehlgeschlagen"; CMD=""
    fi
    echo "$N: $ZEIT – $PRUEF"
    BERICHT+="
$N ($U)
  Stempelzeit:   $ZEIT
  Seriennummer:  $SER
  Ergebnis:      $PRUEF
  Prüfbefehl:    $CMD
"
    OK=$((OK+1))
  else
    rm -f "SHA256SUMS_$N.tsr"
    echo "$N: nicht erreichbar oder abgelehnt"
  fi
done

cat > PRUEFANLEITUNG.txt <<EOF
PRÜFANLEITUNG – Integrität des Beweispakets

SHA256SUMS.txt enthält die SHA-256-Prüfsummen von $ANZ Dateien (alle Ordner außer 03_integritaet).
Prüfsumme von SHA256SUMS.txt: $SUM

Zeitstempel nach RFC 3161 auf SHA256SUMS.txt ($OK Dienst(e)):
$BERICHT
Was die Zeitstempel belegen: Die Datei SHA256SUMS.txt existierte zum Stempelzeitpunkt in genau
dieser Form. Stimmen die Prüfsummen später überein, wurde keine Beweisdatei nachträglich verändert.

Schritt 1 – Dateien prüfen (im entpackten Hauptordner):
    sha256sum -c 03_integritaet/SHA256SUMS.txt          (macOS: shasum -a 256 -c …)
    Windows (PowerShell, Einzeldatei): Get-FileHash -Algorithm SHA256 .\\00_Beweisprotokoll.pdf
Erwartet: für jede Datei "OK". Bei Teilpaketen meldet die Prüfung fehlende Dateien als nicht gefunden.

Schritt 2 – Zeitstempel prüfen (im Ordner 03_integritaet): Prüfbefehle oben.
Zeitstempel im Klartext: openssl ts -reply -in SHA256SUMS_<Dienst>.tsr -text

Keine Datei öffnen und erneut speichern – das ändert die Prüfsumme. Original-ZIP unverändert
auf zwei Datenträgern aufbewahren.
EOF
echo "Fertig: $ANZ Dateien gehasht, $OK Zeitstempel. Siehe 03_integritaet/PRUEFANLEITUNG.txt"
[ "$OK" -ge 1 ] || { echo "WARNUNG: kein Zeitstempel erhalten"; exit 1; }
