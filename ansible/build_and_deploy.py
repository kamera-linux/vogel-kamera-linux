#!/usr/bin/env python3
# Abhängigkeiten: pip install python-dotenv ansible  (z.B. in ~/ansible-venv oder ./ansible-venv-local)
"""build_and_deploy.py – Docker-Image bauen und auf Pi deployen

Verwendung (aus dem ansible/-Ordner oder Repo-Root):
  ./ansible/build_and_deploy.py --install      # Vollständiges Erstdeployment
  ./ansible/build_and_deploy.py --update       # Nur Image aktualisieren (schnell)
  ./ansible/build_and_deploy.py --build        # Nur bauen, nicht deployen
  ./ansible/build_and_deploy.py --setup-host   # Gentoo Build-Host einrichten (Docker, QEMU, buildx)

Voraussetzungen (einmalig):
  1. Virtual Environment mit Ansible:
     cd <repo-root>
     python3 -m venv ansible-venv-local --copies
     ansible-venv-local/bin/pip install ansible python-dotenv pyotp
  2. docker buildx create --use --name pi-builder  (oder: --setup-host)
  3. ansible-vault encrypt ansible/group_vars/all/vault.yml
  4. echo 'VaultPasswort' > ~/.pi-daemon-vault-pass && chmod 600 ~/.pi-daemon-vault-pass
  5. (Optional) bash ansible/setup-sudo-nopasswd.sh  # Sudo ohne Passwort für Docker

Hinweis: Der Build fragt nach dem Sudo-Passwort für docker systemctl restart.
Geben Sie 'bash ansible/setup-sudo-nopasswd.sh' ein, um dies zu automatisieren
(setzt NOPASSWD-Regeln in /etc/sudoers.d/vogel-kamera-buildx).
"""

import argparse
import json
import os
import shutil
import ssl
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

try:
    from dotenv import dotenv_values
except ImportError:
    print("❌ python-dotenv nicht installiert: pip install python-dotenv", file=sys.stderr)
    sys.exit(1)

# ── ANSI-Farben ──────────────────────────────────────────────────────────────
BOLD   = "\033[1m"
GREEN  = "\033[32m"
YELLOW = "\033[33m"
RED    = "\033[31m"
RESET  = "\033[0m"

def bold(s: str)   -> str: return f"{BOLD}{s}{RESET}"
def green(s: str)  -> str: return f"{GREEN}{s}{RESET}"
def yellow(s: str) -> str: return f"{YELLOW}{s}{RESET}"
def red(s: str)    -> str: return f"{RED}{s}{RESET}"

# ── Pfade ────────────────────────────────────────────────────────────────────
SCRIPT_DIR  = Path(__file__).resolve().parent
REPO_ROOT   = SCRIPT_DIR.parent
ANSIBLE_DIR = SCRIPT_DIR
DOCKERFILE  = REPO_ROOT / "docker" / "Dockerfile"
IMAGE_NAME  = "vogel-pi"
IMAGE_TAG   = "latest"
ARCHIVE     = Path("/tmp/vogel-pi.tar.gz")

# ── SSL-Kontext (self-signed) ─────────────────────────────────────────────────
_SSL_CTX = ssl.create_default_context()
_SSL_CTX.check_hostname = False
_SSL_CTX.verify_mode    = ssl.CERT_NONE


