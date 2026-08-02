#!/usr/bin/env python3
"""
Garmin HRV-Status  →  Atem-App Import-JSON.

Zwei Modi:

  A) AUTO-PULL direkt aus Garmin Connect (Login, empfohlen für Automatisierung):
       pip install garminconnect
       export GARMIN_EMAIL="du@example.com"
       export GARMIN_PASSWORD="dein-passwort"
       python3 garmin_hrv_to_atem.py --fetch --days 28 -o ~/Library/Mobile\ Documents/com~apple~CloudDocs/atem-garmin.json
     → Zieht der letzten N Tage: **Nacht-HRV + Ruhepuls** (mode garmin),
       **Sleep Score + Schlafdauer** (mode sleep) und **Aktivitäten** inkl.
       Rennrad-Fahrten (mode activity). Token in ~/.garminconnect gecacht
       (Login/MFA nur beim ersten Mal). Import in der App wie gehabt.

  B) CSV → JSON (kein Login, aus Garmin-Connect-Export):
       python3 garmin_hrv_to_atem.py HFV-Status.csv -o atem-garmin.json

Danach: die JSON liegt (z. B. via iCloud Drive) auf dem Handy → in der App
unter Verlauf → „Import" laden. Import ist idempotent (merged, keine Duplikate),
du kannst also täglich neu ziehen und immer dieselbe Datei importieren.

Automatisch täglich (macOS, launchd) — Beispiel siehe Kommentar am Dateiende.
"""
import sys, os, json, re, argparse
from datetime import datetime, date, timedelta

# ---------------- gemeinsame Helfer ----------------
MON = {"jan":1,"feb":2,"mär":3,"mar":3,"mrz":3,"apr":4,"mai":5,"may":5,
       "jun":6,"jul":7,"aug":8,"sep":9,"okt":10,"oct":10,"nov":11,"dez":12,"dec":12}

def _num(s):
    m = re.search(r"-?\d+(?:[.,]\d+)?", str(s) if s is not None else "")
    return float(m.group(0).replace(",", ".")) if m else None

def _entry(ts_ms, rmssd, g7=None, lo=None, hi=None):
    return {"ts": int(ts_ms), "mode": "garmin", "src": "garmin",
            "rmssd": rmssd, "g7": g7, "baseLo": lo, "baseHi": hi, "dur": 0}

def _ts(y, mo, da):
    return int(datetime(y, mo, da, 7, 0, 0).timestamp() * 1000)

# ---------------- A) Auto-Pull via garminconnect ----------------
def _dig(d, *keys, default=None):
    for k in keys:
        if isinstance(d, dict) and k in d and d[k] is not None:
            return d[k]
    return default

def _ts_at(d, hh, mm):
    return int(datetime(d.year, d.month, d.day, hh, mm, 0).timestamp() * 1000)

def fetch_from_garmin(days, email, password):
    from garminconnect import Garmin
    tokenstore = os.path.expanduser("~/.garminconnect")
    try:
        client = Garmin()                       # nutzt gecachte Tokens
        client.login(tokenstore)
    except Exception:
        client = Garmin(email, password, prompt_mfa=lambda: input("Garmin MFA-Code: "))
        client.login(tokenstore)
    out = []
    for i in range(days):
        d = (date.today() - timedelta(days=i))
        ds = d.isoformat()
        # --- Nacht-HRV (07:00) ---
        try:
            data = client.get_hrv_data(ds)
            summ = _dig(data or {}, "hrvSummary", default={}) or {}
            val = _dig(summ, "lastNightAvg", "lastNight5MinHigh", "weeklyAvg")
            if val is not None:
                base = _dig(summ, "baseline", default={}) or {}
                e = _entry(_ts(d.year, d.month, d.day), _num(val),
                           g7=_num(_dig(summ, "weeklyAvg")),
                           lo=_num(_dig(base, "balancedLow", "lowUpper")),
                           hi=_num(_dig(base, "balancedUpper", "markerValue")))
                # Ruhepuls dranhaengen (defensiv aus mehreren Quellen)
                try:
                    st = client.get_stats(ds) or {}
                    e["rhr"] = _num(_dig(st, "restingHeartRate"))
                except Exception:
                    pass
                out.append(e)
        except Exception:
            pass
        # --- Schlaf (07:05) ---
        try:
            sd = client.get_sleep_data(ds) or {}
            dto = _dig(sd, "dailySleepDTO", default={}) or {}
            scores = _dig(dto, "sleepScores", default={}) or {}
            score = _dig(_dig(scores, "overall", default={}) or {}, "value") or _dig(dto, "sleepScoreValue")
            secs = _dig(dto, "sleepTimeSeconds")
            if score is not None or secs is not None:
                out.append({"ts": _ts_at(d, 7, 5), "mode": "sleep", "src": "garmin",
                            "score": _num(score),
                            "hours": round(_num(secs) / 3600, 1) if secs else None,
                            "dur": int(_num(secs)) if secs else 0})
        except Exception:
            pass
    # --- Aktivitaeten (echte Startzeit) ---
    try:
        acts = client.get_activities_by_date(
            (date.today() - timedelta(days=days)).isoformat(), date.today().isoformat()) or []
        for a in acts:
            start = _dig(a, "startTimeLocal", "startTimeGMT")
            if not start:
                continue
            try:
                ts = int(datetime.fromisoformat(str(start).replace(" ", "T")).timestamp() * 1000)
            except Exception:
                continue
            out.append({"ts": ts, "mode": "activity", "src": "garmin",
                        "name": _dig(_dig(a, "activityType", default={}) or {}, "typeKey") or a.get("activityName") or "Aktivität",
                        "dur": int(_num(_dig(a, "duration")) or 0),
                        "distance": _num(_dig(a, "distance"))})
    except Exception:
        pass
    out.sort(key=lambda e: e["ts"])
    return out

