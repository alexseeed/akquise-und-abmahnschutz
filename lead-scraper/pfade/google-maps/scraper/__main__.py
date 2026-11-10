import faulthandler
import os
import signal
import sys

# Diagnose: `kill -USR1 <pid>` schreibt die aktuelle Code-Stelle aller Threads nach stderr
faulthandler.register(signal.SIGUSR1, all_threads=True)

# --kampagne <name> muss vor dem Import der Konfiguration gesetzt sein: sie bestimmt Prompts,
# Datenbank und Exporte (kampagnen/<name>/). Funktioniert vor und nach dem Unterbefehl.
argv = sys.argv[1:]
for i, arg in enumerate(argv):
    if arg == "--kampagne" and i + 1 < len(argv):
        os.environ["KAMPAGNE"] = argv[i + 1]
        del argv[i:i + 2]
        break
    if arg.startswith("--kampagne="):
        os.environ["KAMPAGNE"] = arg.split("=", 1)[1]
        del argv[i]
        break

from .cli import main  # noqa: E402

sys.exit(main(argv))