# ── Argumente ─────────────────────────────────────────────────────────────────
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog=Path(__file__).name,
        description="Vogel-Kamera – Build & Deploy",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    grp = parser.add_mutually_exclusive_group()
    grp.add_argument("--install",    dest="mode", action="store_const", const="deploy",
                     help="Vollständiges Erstdeployment (Docker, SSL, Firewall, systemd)")
    grp.add_argument("--update",     dest="mode", action="store_const", const="update",
                     help="Nur Image + .env aktualisieren (schnell)")
    grp.add_argument("--build",      dest="mode", action="store_const", const="build",
                     help="Nur Docker-Image bauen, kein Deploy")
    grp.add_argument("--setup-host", dest="mode", action="store_const", const="setup-host",
                     help="Gentoo Build-Host einrichten (Docker, QEMU aarch64, buildx)")
    grp.add_argument("--hotpatch",   dest="mode", action="store_const", const="hotpatch",
                     help="pi_daemon_secure.py direkt in Container kopieren + Neustart (kein Image-Rebuild)")
    parser.add_argument("--no-cache", action="store_true",
                        help="Docker Build-Cache ignorieren (sauberer Rebuild)")
    parser.add_argument("--e2e",      action="store_true",
                        help="E2E-Test nach Deploy (oder solo: nur testen, kein Build)")
    args = parser.parse_args()
    # Mode ableiten: nur --e2e → "e2e", kein Flag → "deploy"
    if args.mode is None:
        args.mode = "e2e" if args.e2e else "deploy"
    return args


# ── .env laden ────────────────────────────────────────────────────────────────
def load_env() -> dict:
    env_file = ANSIBLE_DIR / ".env"
    if not env_file.exists():
        print(red(f"❌ Keine .env gefunden: {env_file}"), file=sys.stderr)
        print( "   Einmalig anlegen:", file=sys.stderr)
        print(r"   cp ansible/.env.example ansible/.env && ${EDITOR:-nano} ansible/.env", file=sys.stderr)
        sys.exit(1)
    env = dict(dotenv_values(env_file))
    for key in ("PI_HOST", "PI_USER", "PI_SSH_KEY"):
        if not env.get(key):
            print(red(f"❌ {key} nicht in .env gesetzt"), file=sys.stderr)
            sys.exit(1)
    env["PI_SSH_KEY"] = str(Path(env["PI_SSH_KEY"]).expanduser())
    # Ansible liest PI_HOST/PI_USER/PI_SSH_KEY per lookup('env', ...) aus der
    # Prozessumgebung – daher alle .env-Werte exportieren (wie bash: set -a; source .env)
    os.environ.update(env)
    return env


# ── Tool-Lookups ─────────────────────────────────────────────────────────────
def find_tool(name: str) -> str | None:
    """Sucht Tool in bekannten Venv-Verzeichnissen, dann im PATH."""
    # Lokale Venvs haben Priorität vor PATH (kann alte, beschädigte Installationen überschreiben)
    for d in (
        REPO_ROOT / "ansible-venv-local" / "bin",
        REPO_ROOT / ".venv" / "bin",
        Path.home() / "ansible-venv" / "bin",
    ):
        candidate = d / name
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    # Dann im PATH suchen
    if path := shutil.which(name):
        return path
    # Fallback: .local/bin als letztes (kann alte Installation sein)
    candidate = Path.home() / ".local" / "bin" / name
    if candidate.is_file() and os.access(candidate, os.X_OK):
        return str(candidate)
    return None


def require_tool(name: str) -> str:
    if path := find_tool(name):
        return path
    print(red(f"❌ '{name}' nicht gefunden."), file=sys.stderr)
    if name == "ansible-playbook":
        print("   Bitte installieren Sie Ansible in einem venv:", file=sys.stderr)
        print(f"   cd {REPO_ROOT}", file=sys.stderr)
        print("   python3 -m venv ansible-venv-local --copies", file=sys.stderr)
        print("   ansible-venv-local/bin/pip install ansible python-dotenv pyotp", file=sys.stderr)
    sys.exit(1)


# ── subprocess-Helfer ─────────────────────────────────────────────────────────
def run(cmd: list, **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=True, **kwargs)


def run_capture(cmd: list) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True)


