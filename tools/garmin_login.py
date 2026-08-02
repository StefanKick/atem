#!/usr/bin/env python3
"""Einmaliger Garmin-Login → Token-Cache (~/.garminconnect).
Passwort wird nur am sicheren Prompt eingegeben und NICHT gespeichert.
Danach läuft garmin_hrv_to_atem.py --fetch ohne Passwort (nutzt den Token)."""
import os, sys, getpass

def main():
    try:
        from garminconnect import Garmin
    except ImportError:
        print("Bitte zuerst: pip3 install --user garminconnect", file=sys.stderr); sys.exit(1)
    email = input("Garmin E-Mail: ").strip()
    pw = getpass.getpass("Garmin Passwort (Eingabe unsichtbar): ")
    store = os.path.expanduser("~/.garminconnect")
    client = Garmin(email, pw, prompt_mfa=lambda: input("MFA-Code (falls abgefragt): ").strip())
    client.login(store)
    print("✅ Login ok. Token gecacht in", store)
    print("   Künftige Läufe brauchen KEIN Passwort mehr.")

if __name__ == "__main__":
    main()
