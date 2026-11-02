import os
import random
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
SERPAPI_KEY = os.environ.get("SERPAPI_KEY", "")

# Popüler Şehir IATA ve RegioJet ID Kodları
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

REGIOJET_DEST_IDS = {
    "prag": "10202002", "prague": "10202002",
    "viyana": "10202003", "vienna": "10202003",
    "berlin": "10202004",
    "münih": "10202005", "munich": "10202005"
}

# --- SÖZ KATEGORİLERİ VE LİSTELERİ ---
NASTENKA_SOZLERI = [
    "\"Senin bir tek gülücüğün, bana bir ömür boyu hayal kurmak için yeter Nastenka... Seni sevmek bana yetiyor, sevilmesem de olur.\" — Fyodor Dostoyevski (Beyaz Geceler)",
    "\"Tanrım! Bir dakikalık mutluluk! Bütün bir insan ömrü için az bir şey mi bu?\" — Fyodor Dostoyevski (Beyaz Geceler)",
    "\"Ben bir hayalperestim. Gerçek hayatta o kadar az yaşadım ki, seninle geçirdiğim bu anlar benim bütün hayatım olacak.\" — Fyodor Dostoyevski (Beyaz Geceler)",
    "\"Beni sevmene gerek yok Nastenka, sadece var ol ve bazen gökyüzüne bakarken beni hatırla.\" — Fyodor Dostoyevski (Beyaz Geceler)",
    "\"Sevilmek bir lütuftur ama karşılıksız da olsa o kadar katıksız sevebilmek bir ruha verilebilecek en büyük armağandır.\" — Fyodor Dostoyevski (Beyaz Geceler)",
    "\"Sadece bir anlığına göz göze gelmiştik ama ben o bir anın içinde bir ömrü kaybettim.\" — Fyodor Dostoyevski (Beyaz Geceler)",
    "\"Şimdi hangi şehrin caddesinde yürürsem yürüyeyim, adımlarım hep senin hiç gitmediğin o sokağa çıkıyor Nastenka...\" — Fyodor Dostoyevski (Beyaz Geceler)"
]