# ── Uptime-Statistik aus journalctl seeden ────────────────────────────────────
def seed_uptime_stats(env: dict) -> None:
    """Liest journalctl --list-boots vom Pi-Host per SSH und schreibt uptime_stats.json."""
    import re, json as _json, tempfile, os
    from datetime import datetime as _dt, timedelta as _td

    pi_user = env["PI_USER"]
    pi_host = env["PI_HOST"]
    pi_key  = env["PI_SSH_KEY"]

    print("   📊 Laufzeitstatistik aus journalctl laden... ", end="", flush=True)
    r = run_capture([
        "ssh", "-i", pi_key, "-o", "BatchMode=yes",
        f"{pi_user}@{pi_host}",
        "journalctl --list-boots --no-pager -q 2>/dev/null",
    ])
    if r.returncode != 0 or not r.stdout.strip():
        print(yellow("⚠ journalctl --list-boots nicht verfügbar, übersprungen."))
        return

    # Flexibles Regex – unterstützt beide Formate:
    # Mit Boot-ID:  " -3 c67176... Fri 2026-04-03 18:56:26 CEST  Sat 2026-04-04 17:57:44 CEST"
    # Ohne Boot-ID: " -3  Fri 2026-04-03 18:56:26 → Sat 2026-04-04 17:57:44"
    # Laufend:      "  0  Sun 2026-04-05 18:09:40 → laufend" (kein End-Datum → ignoriert)
    pat = re.compile(
        r'^\s*[-\d]+\s+'
        r'(?:[0-9a-f]{20,}\s+)?'          # Boot-ID: optional (20+ Hex-Zeichen)
        r'(?:\w{3}\s+)?(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2}:\d{2})(?:\s+\S+)?'
        r'\s+(?:→\s+)?'                    # Trenner: whitespace + optional "→ "
        r'(?:\w{3}\s+)?(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2}:\d{2})',
        re.MULTILINE,
    )

    daily: dict[str, float] = {}
    total_s: float = 0.0

    for m in pat.finditer(r.stdout):
        start_date, start_time, end_date, end_time = m.groups()
        try:
            start = _dt.fromisoformat(f"{start_date}T{start_time}")
            end   = _dt.fromisoformat(f"{end_date}T{end_time}")
            if end <= start:
                continue
            # Boot über Mitternacht aufteilen
            cur = start
            while cur < end:
                day_key  = cur.strftime('%Y-%m-%d')
                day_end  = _dt.fromisoformat(f"{day_key}T23:59:59") + _td(seconds=1)
                seg_end  = min(end, day_end)
                seg_s    = (seg_end - cur).total_seconds()
                daily[day_key] = daily.get(day_key, 0.0) + seg_s
                total_s += seg_s
                cur = seg_end
        except Exception:
            continue

    if not daily:
        print(yellow("⚠ Keine Boot-Einträge geparst."))
        return

    # Bestehende Datei auf dem Pi lesen (nicht überschreiben falls neuer)
    existing_raw = run_capture([
        "ssh", "-i", pi_key, "-o", "BatchMode=yes",
        f"{pi_user}@{pi_host}",
        "cat /etc/pi-daemon/uptime_stats.json 2>/dev/null || echo '{}'",
    ])
    existing: dict = {}
    try:
        existing = _json.loads(existing_raw.stdout)
    except Exception:
        pass

    existing_total = float(existing.get("total_seconds", 0))
    existing_daily: dict = existing.get("daily", {})

    # journalctl-Werte gewinnen (sind präziser als akkumulierte), per Tag mergen
    merged_daily = dict(existing_daily)
    for day, secs in daily.items():
        # Journalctl-Wert übernehmen wenn größer (= realer Wert)
        merged_daily[day] = max(merged_daily.get(day, 0.0), secs)

    merged_total = max(existing_total, total_s)

    # Einträge >90 Tage entfernen
    from datetime import date as _date
    cutoff = (_date.today() - _td(days=90)).isoformat()
    merged_daily = {k: v for k, v in merged_daily.items() if k >= cutoff}

    stats_json = _json.dumps({
        "total_seconds": int(merged_total),
        "daily": {k: int(v) for k, v in sorted(merged_daily.items())},
    }, indent=2)

    # Datei per SCP nach /tmp/ schreiben, dann per docker cp in den Container
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(stats_json)
            tmp_local = f.name

        scp_r = run_capture([
            "scp", "-i", pi_key,
            tmp_local,
            f"{pi_user}@{pi_host}:/tmp/uptime_stats_seed.json",
        ])
        os.unlink(tmp_local)

        if scp_r.returncode != 0:
            print(yellow("⚠ SCP nach /tmp/ fehlgeschlagen."))
            return

        # Container-ID ermitteln (laufender pi-daemon)
        cid_r = run_capture([
            "ssh", "-i", pi_key, "-o", "BatchMode=yes",
            f"{pi_user}@{pi_host}",
            "docker ps --filter name=pi-daemon --format '{{.ID}}' | head -1",
        ])
        cid = cid_r.stdout.strip()
        if cid:
            cp_r = run_capture([
                "ssh", "-i", pi_key, "-o", "BatchMode=yes",
                f"{pi_user}@{pi_host}",
                f"docker cp /tmp/uptime_stats_seed.json {cid}:/config/uptime_stats.json"
                f" && rm /tmp/uptime_stats_seed.json",
            ])
            ok = cp_r.returncode == 0
        else:
            # Fallback: sudo mv direkt nach /etc/pi-daemon/
            mv_r = run_capture([
                "ssh", "-i", pi_key, "-o", "BatchMode=yes",
                f"{pi_user}@{pi_host}",
                "sudo mv /tmp/uptime_stats_seed.json /etc/pi-daemon/uptime_stats.json",
            ])
            ok = mv_r.returncode == 0

        if ok:
            days_str = ', '.join(f"{k}: {int(v)//3600}h{(int(v)%3600)//60:02d}m"
                                 for k, v in sorted(merged_daily.items())[-3:])
            print(green(f"✅  ({days_str})"))
        else:
            print(yellow("⚠ Schreiben in Container fehlgeschlagen."))
    except Exception as exc:
        print(yellow(f"⚠ Fehler: {exc}"))