# ---------------- B) CSV → JSON ----------------
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
        mon = MON.get(dm.group(1).lower()[:3]); day = int(dm.group(2)); rmssd = _num(c[1])
        if not mon or not day or rmssd is None:
            continue
        rng = re.search(r"(\d+)\D+(\d+)", c[2] if len(c) > 2 else "")
        rows.append({"month": mon, "day": day, "rmssd": rmssd,
                     "g7": _num(c[3]) if len(c) > 3 else None,
                     "lo": int(rng.group(1)) if rng else None,
                     "hi": int(rng.group(2)) if rng else None})
    if not rows:
        return []
    now = datetime.now(); year = now.year
    last = rows[-1]
    if datetime(year, last["month"], last["day"]) > now:
        year -= 1
    for i in range(len(rows) - 1, -1, -1):
        if i < len(rows) - 1 and rows[i]["month"] > rows[i + 1]["month"]:
            year -= 1
        rows[i]["year"] = year
    return [_entry(_ts(r["year"], r["month"], r["day"]), r["rmssd"], r["g7"], r["lo"], r["hi"]) for r in rows]

# ---------------- main ----------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", nargs="?", help="Garmin HFV-Status CSV (CSV-Modus)")
    ap.add_argument("--fetch", action="store_true", help="Direkt aus Garmin Connect ziehen (Login)")
    ap.add_argument("--days", type=int, default=28)
    ap.add_argument("-o", "--out", default="atem-garmin.json")
    args = ap.parse_args()

    if args.fetch:
        email = os.environ.get("GARMIN_EMAIL"); password = os.environ.get("GARMIN_PASSWORD")
        token = os.path.expanduser("~/.garminconnect")
        if not (email and password) and not os.path.exists(token):
            print("Kein Login-Token gefunden. Erst einmalig 'python3 garmin_login.py' ausfuehren "
                  "(oder GARMIN_EMAIL/GARMIN_PASSWORD setzen).", file=sys.stderr); sys.exit(2)
        entries = fetch_from_garmin(args.days, email, password)
    elif args.csv:
        entries = parse_csv(args.csv)
    else:
        ap.print_help(); sys.exit(1)

    if not entries:
        print("Keine Garmin-Daten erkannt.", file=sys.stderr); sys.exit(1)
    doc = {"app": "atem", "version": 14,
           "exported": datetime.now().isoformat(timespec="seconds"), "history": entries}
    outdir = os.path.dirname(os.path.abspath(args.out))
    if outdir:
        os.makedirs(outdir, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
    print(f"{len(entries)} Garmin-Nächte → {args.out}")

if __name__ == "__main__":
    main()

# --- Täglich automatisch (macOS launchd) ---
# ~/Library/LaunchAgents/com.atem.garmin.plist mit ProgramArguments:
#   /usr/bin/python3  <pfad>/garmin_hrv_to_atem.py  --fetch  --days 28
#   -o  <iCloud-Pfad>/atem-garmin.json
# und <key>StartCalendarInterval</key> (z. B. Hour 9). Dann liegt die
# aktuelle JSON täglich in iCloud → auf dem Handy 1× antippen zum Import.
