# Garmin Auto-Pull — Einrichtung

Zieht aus Garmin Connect: **Nacht-HRV, Ruhepuls, Sleep Score, Aktivitäten**
→ schreibt eine JSON, die du in der Atem-App unter **Verlauf → Import** lädst.
Läuft auf deinem Mac. (Direkt-Bluetooth zur Uhr geht nicht — Sleep/Aktivitäten liegen nur in der Garmin-Cloud.)

## ✅ Schon erledigt
`garminconnect` ist installiert.

## Schritt 1 — Einmaliger Login (Passwort nur am Prompt, wird NICHT gespeichert)
```bash
cd ~/Documents/Claude/atem-app/tools
python3 garmin_login.py
```
E-Mail, Passwort (unsichtbar) und ggf. den **MFA-Code** eingeben. Der Login-Token wird in
`~/.garminconnect` gecacht → **ab jetzt kein Passwort mehr nötig.**

## Schritt 2 — Daten ziehen
```bash
cd ~/Documents/Claude/atem-app/tools
python3 garmin_hrv_to_atem.py --fetch --days 28 -o ~/Documents/atem-garmin.json
```
Erzeugt `~/Documents/atem-garmin.json`.

## Schritt 3 — In die App importieren (auf dem Handy)
Die JSON aufs Handy bringen (AirDrop / iCloud Drive / an dich selbst mailen) und in der App
**Verlauf → „Import"** öffnen. Import ist idempotent (mergt, keine Duplikate) — du kannst
täglich neu ziehen und immer dieselbe Datei importieren.
> Tipp: Wenn du iCloud Drive nutzt, gib in Schritt 2 einen iCloud-Pfad als `-o` an, dann liegt die
> Datei automatisch auf dem Handy. (Bei dir war der Standard-iCloud-Ordner nicht vorhanden — ggf.
> iCloud Drive in den Systemeinstellungen aktivieren.)

## Schritt 4 — Täglich automatisch (optional, ohne Passwort in der Datei)
`~/Library/LaunchAgents/com.atem.garmin.plist`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.atem.garmin</string>
  <key>ProgramArguments</key><array>
    <string>/usr/bin/python3</string>
    <string>/Users/stefan.kick/Documents/Claude/atem-app/tools/garmin_hrv_to_atem.py</string>
    <string>--fetch</string><string>--days</string><string>7</string>
    <string>-o</string><string>/Users/stefan.kick/Documents/atem-garmin.json</string>
  </array>
  <key>StartCalendarInterval</key><dict><key>Hour</key><integer>9</integer><key>Minute</key><integer>0</integer></dict>
</dict></plist>
```
```bash
launchctl load ~/Library/LaunchAgents/com.atem.garmin.plist
```
Läuft täglich 9:00, nutzt den gecachten Token (kein Passwort in der Datei).

## Troubleshooting
- **Login/Token abgelaufen:** `rm -rf ~/.garminconnect` und Schritt 1 erneut.
- **Sleep/Aktivität leer:** Garmin ändert manchmal Feldnamen; sag Bescheid, dann passe ich die Feldpfade im Skript an.