# ── HTTP-Helfer (urllib, kein requests nötig) ─────────────────────────────────
def http_get(url: str, headers: dict | None = None) -> tuple[int, dict]:
    req = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(req, context=_SSL_CTX, timeout=5) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        try:    return e.code, json.loads(e.read())
        except Exception: return e.code, {}
    except Exception:
        return 0, {}


def http_post(url: str, payload: dict, headers: dict | None = None) -> tuple[int, dict]:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        method="POST",
        headers={"Content-Type": "application/json", **(headers or {})},
    )
    try:
        with urllib.request.urlopen(req, context=_SSL_CTX, timeout=5) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        try:    return e.code, json.loads(e.read())
        except Exception: return e.code, {}
    except Exception:
        return 0, {}


# ── SSH-Verbindungscheck ──────────────────────────────────────────────────────
def check_ssh(env: dict) -> None:
    print("🔗 SSH-Verbindung zum Pi... ", end="", flush=True)
    r = run_capture([
        "ssh", "-i", env["PI_SSH_KEY"],
        "-o", "ConnectTimeout=5", "-o", "BatchMode=yes",
        f"{env['PI_USER']}@{env['PI_HOST']}", "echo", "ok",
    ])
    if r.returncode != 0:
        print(red("FEHLER"))
        print(f"   Kann {env['PI_USER']}@{env['PI_HOST']} nicht erreichen.", file=sys.stderr)
        sys.exit(1)
    print(green("OK"))


# ── Setup-Host ────────────────────────────────────────────────────────────────
def setup_host() -> None:
    ansible = require_tool("ansible-playbook")
    print(bold("🔧 Gentoo Build-Host einrichten (Docker, QEMU, buildx)..."))
    print("   Benötigt sudo/become – bitte Passwort eingeben.\n")
    run([ansible, str(ANSIBLE_DIR / "playbooks" / "setup-build-host.yml"), "--ask-become-pass"])
    print(f"\n{green(bold('✅ Build-Host eingerichtet.'))}")
    print("   Bitte neu einloggen oder 'newgrp docker' ausführen.")
    print("   Danach: ./ansible/build_and_deploy.py --install")


