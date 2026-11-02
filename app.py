import os
import random
import requests
from datetime import datetime, timedelta
from flask import Flask, request, jsonify

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
SERPAPI_KEY = os.environ.get("SERPAPI_KEY", "")

# --- HAVALİMANI IATA KODLARI ---
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

# --- REGİOJET ŞEHİR / İSTASYON ID'LERİ ---
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
    "\"Bizi ne
