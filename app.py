import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
SERPAPI_KEY = os.environ.get("SERPAPI_KEY", "")

# Popüler şehir kodları haritası
CITY_CODES = {
    "prag": "PRG", "prague": "PRG",
    "viyana": "VIE", "vienna": "VIE",
    "roma": "FCO", "rome": "FCO",
    "berlin": "BER",
    "münih": "MUC", "munich": "MUC",
    "paris": "CDG",
    "londra": "LON", "london": "LON",
    "budapeşte": "BUD", "budapest": "BUD",
    "amsterdam": "AMS"
}

def send_telegram(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }
    requests.post(url, json=payload)

def dinamik_bilet_tara(kalkis_sehri, varis_sehri, tarih="2026-11-20"):
    sonuclar = []

    # Şehir isimlerini IATA koduna çevir
    dep_code = CITY_CODES.get(kalkis_sehri.lower(), kalkis_sehri.upper())
    arr_code = CITY_CODES.get(varis_sehri.lower(), varis_sehri.upper()) if varis_sehri.lower() != "heryer" else "EC"

    # 1. UÇAK TARAMASI (Google Flights / SerpApi)
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
        res = requests.get("https://serpapi.com/search", params=params, timeout=10).json()
        flights = res.get("best_flights", []) + res.get("other_flights", [])

        for f in flights[:5]:
            price = f.get("price", 999)
            leg = f["flights"][0]
            airline = leg.get("airline", "Hava Yolu")
            dep_time = leg["departure_airport"].get("time", "")
            
            msg = (
                f"✈️ *UÇAK BİLETİ*\n"
                f"🛫 *Kalkış:* {dep_code} -> 🛬 *Varış:* {f['flights'][-1]['arrival_airport'].get('name', arr_code)}\n"
                f"✈️ *Firma:* {airline}\n"
                f"📅 *Tarih/Saat:* {tarih} {dep_time}\n"
                f"💰 *Fiyat:* {price} EUR\n"
                f"🔗 [Google Flights İncele](https://www.google.com/travel/flights)\n"
            )
            sonuclar.append(msg)
    except Exception as e:
        print(f"Uçak hatası: {e}")

    # 2. OTOBÜS & TREN TARAMASI (RegioJet)
    # Eğer kalkış České Budějovice veya Prag ise otobüs/tren API'sini sorgula
    try:
        url = "https://brn-yee-api.regiojet.com/rest/busTickets/search"
        # České Budějovice ID: 10202000 | Prag ID: 10202002
        cb_id = "10202000" if "budějovice" in kalkis_sehri.lower() or "cb" in kalkis_sehri.lower() else "10202002"
        
        params = {"fromLocationId": cb_id, "toLocationId": "10202003", "departureDate": tarih}
        res = requests.get(url, params=params, timeout=10).json()
        
        for r in res.get("routes", [])[:3]:
            price = r.get("priceFrom", 999)
            vehicle = "🚆 Tren" if r.get("vehicleTypes", [])[0] == "TRAIN" else "🚌 Otobüs"
            dep_time = r.get("departureTime").split("T")[1][:5]
            
            msg = (
                f"{vehicle} *BİLETİ*\n"
                f"🛫 {kalkis_sehri.capitalize()} -> 🛬 Sefer\n"
                f"📅 *Saat:* {dep_time}\n"
                f"💰 *Fiyat:* {price} EUR / CZK\n"
                f"🔗 [RegioJet Sitesinde Gör](https://regiojet.com)\n"
            )
            sonuclar.append(msg)
    except Exception as e:
        print(f"Otobüs hatası: {e}")

    if not sonuclar:
        return "⚠️ Belirttiğin kriterlerde uygun bilet bulunamadı."
    
    return "\n---\n".join(sonuclar)

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    if data and "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "").strip()

        # Kullanıcının attığı mesajı analiz et
        kelimeler = text.split()

        # Örnek Kullanım: "Prag Roma" veya "Viyana Berlin 2026-11-20"
        if len(kelimeler) >= 2:
            kalkis = kelimeler[0]
            varis = kelimeler[1]
            tarih = kelimeler[2] if len(kelimeler) >= 3 else "2026-11-20"

            send_telegram(chat_id, f"🔎 *{kalkis.upper()} -> {varis.upper()}* için uçak, otobüs ve trenler taranıyor...")
            rapor = dinamik_bilet_tara(kalkis, varis, tarih)
            send_telegram(chat_id, rapor)
        else:
            send_telegram(chat_id, (
                "🤖 *Nasıl Kullanılır?*\n\n"
                "Arama yapmak için kalkış ve varış şehirlerini yazın:\n"
                "👉 Örnek: `Prag Roma`\n"
                "👉 Örnek: `Viyana Berlin`\n"
                "👉 Örnek: `Prag Roma 2026-11-25`\n"
            ))

    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))