# ── QEMU binfmt-Handler ────────────────────────────────────────────────────────
def ensure_qemu_binfmt_handlers() -> None:
    """Aktualisiert QEMU-Emulatoren für ARM64 Cross-Compilation.
    
    Gentoo + Hardened-Kernel: QEMU aarch64 segfault bei ASLR (randomize_va_space=2).
    Workaround: tonistiigi/binfmt mit aktuellen Patches installieren.
    
    Siehe: https://github.com/tonistiigi/binfmt/issues/215
           https://github.com/docker/buildx/issues/3170
    """
    print(yellow("🔄 QEMU binfmt-Handler aktualisieren (tonistiigi/binfmt)..."))
    try:
        # Deinstalliere alte QEMU-Versionen
        run_capture(["docker", "run", "--privileged", "--rm", "tonistiigi/binfmt", 
                     "--uninstall", "qemu-*"])
        
        # Installiere alle Emulatoren (mit aktuellen Workarounds für Gentoo/ASLR)
        result = run(["docker", "run", "--privileged", "--rm", "tonistiigi/binfmt",
                      "--install", "all"])
        
        # Docker-Daemon neu starten, um Handler zu laden
        print(yellow("   🔄 Docker-Daemon wird neu gestartet..."))
        run(["sudo", "systemctl", "restart", "docker"])
        time.sleep(3)  # Gib Docker Zeit zum Hochfahren
        
        print(green("   ✅ binfmt-Handler aktualisiert"))
    except Exception as e:
        print(yellow(f"   ⚠ binfmt-Update fehlgeschlagen: {e}"))
        print("   (Weitermachen – fallback auf existierenden Builder)")


# ── Docker Build ──────────────────────────────────────────────────────────────
def docker_build(no_cache: bool) -> None:
    """Baut ARM64 Docker-Image mit buildx für Raspberry Pi Deployment.
    
    **Gentoo x86_64 → ARM64 Cross-Compilation:**
    - Verwendet tonistiigi/binfmt für QEMU aarch64 Emulation
    - Nutzt den stabilen 'default' docker-driver Builder
    - Vermeidet gRPC-Fehler beim Erstellen neuer docker-container-driver Builder
    
    **Fehlerbehandlung bei gRPC Frame-Größe (v2.3.2+):**
    - Symptom: "error reading server preface: http2: frame too large"
    - Ursache: QEMU aarch64 Segfault auf Gentoo Hardened-Kernel (ASLR-Patches)
    - Lösung: ensure_qemu_binfmt_handlers() + docker-driver Builder
    
    Siehe auch: ansible/README.md "QEMU binfmt-Handler · Laufzeit-Updates"
    """
    # ── Stelle sicher, dass QEMU binfmt-Handler aktuell sind ────────────────
    ensure_qemu_binfmt_handlers()
    
    # ── Nutze den default builder (der bereits auf Gentoo funktioniert) ────────
    print(yellow("📍 Verwende docker buildx 'default' Builder..."))
    run(["docker", "buildx", "use", "default"])
    
    print(f"\n{bold('📦 Baue Docker-Image für linux/arm64...')}")
    print(f"   Dockerfile: {DOCKERFILE}")
    print(f"   Build-Kontext: {REPO_ROOT}\n")
    if no_cache:
        print(yellow("⚠ --no-cache: Build-Cache wird ignoriert"))

    cmd = [
        "docker", "buildx", "build",
        "--platform", "linux/arm64",
        "--file", str(DOCKERFILE),
        "--tag", f"{IMAGE_NAME}:{IMAGE_TAG}",
        "--load",
        str(REPO_ROOT),
    ]
    if no_cache:
        cmd.append("--no-cache")
    run(cmd)
    print(green(f"✅ Image gebaut: {IMAGE_NAME}:{IMAGE_TAG}"))

    # ── Lokales Cleanup: dangling images entfernen ────────────────────────
    try:
        prune = run_capture(["docker", "image", "prune", "-f"])
        stdout = prune.stdout or ""
        reclaimed = next((l for l in stdout.splitlines() if "reclaimed" in l.lower()), "")
        if reclaimed and "0B" not in reclaimed:
            print(f"   🧹 Lokale dangling images entfernt – {reclaimed.strip()}")
    except Exception:
        pass  # Prune-Fehler darf den Build-Ablauf nicht unterbrechen


