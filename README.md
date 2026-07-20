# Atem 🫁

Persönliche Atem- & HRV-Biofeedback-App für Stefan Kick. Single-File-Web-App (PWA),
läuft offline auf Android/Chrome, misst HRV live über einen **Polar-Brustgurt (H10)**
via Web Bluetooth. Ersatz für die myQiu/BioSign-App (ohne Lizenz/Ablauf).

**Live:** https://stefankick.github.io/atem/
**Repo:** https://github.com/StefanKick/atem (GitHub Pages, Branch `main`, Root `/`)

---

## Was die App kann

| Tab | Funktion |
|-----|----------|
| **Resonanz** | Geführte Resonanzatmung (Default 4-6). Rate/Halte-Phasen frei einstellbar, flexible Dauer (1–45 Min oder ohne Zeitlimit). Atem-Orb + Ton + Vibration. |
| **Seufzer** | Physiological Sigh (Doppel-Einatmung + langer Ausatem), Zyklen-Zähler. |
| **HRV Live** | Polar verbinden → **Training** (paced Biofeedback: Kohärenz, adaptiver Zielwert, Übungserfolg) oder **Ruhemessung** (still sitzen → Baseline-HRV vs. Altersnorm). Nach der Sitzung: volle Auswertung. |
| **Verlauf** | Jede Sitzung geloggt (localStorage). Summary, Interpretation, Trend pro Kennzahl, Tap-auf-Sitzung → Auswertung, Export/Import (JSON-Backup). |

**Auswertungs-Screen:** Ring-Gauge (Übungserfolg + Zonen), Zeit-im-Zielbereich, Puls+Kohärenz-Replay-Chart, volle HRV-Kennzahlentabelle mit Interpretation.

**Klang:** Atem-Ton *Weich* (Pad) / *Glocke* / *Klick*. Hintergrund *Aus* / *Meer* / *Drone*,
optional an den Atem gekoppelt (Brandung schwillt mit) oder als gleichmäßiger Klangteppich.
Alles prozedural synthetisiert (Web Audio) → keine Audiodateien, bleibt offline.
Alternativ: Spotify o. Ä. im Hintergrund + „Klick" als Wechsel-Marker.

---

## Architektur

- **`index.html`** — die komplette App (HTML + CSS + JS inline, keine Build-Tools, keine Dependencies).
- **`sw.js`** — Service Worker. **network-first für HTML** (online immer frisch), cache-first für Assets. `CACHE='atem-vN'` bei **jedem Release hochzählen**, sonst bekommen Clients keine Updates.
- **`manifest.json`** + **`icon.svg`** — PWA-Installierbarkeit (Add to Home Screen).

### JS-Bausteine (in `index.html`)
- **Audio** (Web Audio): `breathPad` / `breathBell` / `clickTone` (Atem-Ton), `startAmbient`/`stopAmbient`/`ambientPhase` + `oceanBuf` (Hintergrund), `glide()` dispatcht auf den Stil.
- **Atem-Engine:** `startBreathing(isHrv)` (Resonanz + HRV-Pacer, geteilte State-Machine), `startScan()` (Ruhemessung), `startSigh()`. Phasen-Objekte tragen `{name,dur,scale,glide,vibe}`.
- **HRV-Engine:** `timeDomain(rr)` (RMSSD/SDNN/pNN50/SD1/SD2/CV), `freqDomain(rr)` (eigene `fft` → Welch-PSD → Bänder VLF/LF/HF, LF/HF, nu), `computeAllMetrics`.
- **BLE:** `connectPolar` (Standard Heart Rate Service `0x180D`, Characteristic `0x2A37`), `onHr` parst Flags + RR-Intervalle (1/1024 s), Artefaktfilter, Recording (`startRec`/`stopRec`).
- **Auswertung:** `openResult(rec)`, `drawRing`, `drawReplay`, `metricRows`, `interpretSession`.
- **Verlauf/Storage:** `loadHist`/`saveHist`/`logSession` (localStorage `atem_history`), `renderHistory`, `renderTrend`, `drawSpark`, Export/Import.
- **Settings:** localStorage `atem`. `state.settings` = Single Source of Truth; `syncControls()` spiegelt sie in die UI.

