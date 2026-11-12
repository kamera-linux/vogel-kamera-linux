"""Atomares Schreiben von Einstellungsdateien.

Der Pi läuft am Akku und kann mitten im Schreiben ausgehen. Deshalb erst in eine
Temp-Datei im selben Verzeichnis schreiben, auf die Platte zwingen und dann per
os.replace() umbenennen: Die Zieldatei ist immer entweder alt oder neu, nie halb.
"""
import json
import os
import tempfile
from pathlib import Path


def write_json_atomic(path, data) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    # Eigene Temp-Datei je Aufruf: Der Server ist mehrthreadig, zwei gleichzeitige
    # Speichervorgänge dürfen sich die Temp-Datei nicht gegenseitig wegnehmen.
    fd, tmp = tempfile.mkstemp(dir=target.parent, prefix=f'.{target.name}.', suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as fh:
            fh.write(json.dumps(data, indent=2))
            fh.flush()
            os.fchmod(fh.fileno(), 0o644)   # wie bisher lesbar (mkstemp legt 0600 an)
            os.fsync(fh.fileno())
        os.replace(tmp, target)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
