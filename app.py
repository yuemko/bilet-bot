import os
import random
import requests
from datetime import datetime, timedelta
from flask import Flask, request, jsonify

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "").strip()
SERPAPI_KEY = "38e17865fa12c48db2e73e112fe648937dad1e3dbf4649cacddf7177cde7ef5"

AIRPORT_CODES = {
    "prag": "PRG", "prague": "PRG",
    "viyana": "VIE", "vienna": "VIE",
    "roma": "FCO", "rome": "FCO",
    "berlin": "BER", "münih": "MUC"
}

REGIOJET_IDS = {
    "prag": "10202002", "prague": "10202002",
    "viyana": "10202003", "vienna": "10202003"
}

NASTENKA_SOZLERI = [
    "\"Senin bir tek gülücüğün, bana bir ömür boyu hayal kurmak için yeter Nastenka... Seni sevmek bana yetiyor, sevilmesem de olur.\" — Fyodor Dostoyevski (Beyaz Geceler)"
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

    dep_code = AIRPORT_CODES.get(kalkis_sehri.lower(), kalkis_sehri.upper())
    arr_code = AIRPORT_CODES.get(varis_sehri.lower(), varis_sehri.upper())

    serp_debug_info = ""

    # SERPAPI DOGRUDAN TESTI
    try:
        params = {
            "engine": "google_flights",
            "departure_id": dep_code,
            "arrival_id": arr_code,
            "outbound_date": tarih,
            "currency": "EUR",
            "api_key": SERPAPI_KEY
        }
        r = requests.get("https://serpapi.com/search.json", params=params, timeout=12)
        res_json = r.json()
        
        if "error" in res_json:
            serp_debug_info = f"🔴 SerpApi Hatası: {res_json.get('error')}"
        elif "best_flights" in res_json or "other_flights" in res_json:
            flights = res_json.get("best_flights", []) + res_json.get("other_flights", [])
            f = flights[0]
            price = f.get("price", "Bilinmiyor")
            airline = f.get("flights", [{}])[0].get("airline", "Hava Yolu")
            return (
                f"✈️ *UÇAK BİLETİ (SERPAPI BAŞARILI!)*\n"
                f"🛫 {dep_code} -> 🛬 {arr_code}\n"
                f"✈️ Firma: {airline}\n"
                f"💰 Fiyat: {price} EUR\n"
                f"📅 Tarih: {tarih}"
            )
        else:
            serp_debug_info = f"⚠️ SerpApi İstek Yaptı (Status {r.status_code}) Ama Uçuş Dizisi Boş Döndü."
    except Exception as e:
        serp_debug_info = f"❌ SerpApi Bağlantı Koptu: {e}"

    # REGIOJET TESTI
    from_regio = REGIOJET_IDS.get(kalkis_sehri.lower())
    to_regio = REGIOJET_IDS.get(varis_sehri.lower())
    regio_info = ""
    
    if from_regio and to_regio:
        try:
            url = "https://brn-yee-api.regiojet.com/rest/busTickets/search"
            params = {"fromLocationId": from_regio, "toLocationId": to_regio, "departureDate": tarih}
            rj_res = requests.get(url, params=params, timeout=8)
            if rj_res.status_code == 200:
                routes = rj_res.json().get("routes", [])
                if routes:
                    r_item = routes[0]
                    p = r_item.get("priceFrom", "Bilinmiyor")
                    t = r_item.get("departureTime", "").split("T")[-1][:5]
                    regio_info = f"🚌 *RegioJet Seferi Bulundu:* {t} kalkışlı - {p} CZK/EUR"
        except Exception:
            regio_info = "🚌 RegioJet bağlantısı sağlanamadı."

    google_flights_link = f"https://www.google.com/travel/flights?q=Flights%20to%20{arr_code}%20from%20{dep_code}%20on%20{tarih}"
    regio_link = f"https://regiojet.com/?fromLocationId={from_regio}&toLocationId={to_regio}&departureDate={tarih}" if from_regio and to_regio else "https://regiojet.com"

    return (
        f"🎫 *{kalkis_sehri.upper()} -> {varis_sehri.upper()} ({tarih})*\n\n"
        f"🔍 *API TEŞHİS RAPORU:*\n"
        f"{serp_debug_info}\n"
        f"{regio_info}\n\n"
        f"📌 *CANLI BİLET LİNKLERİ:*\n"
        f"✈️ [Google Flights ile Hemen Bilet Al]({google_flights_link})\n"
        f"🚌 [RegioJet ile Hemen Bilet Al]({regio_link})"
    )

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
