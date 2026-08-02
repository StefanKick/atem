#!/usr/bin/env python3
"""Einmaliger Garmin-Login -> Token-Cache (~/.garminconnect).
Passwort nur am sicheren Prompt, wird NICHT gespeichert.
Danach laeuft garmin_hrv_to_atem.py --fetch ohne Passwort (nutzt den Token).
Robust fuer garminconnect 0.2.x / garth 0.4.x (MFA ueber garth)."""
import os, sys, getpass

def main():
    store = os.path.expanduser("~/.garminconnect")
    os.makedirs(store, exist_ok=True)
    email = input("Garmin E-Mail: ").strip()
    pw = getpass.getpass("Garmin Passwort (Eingabe unsichtbar): ")
    mfa = lambda: input("MFA-Code (falls abgefragt): ").strip()

    # 1) garth direkt (bester MFA-Support)
    try:
        import garth
        try:
            garth.login(email, pw, prompt_mfa=mfa)
        except TypeError:
            garth.login(email, pw)  # aeltere garth ohne prompt_mfa (MFA via Default-Prompt)
        garth.save(store)
        print("OK Login erfolgreich. Token in", store)
        print("   Kuenftige Laeufe brauchen KEIN Passwort mehr.")
        return
    except Exception as e:
        print("garth-Login-Versuch fehlgeschlagen:", repr(e), file=sys.stderr)

    # 2) Fallback ueber garminconnect
    try:
        from garminconnect import Garmin
        c = Garmin(email, pw)
        c.login(store)
        print("OK Login erfolgreich (garminconnect). Token in", store)
    except Exception as e:
        print("Login endgueltig fehlgeschlagen:", repr(e), file=sys.stderr)
        print("Tipp: bei MFA-Konten ggf. garth aktualisieren:  pip3 install --user -U garth garminconnect", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
