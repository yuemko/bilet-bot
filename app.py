import os
import random
import requests
from datetime import datetime, timedelta
from flask import Flask, request, jsonify

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
SERPAPI_KEY = os.environ.get("SERPAPI_KEY", "")

AIRPORT_CODES = {
    "prag": "PRG", "prague": "PRG",
    "brno": "BRQ", "ostrava": "OSR", "karlovy vary": "KLV", "karlovyvary": "KLV",
    "viyana": "VIE", "vienna": "VIE", "budapeşte": "BUD", "budapest": "BUD",
    "bratislava": "BTS", "berlin": "BER", "münih": "MUC", "munich": "MUC",
    "dresden": "DRS", "frankfurt": "FRA", "nürnberg": "NUE", "nuremberg": "NUE",
    "varşova": "WAW", "warsaw": "WAW", "krakow": "KRK", "wroclaw": "WRO",
    "roma": "FCO", "rome": "FCO", "milano": "MXP", "milan": "MXP",
    "venedik": "VCE", "venice": "VCE", "bologna": "BLQ", "floransa": "FLR", "florence": "FLR",
    "paris": "CDG", "amsterdam": "AMS", "brüksel": "BRU", "brussels": "BRU",
    "barselona": "BCN", "barcelona": "BCN", "madrid": "MAD", "londra": "LON", "london": "LON"
}

REGIOJET_IDS = {
    "prag": "10202002", "prague": "10202002",
    "cb": "10202000", "budějovice": "10202000", "ceske budejovice": "10202000",
    "brno": "10202001", "pilsen": "10202006", "plzen": "10202006",
    "ostrava": "10202007", "olomouc": "10202008", "liberec": "10202009",
    "hradec kralove": "10202010", "hradec": "10202010", "pardubice": "10202011",
    "karlovy vary": "10202012", "karlovyvary": "10202012", "zlin": "10202013",
    "jihlava": "10202014", "usti": "10202015", "usti nad labem": "10202015",
    "viyana": "10202003", "vienna": "10202003", "berlin": "10202004",
    "münih": "10202005", "munich": "10202005", "dresden": "10202016",
    "nürnberg": "10202021", "nuremberg": "10202021", "frankfurt": "10202022",
    "bratislava": "10202017", "budapeşte": "10202018", "budapest": "10202018",
    "krakow": "10202019", "varşova": "10202020", "warsaw": "10202020",
    "wroclaw": "10202023", "venedik": "10202024", "venice": "10202024",
    "milano": "10202025", "milan": "10202025", "roma": "10202026", "rome": "10202026",
    "amsterdam": "10202027"
}

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
    "\"Beni hemen anlamalısın, çünkü ben dünyayı anlamıyorum.\" — Oğuz Atay (Tutunamayanlar)",
    "\"Şu anda, sana güzel bir söz söyleyebilmek için 10.000 kitap okumuş olmayı isterdim. Yine de seni seviyorum.\" — Oğuz Atay (Tutunamayanlar)",
    "\"Bizi ne zaman anlayacaklar Olric? Hiçbir zaman... Zaten anlamalarına da gerek kalmadı.\" — Oğuz Atay (Tutunamayanlar)",
    "\"Belli bir sebebi yok; sadece içimde büyük bir kırgınlık var, bir de hiçbir yere sığamama hissi.\" — Oğuz Atay (Tehlikeli Oyunlar)",
    "\"Bizler, hayatın kıyısında durup içeriye girmeye cesaret edemeyen tutunamayanlarız.\" — Oğuz Atay",
    "\"O gemi bir gün gelecek Mecnun... Biz sadece yanlış limanda bekliyoruz.\" — İsmail Abi (Leyla ile Mecnun)",
    "\"Ben seni öyle bir severim ki, sen bile kendini sevmeye doyamazsın Leyla.\" — Mecnun (Leyla ile Mecnun)",
    "\"Ben birisini sevdim Leyla... Ama o başkasını sevdi. Sonra ben kendimi sevmeyi de unuttum.\" — Mecnun (Leyla ile Mecnun)",
    "\"İnsan birini bu kadar çok severken, onun yokluğunda nasıl böyle tek başına kalabilir ki?\" — Mecnun (Leyla ile Mecnun)",
    "\"Kireçburnu sahili çok güzel de... İçindeki insanı yakınca soğuk oluyor be abi.\" — İsmail Abi (Leyla ile Mecnun)",
    "\"Benim hayallerim vardı Leyla. Sonra sen geldin, hayallerimden daha güzel bir şey oldun. Şimdi gidersen geriye sadece boşluk kalır.\" — Mecnun (Leyla ile Mecnun)",
    "\"Giden gidiyor Mecnun, kalan sadece el sallıyor.\" — İsmail Abi (Leyla ile Mecnun)",
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
        print(f"Telegram hatası: {e}")

