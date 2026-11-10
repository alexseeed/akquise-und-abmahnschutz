#!/bin/sh
# Startet den Scraper mit dem ersten passenden Python (>= 3.10). Beispiel:
#   ./scraper.sh --kampagne steuerberater-bayern doctor
cd "$(dirname "$0")" || exit 1
for py in python3.13 python3.12 python3.11 python3.10 python3; do
  if command -v "$py" >/dev/null 2>&1 && "$py" -c 'import sys; sys.exit(sys.version_info < (3, 10))'; then
    exec "$py" -m scraper "$@"
  fi
done
echo "Python 3.10 oder neuer fehlt. macOS: brew install python@3.12" >&2
exit 1