### Referenzwerte / Interpretation
HRV-Normwerte (Ruhe, 5 Min): Nunan 2010 Meta-Analyse; Zuordnung/Definitionen: Shaffer & Ginsberg 2017; Resonanz/Kohärenz: Lehrer/HeartMath. Konstante `NORM` in `index.html`. **Wichtig:** Trainingswerte (paced ~6/min) inflationieren SDNN/LF/Total Power (0,1-Hz-Resonanz) → nur mit eigenen Trainingssitzungen vergleichen; Norm-Vergleich nur im Ruhemess-Modus.

---

## Entwickeln & Deployen

Keine Toolchain nötig — reines HTML/JS.

**Lokal testen:**
```
cd atem-app
python3 -m http.server 8000     # oder: npx serve .
# → http://localhost:8000  (Web Bluetooth braucht localhost oder https)
```

**Deployen:**
```
# 1. sw.js: CACHE-Version hochzählen (atem-vN → atem-vN+1)   ← nicht vergessen!
# 2.
git add -A && git commit -m "..." && git push
# GitHub Pages baut automatisch (~1–2 Min). Live: https://stefankick.github.io/atem/
```

**Update landet beim Nutzer:** Dank network-first HTML reicht einmal neu laden (online). Der neue Service Worker (neue CACHE-Version) übernimmt automatisch.

**Testen im Browser (Claude Code):** über die Preview-Tools; HRV-Engine lässt sich mit synthetischen RR-Arrays unit-testen (`computeAllMetrics` mit 0,1-Hz-Sinus → LF muss dominieren). Web Bluetooth nur auf echtem Android/Chrome mit Polar real testbar.

---

## Ideen-Backlog (offen)
- Echter FFT-Kohärenz-Score im 0,1-Hz-Band (statt RSA-Amplituden-Näherung).
- Kalibrierung der Kohärenz-Skala / Zielwert-Logik an Stefans reale Polar-Werte.
- Klick-Timbre-Varianten (Holz-Tock / Glöckchen), getrennte Klänge für Ein-/Ausatmen.
- Datei-Upload für eigene Meditationsmusik/Field-Recording als Alternative zur synthetischen Ambience.
- Optional: 1-Klick-Garmin-Auto-Sync über privaten Gist (App zieht JSON per URL) — nur mit ausdrücklichem OK (Health-Daten).
- Mehrfach-Löschen / Auto-Ausblenden von Messfehlern (Qualität < X %).

## Versionen
- **v1** Resonanz · Seufzer · HRV-Live (Polar)
- **v2** Verlauf/Historie, Interpretation, flexible Timer, network-first SW
- **v3** Volle HRV-Metrik-Engine (Zeit+Frequenz/FFT), Auswertungs-Screen, Training/Ruhemessung, Trends
- **v4** Angenehmer Klang statt Sirene (Pad ohne Pitch-Sweep) + Klangfarbe-Wahl
- **v5** Atem-gekoppelter Hintergrund (Meer/Drone), prozedural
- **v6** Atem-Ton „Klick" + Hintergrund entkoppelbar (steady Klangteppich)
- **v7** Alle HRV-Werte interpretiert + antippbare Erklärungen · stärkere Ein-/Ausatem-Visualisierung · Seufzer nach Zeit/Anzahl · optionales Polar-Mitmessen bei Resonanz
- **v8** Garmin Nacht-HRV Import (In-App-CSV, eigener Modus/Trend, persönliche Baseline) + Python-Tool
- **v9** Resonanz-Frequenz-Assistent · Puls-Kreis (Ruhemessung) · Tagesform-Ampel · Erinnerungen (In-App + ICS) · Garmin Auto-Pull (Login) im Python-Tool
- **v10** Einzelne Verlaufs-Einträge löschbar (Zeile + Auswertung)