def tarih_formatla(tarih_str):
    if not tarih_str:
        return (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
    try:
        parcalar = tarih_str.split("-")
        if len(parcalar) == 3:
            yil, ay, gun = parcalar[0], parcalar[1].zfill(2), parcalar[2].zfill(2)
            return f"{yil}-{ay}-{gun}"
    except Exception:
        pass
    return (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")

def dinamik_bilet_tara(kalkis_sehri, varis_sehri, tarih_girdisi=None):
    tarih = tarih_formatla(tarih_girdisi)
    sonuclar = []

    dep_code = AIRPORT_CODES.get(kalkis_sehri.lower(), kalkis_sehri.upper())
    arr_code = AIRPORT_CODES.get(varis_sehri.lower(), varis_sehri.upper())

    # 1. UÇAK TARAMASI (Google Flights)
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
            response = requests.get("https://serpapi.com/search", params=params, timeout=12)
            if response.status_code == 200:
                res = response.json()
                flights = res.get("best_flights", []) + res.get("other_flights", [])
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
                        f"🎓 *Öğrenci Notu:* ISIC / Öğrenci indirimi geçerli olabilir.\n"
                        f"🔗 [Google Flights Satın Al](https://www.google.com/travel/flights)\n"
                    )
                    sonuclar.append(msg)
        except Exception as e:
            print(f"SerpApi hatası: {e}")

    # 2. OTOBÜS & TREN TARAMASI (RegioJet REST API)
    from_regio = REGIOJET_IDS.get(kalkis_sehri.lower())
    to_regio = REGIOJET_IDS.get(varis_sehri.lower())

    if from_regio and to_regio:
        try:
            url = "https://brn-yee-api.regiojet.com/rest/busTickets/search"
            # ISO tarih formatı eklenerek API kabul garantisi sağlandı
            params = {
                "fromLocationId": from_regio,
                "toLocationId": to_regio,
                "departureDate": f"{tarih}T00:00:00.000Z",
                "tariffs": "REGULAR"
            }
            headers = {
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/json"
            }
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                res = response.json()
                routes = res.get("routes", [])
                for r in routes[:3]:
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
                        f"🎓 *ISIC Öğrenci:* İstasyonda/Sitede indirim imkanı.\n"
                        f"🔗 [RegioJet Bilet Al](https://regiojet.com)\n"
                    )
                    sonuclar.append(msg)
        except Exception as e:
            print(f"RegioJet hatası: {e}")

    # Fallback: API canlı veriyi çekemezse hazır linkler sunulur
    if not sonuclar:
        regio_link = f"https://regiojet.com/?fromLocationId={from_regio}&toLocationId={to_regio}&departureDate={tarih}" if from_regio and to_regio else "https://regiojet.com"
        google_flights_link = f"https://www.google.com/travel/flights?q=Flights%20to%20{arr_code}%20from%20{dep_code}%20on%20{tarih}"
        
        fallback_msg = (
            f"🎫 *{kalkis_sehri.upper()} -> {varis_sehri.upper()} ({tarih}) BİLET ARAMA LİNKLERİ*\n\n"
            f"Anlık otomasyon servisinde sonuç listelenemedi ancak canlı arama linklerinden hemen biletinizi sorgulayabilirsiniz:\n\n"
            f"✈️ *Uçak Biletleri:* [Google Flights Üzerinden Gör]({google_flights_link})\n"
            f"🚌🚆 *Otobüs & Tren:* [RegioJet / StudentAgency Üzerinden Gör]({regio_link})\n\n"
            f"🎓 *Öğrenci Notu:* RegioJet biletini alırken ISIC tarifesini seçmeyi unutmayın!"
        )
        return fallback_msg

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

        if "nastenka" in text_lower:
            secilen_soz = random.choice(NASTENKA_SOZLERI)
            send_telegram(chat_id, f"🕯️ *Nastenka'ya Hisler (Beyaz Geceler)*\n\n_{secilen_soz}_")

        elif any(keyword in text_lower for keyword in ["söz", "soz", "leyla", "mecnun", "tutunamayanlar", "hüzün", "huzun"]):
            secilen_soz = random.choice(GENEL_SOZLER)
            send_telegram(chat_id, f"🕯️ *Günün Sözü*\n\n_{secilen_soz}_")

        elif len(kelimeler) >= 2:
            kalkis = kelimeler[0]
            varis = kelimeler[1]
            tarih = kelimeler[2] if len(kelimeler) >= 3 else None

            send_telegram(chat_id, f"🔎 *{kalkis.upper()} -> {varis.upper()}* için biletler taranıyor...")
            rapor = dinamik_bilet_tara(kalkis, varis, tarih)
            send_telegram(chat_id, rapor)

        else:
            send_telegram(chat_id, (
                "🤖 *Bilet Avcısı Botu*\n\n"
                "📌 *Bilet Arama:* Kalkış, varış ve tarih yazın.\n"
                "👉 Örnek: `Prag Viyana`\n"
                "👉 Örnek: `Prag Roma 2026-11-20`\n\n"
                "🕯️ *Günün Sözü:* `nastenka`, `söz`, `leyla` veya `mecnun` yazabilirsiniz."
            ))

    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