GENEL_SOZLER = NASTENKA_SOZLERI + [
    # Oğuz Atay (Tutunamayanlar & Tehlikeli Oyunlar)
    "\"Beni hemen anlamalısın, çünkü ben dünyayı anlamıyorum.\" — Oğuz Atay (Tutunamayanlar)",
    "\"Şu anda, sana güzel bir söz söyleyebilmek için 10.000 kitap okumuş olmayı isterdim. Yine de seni seviyorum.\" — Oğuz Atay (Tutunamayanlar)",
    "\"Bizi ne zaman anlayacaklar Olric? Hiçbir zaman... Zaten anlamalarına da gerek kalmadı.\" — Oğuz Atay (Tutunamayanlar)",
    "\"Belli bir sebebi yok; sadece içimde büyük bir kırgınlık var, bir de hiçbir yere sığamama hissi.\" — Oğuz Atay (Tehlikeli Oyunlar)",
    "\"Bizler, hayatın kıyısında durup içeriye girmeye cesaret edemeyen tutunamayanlarız.\" — Oğuz Atay",

    # Leyla ile Mecnun (Dizi Replikleri)
    "\"O gemi bir gün gelecek Mecnun... Biz sadece yanlış limanda bekliyoruz.\" — İsmail Abi (Leyla ile Mecnun)",
    "\"Ben seni öyle bir severim ki, sen bile kendini sevmeye doyamazsın Leyla.\" — Mecnun (Leyla ile Mecnun)",
    "\"Ben birisini sevdim Leyla... Ama o başkasını sevdi. Sonra ben kendimi sevmeyi de unuttum.\" — Mecnun (Leyla ile Mecnun)",
    "\"İnsan birini bu kadar çok severken, onun yokluğunda nasıl böyle tek başına kalabilir ki?\" — Mecnun (Leyla ile Mecnun)",
    "\"Kireçburnu sahili çok güzel de... İçindeki insanı yakınca soğuk oluyor be abi.\" — İsmail Abi (Leyla ile Mecnun)",
    "\"Benim hayallerim vardı Leyla. Sonra sen geldin, hayallerimden daha güzel bir şey oldun. Şimdi gidersen geriye sadece boşluk kalır.\" — Mecnun (Leyla ile Mecnun)",
    "\"Giden gidiyor Mecnun, kalan sadece el sallıyor.\" — İsmail Abi (Leyla ile Mecnun)",

    # Diğer Hassas Kalpler (Kafka, Zweig, Sabahattin Ali)
    "\"Seni tanıdığımdan beri kalbimin bir köşesinde hep ince, sızlayan bir sızı var. Geçmesini hiç istemediğim bir sızı...\" — Franz Kafka (Milena'ya Mektuplar)",
    "\"Ben sadece senin mutlu olmanı istedim; benimle olup olmamanın artık hiçbir önemi yoktu.\" — Stefan Zweig (Bilinmeyen Bir Kadının Mektubu)",
    "\"Biz ki hassas kalpleriz; dünyaya alışamayan, her rüzgarda yaprak gibi titreyenleriz.\" — Sabahattin Ali (Kürk Mantolu Madonna)",
    "\"Hassas kalpler için bu dünya bir cehennemdir.\" — Goethe"
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
        print(f"Telegram gönderme hatası: {e}")

def dinamik_bilet_tara(kalkis_sehri, varis_sehri, tarih="2026-11-20"):
    sonuclar = []

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
                f"🛫 *Kalkış:* {dep_code} -> 🛬 *Varış:* {arr_code}\n"
                f"✈️ *Firma:* {airline}\n"
                f"📅 *Tarih/Saat:* {tarih} {dep_time}\n"
                f"💰 *Fiyat:* {price} EUR\n"
                f"🔗 [Google Flights İncele](https://www.google.com/travel/flights)\n"
            )
            sonuclar.append(msg)
    except Exception as e:
        print(f"Uçak hatası: {e}")

    # 2. OTOBÜS & TREN TARAMASI (RegioJet)
    try:
        url = "https://brn-yee-api.regiojet.com/rest/busTickets/search"
        cb_id = "10202000" if "budějovice" in kalkis_sehri.lower() or "cb" in kalkis_sehri.lower() else "10202002"
        varis_id = REGIOJET_DEST_IDS.get(varis_sehri.lower(), "10202003")
        
        params = {"fromLocationId": cb_id, "toLocationId": varis_id, "departureDate": tarih}
        res = requests.get(url, params=params, timeout=10).json()
        
        for r in res.get("routes", [])[:3]:
            price = r.get("priceFrom", 999)
            vehicle = "🚆 Tren" if r.get("vehicleTypes", [])[0] == "TRAIN" else "🚌 Otobüs"
            dep_time = r.get("departureTime").split("T")[1][:5]
            
            msg = (
                f"{vehicle} *BİLETİ*\n"
                f"🛫 {kalkis_sehri.capitalize()} -> 🛬 {varis_sehri.capitalize()}\n"
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

@app.route("/", methods=["GET"])
def index():
    return "Bilet Avcısı Botu Canlıda Çalışıyor!"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    if data and "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "").strip()
        text_lower = text.lower()
        kelimeler = text.split()

        # 1. Özel "nastenka" Tetikleyicisi
        if "nastenka" in text_lower:
            secilen_soz = random.choice(NASTENKA_SOZLERI)
            send_telegram(chat_id, f"🕯️ *Nastenka'ya Hisler (Beyaz Geceler)*\n\n_{secilen_soz}_")

        # 2. Genel Söz Tetikleyicileri (söz, leyla, mecnun, tutunamayanlar vs.)
        elif any(keyword in text_lower for keyword in ["söz", "soz", "leyla", "mecnun", "tutunamayanlar", "hüzün", "huzun"]):
            secilen_soz = random.choice(GENEL_SOZLER)
            send_telegram(chat_id, f"🕯️ *Günün Sözü*\n\n_{secilen_soz}_")

        # 3. Bilet Arama Tetikleyicisi (En az 2 şehir yazıldığında)
        elif len(kelimeler) >= 2:
            kalkis = kelimeler[0]
            varis = kelimeler[1]
            tarih = kelimeler[2] if len(kelimeler) >= 3 else "2026-11-20"

            send_telegram(chat_id, f"🔎 *{kalkis.upper()} -> {varis.upper()}* için uçak, otobüs ve trenler taranıyor...")
            rapor = dinamik_bilet_tara(kalkis, varis, tarih)
            send_telegram(chat_id, rapor)

        # 4. Yardım / Rehber Mesajı
        else:
            send_telegram(chat_id, (
                "🤖 *Bilet Avcısı & Hassas Ruhlar Botu*\n\n"
                "📌 *Bilet Arama:* Kalkış ve varış şehirlerini yazın.\n"
                "👉 Örnek: `Prag Roma`\n"
                "👉 Örnek: `Viyana Berlin 2026-11-25`\n\n"
                "🕯️ *Günün Sözü:* `nastenka`, `söz`, `leyla` veya `mecnun` yazarak ruhunuza dokunacak edebi sözler alabilirsiniz."
            ))

    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
