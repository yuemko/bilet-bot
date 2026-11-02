import os
import random
import requests
from datetime import datetime, timedelta
from flask import Flask, request, jsonify

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "").strip()

# SERPAPI KEY'İ DOĞRUDAN KODA YAZILDI (RENDER OKUYAMASA BİLE ÇALIŞIR)
SERPAPI_KEY = "38e17865fa12c48db2e73e112fe648937dad1e3dbf4649cacddf7177cde7ef5"

AIRPORT_CODES = {
    "prag": "PRG", "prague": "PRG",
    "brno": "BRQ", "ostrava": "OSR", "karlovy vary": "KLV", "karlovyvary": "KLV",
    "viyana": "VIE", "vienna": "VIE",
    "budapeşte": "BUD", "budapest": "BUD",
    "bratislava": "BTS",
    "berlin": "BER", "münih": "MUC", "munich": "MUC", "dresden": "DRS",
    "frankfurt": "FRA", "nürnberg": "NUE", "nuremberg": "NUE",
    "varşova": "WAW", "warsaw": "WAW", "krakow": "KRK", "wroclaw": "WRO",
    "roma": "FCO", "rome": "FCO", "milano": "MXP", "milan": "MXP",
    "venedik": "VCE", "venice": "VCE", "bologna": "BLQ", "floransa": "FLR",
    "paris": "CDG", "amsterdam": "AMS", "brüksel": "BRU",
    "barselona": "BCN", "barcelona": "BCN", "madrid": "MAD", "londra": "LON"
}

REGIOJET_IDS = {
    "prag": "10202002", "prague": "10202002",
    "cb": "10202000", "budějovice": "10202000", "ceske budejovice": "10202000",
    "brno": "10202001", "pilsen": "10202006", "plzen": "10202006",
    "ostrava": "10202007", "olomouc": "10202008", "liberec": "10202009",
    "hradec kralove": "10202010", "hradec": "10202010", "pardubice": "10202011",
    "karlovy vary": "10202012", "karlovyvary": "10202012", "zlin": "10202013",
    "jihlava": "10202014", "usti": "10202015", "usti nad labem": "10202015",
    "viyana": "10202003", "vienna": "10202003",
    "berlin": "10202004", "münih": "10202005", "munich": "10202005",
    "dresden": "10202016", "bratislava": "10202017",
    "budapeşte": "10202018", "budapest": "10202018",
    "krakow": "10202019", "varşova": "10202020", "warsaw": "10202020"
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

def tarih_formatla(tarih_str):
    if not tarih_str:
        return (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
    try:
        parcalar = tarih_str.split("-")
        if len(parcalar) == 3:
            return f"{parcalar[0]}-{parcalar[1].zfill(2)}-{parcalar[2].zfill(2)}"
    except Exception:
        pass
    return (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")

def dinamik_bilet_tara(kalkis_sehri, varis_sehri, tarih_girdisi=None):
    tarih = tarih_formatla(tarih_girdisi)
    sonuclar = []

    dep_code = AIRPORT_CODES.get(kalkis_sehri.lower(), kalkis_sehri.upper())
    arr_code = AIRPORT_CODES.get(varis_sehri.lower(), varis_sehri.upper())

    # 1. SERPAPI İLE CANLI UÇAK BİLETİ TARAMASI
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
                    f"🎓 *Öğrenci Notu:* ISIC/Öğrenci indirimi geçerli olabilir.\n"
                    f"🔗 [Google Flights Satın Al](https://www.google.com/travel/flights)\n"
                )
                sonuclar.append(msg)
    except Exception as e:
        print(f"SerpApi hatası: {e}")

    # 2. REGIOJET OTOBÜS/TREN TARAMASI
    from_regio = REGIOJET_IDS.get(kalkis_sehri.lower())
    to_regio = REGIOJET_IDS.get(varis_sehri.lower())

    if from_regio and to_regio:
        try:
            url = "https://brn-yee-api.regiojet.com/rest/busTickets/search"
            params = {"fromLocationId": from_regio, "toLocationId": to_regio, "departureDate": tarih}
            headers = {"Accept": "application/json", "User-Agent": "Mozilla/5.0"}
            res_api = requests.get(url, params=params, headers=headers, timeout=10)
            if res_api.status_code == 200:
                res = res_api.json()
                for r in res.get("routes", [])[:3]:
                    price = r.get("priceFrom", "Bilinmiyor")
                    vehicle_types = r.get("vehicleTypes", ["BUS"])
                    vehicle = "🚆 Tren" if "TRAIN" in vehicle_types else "🚌 Otobüs"
                    dep_time_raw = r.get("departureTime", "")
                    dep_time = dep_time_raw.split("T")[-1][:5] if "T" in dep_time_raw else dep_time_raw

                    msg = (
                        f"{vehicle} *BİLETİ*\n"
                        f"🛫 {kalkis_sehri.capitalize()} -> 🛬 {varis_sehri.capitalize()}\n"
                        f"📅 *Saat:* {dep_time}\n"
                        f"💰 *Fiyat:* {price} EUR / CZK\n"
                        f"🎓 *ISIC Öğrenci:* Binerken kart ibrazı gerekebilir.\n"
                        f"🔗 [RegioJet Bilet Al](https://regiojet.com)\n"
                    )
                    sonuclar.append(msg)
        except Exception as e:
            print(f"RegioJet hatası: {e}")

    # EĞER HİÇBİR APİ SONUÇ VERMEZSE YEDEK LİNKLER
    if not sonuclar:
        google_flights_link = f"https://www.google.com/travel/flights?q=Flights%20to%20{arr_code}%20from%20{dep_code}%20on%20{tarih}"
        regio_link = f"https://regiojet.com/?fromLocationId={from_regio}&toLocationId={to_regio}&departureDate={tarih}" if from_regio and to_regio else "https://regiojet.com"
        return (
            f"🎫 *{kalkis_sehri.upper()} -> {varis_sehri.upper()} ({tarih})*\n\n"
            f"Bilet Arama Bağlantıları:\n"
            f"✈️ [Google Flights ile Uçak Ara]({google_flights_link})\n"
            f"🚌🚆 [RegioJet ile Otobüs/Tren Ara]({regio_link})"
        )

    return "\n---\n".join(sonuclar)

@app.route("/", methods=["GET"])
def index():
    return "Bilet Botu Canlıda!"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    if data and "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "").strip()
        text_lower = text.lower()
        kelimeler = text.split()

        if "nastenka" in text_lower:
            send_telegram(chat_id, f"🕯️ *Beyaz Geceler*\n\n_{random.choice(NASTENKA_SOZLERI)}_")
        elif any(k in text_lower for k in ["söz", "soz", "leyla", "mecnun"]):
            send_telegram(chat_id, f"🕯️ *Günün Sözü*\n\n_{random.choice(GENEL_SOZLER)}_")
        elif len(kelimeler) >= 2:
            kalkis, varis = kelimeler[0], kelimeler[1]
            tarih = kelimeler[2] if len(kelimeler) >= 3 else None
            send_telegram(chat_id, f"🔎 *{kalkis.upper()} -> {varis.upper()}* taranıyor...")
            rapor = dinamik_bilet_tara(kalkis, varis, tarih)
            send_telegram(chat_id, rapor)
        else:
            send_telegram(chat_id, "🤖 *Kullanım:* `Prag Roma 2026-11-20` veya `nastenka` yazabilirsiniz.")

    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