# ── Image-Transfer ────────────────────────────────────────────────────────────
def transfer_image(env: dict) -> None:
    print(f"\n{bold('📤 Image komprimieren und auf Pi kopieren...')}")
    with open(ARCHIVE, "wb") as f:
        save_proc = subprocess.Popen(
            ["docker", "save", f"{IMAGE_NAME}:{IMAGE_TAG}"],
            stdout=subprocess.PIPE,
        )
        gzip_proc = subprocess.Popen(["gzip"], stdin=save_proc.stdout, stdout=f)
        save_proc.stdout.close()
        gzip_rc = gzip_proc.wait()
        save_rc = save_proc.wait()
    if save_rc != 0 or gzip_rc != 0:
        raise subprocess.CalledProcessError(save_rc or gzip_rc, "docker save | gzip")

    size = subprocess.check_output(["du", "-sh", str(ARCHIVE)]).decode().split()[0]
    print(f"   Archiv: {ARCHIVE} ({size})")
    run(["scp", "-i", env["PI_SSH_KEY"],
         str(ARCHIVE), f"{env['PI_USER']}@{env['PI_HOST']}:/tmp/vogel-pi.tar.gz"])
    ARCHIVE.unlink(missing_ok=True)
    print(green("✅ Image übertragen"))


# ── Ansible Deploy / Update ───────────────────────────────────────────────────
def ansible_deploy(env: dict, mode: str, ansible: str) -> None:
    vault_pass_file = Path(
        env.get("VAULT_PASS_FILE") or Path.home() / ".pi-daemon-vault-pass"
    ).expanduser()

    if vault_pass_file.exists():
        vault_opts = ["--vault-password-file", str(vault_pass_file)]
        print(f"🔐 Vault-Passwort: aus {vault_pass_file}")
    else:
        vault_opts = ["--ask-vault-pass"]
        print(yellow("🔐 Vault-Passwort wird interaktiv abgefragt."))
        print(f"   Tipp: echo 'Passwort' > {vault_pass_file} && chmod 600 {vault_pass_file}")

    print()
    os.chdir(ANSIBLE_DIR)
    if mode == "deploy":
        print(bold("🚀 Ansible – Voll-Deployment (Erstinstall)..."))
        run([ansible, "playbooks/deploy.yml", *vault_opts])
        print(bold("📊 Ansible – Health-Monitoring Setup..."))
        run([ansible, "-i", f"{env['PI_HOST']},", "-u", env["PI_USER"], 
             "--private-key", env["PI_SSH_KEY"],
             "playbooks/setup_pi_daemon_health_monitoring.yml", *vault_opts])
    elif mode == "hotpatch":
        print(bold("🩹 Ansible – Hotpatch (pi_daemon_secure.py)..."))
        run([ansible, "playbooks/hotpatch.yml", *vault_opts])
    else:
        print(bold("🔄 Ansible – Image-Update..."))
        run([ansible, "playbooks/update.yml", *vault_opts])
        print(bold("📊 Ansible – Health-Monitoring Setup..."))
        run([ansible, "-i", f"{env['PI_HOST']},", "-u", env["PI_USER"], 
             "--private-key", env["PI_SSH_KEY"],
             "playbooks/setup_pi_daemon_health_monitoring.yml", *vault_opts])


