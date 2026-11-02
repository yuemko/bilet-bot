import os
import random
import requests
from datetime import datetime, timedelta
from flask import Flask, request, jsonify

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "").strip()
SERPAPI_KEY = os.environ.get("SERPAPI_KEY", "").strip()

AIRPORT_CODES = {
    "prag": "PRG", "prague": "PRG",
    "viyana": "VIE", "vienna": "VIE",
    "roma": "FCO", "rome": "FCO",
    "berlin": "BER", "münih": "MUC", "munich": "MUC",
    "budapeşte": "BUD", "budapest": "BUD",
    "varşova": "WAW", "warsaw": "WAW",
    "krakow": "KRK", "amsterdam": "AMS"
}

REGIOJET_IDS = {
    "prag": "10202002", "prague": "10202002",
    "viyana": "10202003", "vienna": "10202003",
    "cb": "10202000", "budějovice": "10202000",
    "brno": "10202001", "berlin": "10202004",
    "münih": "10202005", "munich": "10202005"
}

NASTENKA_SOZLERI = [
    "\"Senin bir tek gülücüğün, bana bir ömür boyu hayal kurmak için yeter Nastenka... Seni sevmek bana yetiyor, sevilmesem de olur.\" — Fyodor Dostoyevski (Beyaz Geceler)",
    "\"Tanrım! Bir dakikalık mutluluk! Bütün bir insan ömrü için az bir şey mi bu?\" — Fyodor Dostoyevski (Beyaz Geceler)"
]

GENEL_SOZLER = NASTENKA_SOZLERI + [
    "\"O gemi bir gün gelecek Mecnun... Biz sadece yanlış limanda bekliyoruz.\" — İsmail Abi (Leyla ile Mecnun)"
]

def send_telegram(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Telegram hatası: {e}")

def dinamik_bilet_tara(kalkis_sehri, varis_sehri, tarih_girdisi=None):
    if not tarih_girdisi:
        tarih = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
    else:
        try:
            parcalar = tarih_girdisi.split("-")
            tarih = f"{parcalar[0]}-{parcalar[1].zfill(2)}-{parcalar[2].zfill(2)}"
        except Exception:
            tarih = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")

    sonuclar = []

    dep_code = AIRPORT_CODES.get(kalkis_sehri.lower(), kalkis_sehri.upper())
    arr_code = AIRPORT_CODES.get(varis_sehri.lower(), varis_sehri.upper())

    # 1. UÇAK TARAMASI (SerpApi)
    if SERPAPI_KEY:
        try:
            params = {
                "engine": "google_flights",
                "departure_id": dep_code,
                "arrival_id": arr_code,
                "outbound_date": tarih,
                "currency": "EUR",
                "hl": "tr",
                "api_key": SERPAPI_KEY
            }
            res_api = requests.get("https://serpapi.com/search.json", params=params, timeout=15)
            if res_api.status_code == 200:
                data = res_api.json()
                flights = data.get("best_flights", []) + data.get("other_flights", [])
                for f in flights[:3]:
                    price = f.get("price", "Bilinmiyor")
                    leg = f.get("flights", [{}])[0]
                    airline = leg.get("airline", "Hava Yolu")
                    dep_time = leg.get("departure_airport", {}).get("time", "")

                    msg = (
                        f"✈️ *UÇAK BİLETİ*\n"
                        f"🛫 *Kalkış:* {dep_code} -> 🛬 *Varış:* {arr_code}\n"
                        f"✈️ *Firma:* {airline}\n"
                        f"📅 *Tarih/Saat:* {tarih} {dep_time}\n"
                        f"💰 *Fiyat:* {price} EUR\n"
                        f"🎓 *Öğrenci Notu:* Havayolu sitesinden ISIC/Öğrenci indirimi sorgulanabilir.\n"
                        f"🔗 [Google Flights İncele](https://www.google.com/travel/flights)\n"
                    )
                    sonuclar.append(msg)
        except Exception as e:
            print(f"SerpApi hatası: {e}")

    # 2. OTOBÜS & TREN TARAMASI (RegioJet)
    from_regio = REGIOJET_IDS.get(kalkis_sehri.lower())
    to_regio = REGIOJET_IDS.get(varis_sehri.lower())

    if from_regio and to_regio:
        try:
            url = "https://brn-yee-api.regiojet.com/rest/busTickets/search"
            params = {"fromLocationId": from_regio, "toLocationId": to_regio, "departureDate":
