#!/bin/bash
# setup-sudo-nopasswd.sh
# Richtet passwordlose Sudo-Befehle für vogel-kamera-buildx ein
# Verwendung: bash setup-sudo-nopasswd.sh

set -e

echo "🔧 Richte passwordlose Sudo-Befehle für Docker ein..."

# Überprüfe ob bereits vorhanden
if [ -f /etc/sudoers.d/vogel-kamera-buildx ]; then
    echo "ℹ /etc/sudoers.d/vogel-kamera-buildx existiert bereits"
else
    # Erstelle sudoers-Datei (sicher über visudo-ähnlich)
    sudo tee /etc/sudoers.d/vogel-kamera-buildx > /dev/null <<'EOF'
# Vogel-Kamera Linux - Docker Buildx Build-Host Setup
# Erlaubt passwordloses Neustarten von Docker (nötig für binfmt-Handler)

Defaults env_keep += "DOCKER_HOST"
Defaults secure_path = "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

# Build-Host: Docker systemctl Befehle (ohne Passwort)
%docker ALL=(ALL) NOPASSWD: /bin/systemctl restart docker
%docker ALL=(ALL) NOPASSWD: /bin/systemctl start docker
%docker ALL=(ALL) NOPASSWD: /bin/systemctl status docker
%docker ALL=(ALL) NOPASSWD: /bin/systemctl enable docker

# Gentoo spezifisch: emerge im Build-Kontext (falls nötig)
# %docker ALL=(ALL) NOPASSWD: /usr/bin/emerge *
EOF

    # Rechte setzen (sudoers-Dateien MÜSSEN 0440 sein)
    sudo chmod 0440 /etc/sudoers.d/vogel-kamera-buildx
    
    echo "✅ /etc/sudoers.d/vogel-kamera-buildx erstellt"
fi

# Verifizierung
echo ""
echo "🔍 Verifizierung:"
sudo -l | grep -i docker || echo "⚠ Keine Einträge gefunden"

# Funktionstest
echo ""
echo "🧪 Test: sudo ohne Passwort für Docker"
sudo systemctl is-active docker > /dev/null && echo "✅ Docker läuft" || echo "❌ Docker nicht aktiv"

echo ""
echo "✅ Einrichtung abgeschlossen!"
echo ""
echo "Von nun an läuft 'bash build_and_deploy.sh' ohne Passwort-Abfrage"
echo "Grund: NOPASSWD-Regeln erlauben docker systemctl Befehle"