# ── TOTP-Generierung ──────────────────────────────────────────────────────────
def _generate_totp(secret: str) -> str:
    if oathtool := shutil.which("oathtool"):
        r = run_capture([oathtool, "--base32", "--totp", secret])
        if r.returncode == 0:
            return r.stdout.decode().strip()
    try:
        import pyotp
        return pyotp.TOTP(secret).now()
    except ImportError:
        return ""


# ── E2E-Test ──────────────────────────────────────────────────────────────────
def run_e2e(env: dict) -> None:
    pi_host  = env["PI_HOST"]
    pi_user  = env["PI_USER"]
    pi_key   = env["PI_SSH_KEY"]
    base_url = f"https://{pi_host}:8443"
    errors   = 0

    print(f"\n{bold(f'🧪 E2E-Test gegen {base_url}/ ...')}")
    print("────────────────────────────────────────────────")

    # [1] Container läuft?
    print("   [1] Container 'pi-daemon' läuft... ", end="", flush=True)
    r = run_capture([
        "ssh", "-i", pi_key, "-o", "BatchMode=yes",
        f"{pi_user}@{pi_host}",
        'docker ps --filter name=pi-daemon --filter status=running --format "{{.Names}}"',
    ])
    if r.returncode == 0 and "pi-daemon" in r.stdout:
        print(green("OK"))
    else:
        print(red("FEHLER – Container läuft nicht!"))
        errors += 1

    # [2] HTTPS erreichbar (401 = läuft, Auth fehlt)
    print("   [2] HTTPS Port 8443 erreichbar... ", end="", flush=True)
    code, _ = http_get(f"{base_url}/api/status")
    if code in (200, 401):
        print(green(f"OK (HTTP {code})"))
    else:
        print(red(f"FEHLER – HTTP {code} (erwartet 401)"))
        errors += 1

    # [3-5] Volltest mit Credentials
    e2e_pass    = env.get("E2E_PASSWORD", "")
    totp_secret = env.get("E2E_TOTP_SECRET", "")
    if not e2e_pass or not totp_secret:
        print(yellow("   ⚠ E2E_PASSWORD / E2E_TOTP_SECRET nicht in .env → Volltest übersprungen"))
        print(  "     Tipp: Beide Variablen in ansible/.env eintragen für vollständigen Test.")
    else:
        totp = _generate_totp(totp_secret)
        if not totp:
            print(yellow("   ⚠ TOTP konnte nicht generiert werden."))
            print(  "     Bitte 'oathtool' (oath-toolkit) oder pyotp installieren.")
        else:
            # [3] Login → JWT
            print("   [3] Login (JWT-Token)... ", end="", flush=True)
            _, body = http_post(f"{base_url}/api/login",
                                {"password": e2e_pass, "totp": totp})
            token = body.get("token", "")
            if token:
                print(green("OK"))
            else:
                print(red("FEHLER – Login fehlgeschlagen (Passwort/TOTP prüfen)"))
                errors += 1

            if token:
                auth = {"Authorization": f"Bearer {token}"}

                # [4] Status
                print("   [4] /api/status (kein Recording aktiv)... ", end="", flush=True)
                _, body = http_get(f"{base_url}/api/status", headers=auth)
                rec = str(body.get("recording_running", "?"))
                if rec.lower() == "false":
                    print(green("OK"))
                else:
                    print(yellow(f"WARNUNG – recording_running={rec}"))

                # [5] Testaufnahme – Detection ggf. stoppen (409 sonst)
                _, status_body = http_get(f"{base_url}/api/status", headers=auth)
                detection_was_running = status_body.get("detection_running", False)
                detection_mode_was_auto = status_body.get("detection_mode", False) is True
                if detection_was_running:
                    print("   [5a] Detection stoppen (läuft)... ", end="", flush=True)
                    _, db = http_post(f"{base_url}/api/detection/stop", {}, headers=auth)
                    print(green("OK") if db.get("success") else yellow("Warnung"))
                    time.sleep(2)

                print("   [5] 10s-Testaufnahme starten (HD)... ", end="", flush=True)
                _, body = http_post(f"{base_url}/api/record",
                                    {"duration": 10, "profile": "normal_hd"},
                                    headers=auth)
                if body.get("success"):
                    print(green("gestartet – warte auf Abschluss (max 60s)..."))
                    waited, final = 0, "True"
                    while waited < 60:
                        time.sleep(3)
                        waited += 3
                        _, body = http_get(f"{base_url}/api/status", headers=auth)
                        final = str(body.get("recording_running", "?"))
                        if final.lower() == "false":
                            break
                        print(".", end="", flush=True)
                    print()
                    if final.lower() == "false":
                        print(f"        {green(f'✅ Aufnahme abgeschlossen (nach {waited}s)')}")
                    else:
                        print(f"        {red(f'✗ Timeout – Aufnahme nach 60s nicht fertig (recording_running={final})')}")
                        errors += 1
                else:
                    print(red("FEHLER – Aufnahme konnte nicht gestartet werden"))
                    errors += 1

                if detection_was_running:
                    print("   [5b] Detection wieder starten... ", end="", flush=True)
                    endpoint = "/api/detection/mode/start" if detection_mode_was_auto else "/api/detection/start"
                    _, db = http_post(f"{base_url}{endpoint}", {}, headers=auth)
                    print(green("OK") if db.get("success") else yellow("Warnung"))

    print()
    if errors == 0:
        print(green(bold("✅ E2E-Test bestanden!")))
    else:
        print(red(bold(f"❌ E2E-Test fehlgeschlagen ({errors} Fehler)")))
        sys.exit(1)


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    os.environ.setdefault("PYTHONUTF8", "1")
    os.environ.setdefault("LANG", "de_DE.UTF-8")

    args = parse_args()
    mode = args.mode

    print(bold(f"🐦 Vogel-Kamera – Build & Deploy ({mode})"))
    print("────────────────────────────────────────────────")

    env = load_env()

    if mode == "setup-host":
        setup_host()
        return

    require_tool("docker")
    require_tool("ssh")
    require_tool("scp")

    ansible_bin: str | None = None
    if mode not in ("build", "e2e", "setup-host"):
        ansible_bin = find_tool("ansible-playbook")
        if not ansible_bin:
            print(red("❌ 'ansible-playbook' nicht gefunden."), file=sys.stderr)
            print("   python3 -m venv ~/ansible-venv && ~/ansible-venv/bin/pip install ansible",
                  file=sys.stderr)
            sys.exit(1)
        if not shutil.which("ansible-playbook"):
            print(yellow(f"ℹ ansible-playbook aus: {Path(ansible_bin).parent}"))

    check_ssh(env)

    if mode == "e2e":
        run_e2e(env)
        return

    if mode == "hotpatch":

        ansible_deploy(env, mode, ansible_bin)
        print(f"\n{green(bold('✅ Hotpatch eingespielt!'))}")
        print(f"   Web-GUI: https://{env['PI_HOST']}:8443/")
        return

    docker_build(args.no_cache)

    if mode == "build":
        print("Build-Only Modus – Deploy übersprungen.")
        return

    transfer_image(env)
    ansible_deploy(env, mode, ansible_bin)

    print(f"\n{green(bold('✅ Fertig!'))}")
    print(f"   Web-GUI: https://{env['PI_HOST']}:8443/")
    print("   Beim ersten Aufruf Browser-Zertifikat-Ausnahme bestätigen (self-signed).")

    if args.e2e:
        run_e2e(env)


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        print(red(f"❌ Befehl fehlgeschlagen (Exit {e.returncode}): {' '.join(str(x) for x in e.cmd)}"),
              file=sys.stderr)
        sys.exit(e.returncode)
    except KeyboardInterrupt:
        print("\n⚠ Abgebrochen.", file=sys.stderr)
        sys.exit(130)
