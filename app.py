import os
import random
import requests
from datetime import datetime, timedelta
from flask import Flask, request, jsonify

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "").strip()

AIRPORT_CODES = {
    "prag": "PRG", "prague": "PRG",
    "brno": "BRQ", "ostrava": "OSR",
    "viyana": "VIE", "vienna": "VIE",
    "roma": "FCO", "rome": "FCO",
    "berlin": "BER", "münih": "MUC", "munich": "MUC",
    "budapeşte": "BUD", "budapest": "BUD",
    "varşova": "WAW", "warsaw": "WAW",
    "krakow": "KRK", "amsterdam": "AMS", "paris": "CDG"
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

def bilet_servisi_tara(kalkis, varis, tarih_str):
    tarih = tarih_formatla(tarih_str)
    dep_code = AIRPORT_CODES.get(kalkis.lower(), kalkis.upper())
    arr_code = AIRPORT_CODES.get(varis.lower(), varis.upper())

    mesaj_bloklari = []

    # REGIOJET DIRECT API SORGUSU
    from_id = REGIOJET_IDS.get(kalkis.lower())
    to_id = REGIOJET_IDS.get(varis.lower())

    if from_id and to_id:
        try:
            url = f"https://brn-yee-api.regiojet.com/rest/busTickets/search?fromLocationId={from_id}&toLocationId={to_id}&departureDate={tarih}"
            headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
            res = requests.get(url, headers=headers, timeout=8)
            if res.status_code == 200:
                data = res.json()
                routes = data.get("routes", [])
                if routes:
                    sefer_metinleri = []
                    for r in routes[:3]:
                        fiyat = r.get("priceFrom", "Bilinmiyor")
                        arac = "🚆 Tren" if "TRAIN" in r.get("vehicleTypes", []) else "🚌 Otobüs"
                        saat_raw = r.get("departureTime", "")
                        saat = saat_raw.split("T")[-1][:5] if "T" in saat_raw else "Bilinmiyor"
                        sefer_metinleri.append(f"• {arac} | Saat: `{saat}` | Fiyat: `{fiyat} EUR/CZK`")
                    
                    regio_metni = (
                        f"🚌 *REGIOJET CANLI SEFERLERİ*\n"
                        + "\n".join(sefer_metinleri) +
                        f"\n🔗 [RegioJet'ten Bilet Al](https://regiojet.com/?fromLocationId={from_id}&toLocationId={to_id}&departureDate={tarih})"
                    )
                    mesaj_bloklari.append(regio_metni)
        except Exception as e:
            print(f"RegioJet hatası: {e}")

    # UÇAK BİLETİ CANLI ARAMA LİNKLERİ
    google_flights = f"https://www.google.com/travel/flights?q=Flights%20to%20{arr_code}%20from%20{dep_code}%20on%20{tarih}"
    skyscanner = f"https://www.skyscanner.net/transport/flights/{dep_code.lower()}/{arr_code.lower()}/{tarih[2:].replace('-', '')}/"
    
    ucak_metni = (
        f"✈️ *UÇAK BİLETİ ARAMASI*\n"
        f"📍 Güzergah: `{dep_code}` ➡️ `{arr_code}` | Tarih: `{tarih}`\n"
        f"🔗 [Google Flights Üzerinden Canlı Fiyat Gör]({google_flights})\n"
        f"🔗 [Skyscanner Üzerinden Fiyat Karşılaştır]({skyscanner})"
    )
    mesaj_bloklari.append(ucak_metni)

    return f"🎫 *{kalkis.upper()} -> {varis.upper()} BİLET ARAMASI*\n\n" + "\n\n---\n\n".join(mesaj_bloklari)

@app.route("/", methods=["GET"])
def index():
    return "Bot Aktif"

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
            rapor = bilet_servisi_tara(kalkis, varis, tarih)
            send_telegram(chat_id, rapor)
        else:
            send_telegram(chat_id, "🤖 *Kullanım:* `Prag Viyana` veya `Prag Roma 2026-11-20`")

    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
