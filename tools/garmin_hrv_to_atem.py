#!/usr/bin/env python3
"""
Garmin HRV-Status → Atem-App Import (Bonus/optional).

Die Atem-App kann die Garmin-CSV inzwischen DIREKT importieren
(Verlauf → „🌙 Garmin Nacht-HRV importieren"). Dieses Skript ist nur
für den Desktop-/Automatisierungs-Weg gedacht.

Zwei Modi:

1) CSV → JSON (kein Login nötig):
   Du exportierst in Garmin Connect die HFV-Status-CSV
   (Spalten: Datum, HFV über Nacht, Ausgangszustand, 7-Tage-Durchschnitt)
   und wandelst sie in eine Atem-Backup-JSON um:

       python3 garmin_hrv_to_atem.py HFV-Status.csv -o atem-garmin.json

   Danach die JSON aufs Handy (Cloud) und in der App unter
   Verlauf → „Import" laden.

2) Direkt aus Garmin ziehen (automatisiert, benötigt Login):
   pip install garminconnect
   und die auskommentierte Funktion pull_from_garmin() nutzen.
   (RR/HRV: Garmin liefert die nächtliche HRV-Status-Zahl, keine
   Beat-to-Beat-RR — fürs Live-Biofeedback bleibt der Polar zuständig.)
"""
import sys, json, csv, re, argparse
from datetime import datetime

MON = {"jan":1,"feb":2,"mär":3,"mar":3,"mrz":3,"apr":4,"mai":5,"may":5,
       "jun":6,"jul":7,"aug":8,"sep":9,"okt":10,"oct":10,"nov":11,"dez":12,"dec":12}

def _num(s):
    m = re.search(r"-?\d+(?:[.,]\d+)?", s or "")
    return float(m.group(0).replace(",", ".")) if m else None

def parse_csv(path):
    with open(path, encoding="utf-8-sig") as f:
        lines = [l.strip() for l in f if l.strip()]
    if not lines:
        return []
    start = 1 if re.search(r"datum|hfv|hrv|nacht|overnight", lines[0], re.I) else 0
    rows = []
    for line in lines[start:]:
        c = [x.strip() for x in re.split(r"[;,]", line)]
        if len(c) < 2:
            continue
        dm = re.match(r"([A-Za-zäöüÄÖÜ]{3,})\.?\s+(\d{1,2})", c[0])
        if not dm:
            continue
        mon = MON.get(dm.group(1).lower()[:3])
        day = int(dm.group(2))
        rmssd = _num(c[1])
        if not mon or not day or rmssd is None:
            continue
        rng = re.search(r"(\d+)\D+(\d+)", c[2] if len(c) > 2 else "")
        rows.append({"month": mon, "day": day, "rmssd": rmssd,
                     "g7": _num(c[3]) if len(c) > 3 else None,
                     "lo": int(rng.group(1)) if rng else None,
                     "hi": int(rng.group(2)) if rng else None})
    if not rows:
        return []
    # Jahr rückwärts zuweisen (Daten ohne Jahr, aufsteigend chronologisch)
    now = datetime.now()
    year = now.year
    last = rows[-1]
    if datetime(year, last["month"], last["day"]) > now:
        year -= 1
    for i in range(len(rows) - 1, -1, -1):
        if i < len(rows) - 1 and rows[i]["month"] > rows[i + 1]["month"]:
            year -= 1
        rows[i]["year"] = year
    out = []
    for r in rows:
        ts = int(datetime(r["year"], r["month"], r["day"], 7, 0, 0).timestamp() * 1000)
        out.append({"ts": ts, "mode": "garmin", "src": "garmin",
                    "rmssd": r["rmssd"], "g7": r["g7"],
                    "baseLo": r["lo"], "baseHi": r["hi"], "dur": 0})
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", help="Garmin HFV-Status CSV")
    ap.add_argument("-o", "--out", default="atem-garmin.json")
    args = ap.parse_args()
    entries = parse_csv(args.csv)
    if not entries:
        print("Keine Garmin-Daten erkannt.", file=sys.stderr)
        sys.exit(1)
    doc = {"app": "atem", "version": 8,
           "exported": datetime.now().isoformat(timespec="seconds"),
           "history": entries}
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
    print(f"{len(entries)} Garmin-Nächte → {args.out}")

# --- Optional: direkt aus Garmin Connect ziehen (Login nötig) ---
# def pull_from_garmin(email, password, days=30):
#     from garminconnect import Garmin
#     from datetime import date, timedelta
#     g = Garmin(email, password); g.login()
#     out = []
#     for i in range(days):
#         d = (date.today() - timedelta(days=i)).isoformat()
#         hrv = g.get_hrv_data(d)                     # {'hrvSummary': {'lastNightAvg':..,'baseline':{...}}}
#         summ = (hrv or {}).get("hrvSummary") or {}
#         val = summ.get("lastNightAvg")
#         if val is None: continue
#         base = summ.get("baseline") or {}
#         ts = int(datetime.fromisoformat(d + "T07:00:00").timestamp()*1000)
#         out.append({"ts": ts, "mode":"garmin","src":"garmin","rmssd":val,
#                     "g7": summ.get("weeklyAvg"),
#                     "baseLo": base.get("lowUpper"), "baseHi": base.get("balancedUpper"), "dur":0})
#     return out

if __name__ == "__main__":
    main()
