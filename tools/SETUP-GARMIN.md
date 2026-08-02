# Garmin Auto-Pull — Einrichtung (einmalig)

Zieht automatisch aus Garmin Connect: **Nacht-HRV, Ruhepuls, Sleep Score, Aktivitäten**
→ schreibt eine JSON-Datei, die du in der Atem-App unter **Verlauf → Import** lädst.
Läuft auf deinem Mac. Direkt-Bluetooth zur Uhr geht nicht (Sleep/Aktivitäten liegen nur in der Garmin-Cloud).

## 1. Bibliothek installieren (einmal, im Terminal)
```bash
pip3 install garminconnect
```

## 2. Zugangsdaten setzen (deine, bleiben lokal)
```bash
export GARMIN_EMAIL="deine@mail.de"
export GARMIN_PASSWORD="dein-garmin-passwort"
```
(Dauerhaft: die zwei Zeilen ans Ende von `~/.zshrc` hängen.)

## 3. Erster Lauf (MFA-Code wird einmal abgefragt)
```bash
cd ~/Documents/Claude/atem-app/tools
python3 garmin_hrv_to_atem.py --fetch --days 28 \
  -o ~/Library/Mobile\ Documents/com~apple~CloudDocs/atem-garmin.json
```
Beim ersten Mal fragt Garmin einen **MFA-Code** ab (aus deiner Authenticator-App/SMS).
Danach wird der Login-Token in `~/.garminconnect` gecacht → künftige Läufe ohne Abfrage.

Die JSON landet in **iCloud Drive** → auf dem Handy in der App **Verlauf → Import** öffnen. Import ist idempotent (mergt, keine Duplikate), du kannst also täglich neu ziehen und immer dieselbe Datei importieren.

## 4. Täglich automatisch (optional, launchd)
Datei `~/Library/LaunchAgents/com.atem.garmin.plist` anlegen:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.atem.garmin</string>
  <key>ProgramArguments</key><array>
    <string>/usr/bin/python3</string>
    <string>/Users/stefan.kick/Documents/Claude/atem-app/tools/garmin_hrv_to_atem.py</string>
    <string>--fetch</string><string>--days</string><string>7</string>
    <string>-o</string>
    <string>/Users/stefan.kick/Library/Mobile Documents/com~apple~CloudDocs/atem-garmin.json</string>
  </array>
  <key>EnvironmentVariables</key><dict>
    <key>GARMIN_EMAIL</key><string>deine@mail.de</string>
    <key>GARMIN_PASSWORD</key><string>dein-passwort</string>
  </dict>
  <key>StartCalendarInterval</key><dict><key>Hour</key><integer>9</integer><key>Minute</key><integer>0</integer></dict>
</dict></plist>
```
Aktivieren:
```bash
launchctl load ~/Library/LaunchAgents/com.atem.garmin.plist
```
→ Läuft täglich 9:00, aktualisiert die iCloud-JSON. Du tippst in der App nur noch „Import".

## Troubleshooting
- **Login/MFA schlägt fehl:** `rm -rf ~/.garminconnect` und Schritt 3 erneut.
- **Feldnamen ändern sich bei Garmin:** Das Skript extrahiert defensiv (mehrere Fallbacks); falls Sleep/Aktivität leer bleiben, sag mir Bescheid, dann passe ich die Feldpfade an.
- **Sicherheit:** Passwort steht dann in `~/.zshrc` bzw. der plist (nur lokal, dein Mac). Alternativ die zwei `export`-Zeilen manuell vor jedem Lauf eingeben.
