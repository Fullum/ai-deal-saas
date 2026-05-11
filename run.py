from flask import Flask, render_template_string, request, jsonify
import os
import random
import requests

app = Flask(__name__)

# =========================
# 🔑 GEMINI KEY
# =========================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# =========================
# 🧠 BASE MARCHÉ
# =========================
MARKET_DB = {
    "ps5": 500,
    "playstation 5": 500,
    "iphone": 650,
    "iphone 13": 520,
    "macbook air m1": 900,
    "samsung s21": 360,
    "airpods": 220,
    "ipad": 340
}

# =========================
# 📦 GENERATION OFFRES
# =========================
def generate_ads(query):

    if not query:
        return []

    base_price = MARKET_DB.get(query.lower(), 500)

    ads = []

    for i in range(8):
        price = base_price + random.randint(-200, 200)

        ads.append({
            "title": f"{query.upper()} - Offre {i+1}",
            "price": max(50, price)
        })

    return ads

# =========================
# 📊 PRIX MOYEN
# =========================
def market_price(ads):

    if not ads:
        return 0

    prices = [a.get("price") for a in ads if a.get("price") is not None]

    if not prices:
        return 0

    return round(sum(prices) / len(prices), 2)

# =========================
# 📈 SCORE SAFE
# =========================
def score(price, market):

    if not market or market == 0:
        return 50

    try:
        return max(
            0,
            min(
                100,
                round(50 + ((market - price) / market) * 120, 1)
            )
        )
    except:
        return 50

# =========================
# 🧠 FALLBACK IA (TOUJOURS OK)
# =========================
def simple_ai(price, market, title):

    diff = price - market

    if diff <= -80:
        return "🔥 Excellente affaire (fortement sous le marché)"
    elif diff < 0:
        return "✅ Bonne affaire"
    elif diff <= 50:
        return "⚠️ Prix correct"
    else:
        return "❌ Trop cher"

# =========================
# 🤖 GEMINI + FALLBACK
# =========================
def explain(price, market, title):

    # pas de clé
    if not GEMINI_API_KEY:
        return simple_ai(price, market, title)

    try:

        url = (
            "https://generativelanguage.googleapis.com/v1beta/"
            f"models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
        )

        prompt = f"""
Analyse ce produit :

Nom: {title}
Prix: {price}€
Marché: {market}€

Donne une analyse courte (1-2 phrases).
"""

        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ]
        }

        r = requests.post(url, json=payload, timeout=6)

        data = r.json()

        # sécurité structure
        if not isinstance(data, dict):
            return simple_ai(price, market, title)

        if "candidates" not in data:
            return simple_ai(price, market, title)

        return data["candidates"][0]["content"]["parts"][0]["text"]

    except:
        return simple_ai(price, market, title)

# =========================
# 🎨 FRONTEND
# =========================
HTML = """
<!DOCTYPE html>
<html>

<head>
<title>AI Deal SaaS</title>

<style>

body{
    font-family:Arial;
    background:#0f172a;
    color:white;
    text-align:center;
    padding:20px;
}

input{
    padding:10px;
    width:250px;
}

button{
    padding:10px;
    background:#22c55e;
    border:none;
    cursor:pointer;
    color:white;
    font-weight:bold;
}

.card{
    background:#1e293b;
    margin:10px auto;
    width:420px;
    padding:15px;
    border-radius:10px;
    text-align:left;
}

.good{color:#22c55e;}
.bad{color:#ef4444;}

</style>

</head>

<body>

<h1>🚀 AI Deal SaaS (Stable Pro)</h1>

<input id="q" placeholder="ex: PS5">
<button onclick="search()">Search</button>

<div id="out"></div>

<script>

async function search(){

    const q = document.getElementById("q").value;

    const res = await fetch("/search?q=" + q);
    const data = await res.json();

    let html = "";

    data.forEach(d => {

        let c = d.score > 70 ? "good" : "bad";

        html += `
        <div class="card">

            <h3>${d.title}</h3>

            <p>💰 ${d.price} €</p>

            <p>📊 <span class="${c}">${d.score}/100</span></p>

            <p>${d.explain}</p>

        </div>`;
    });

    document.getElementById("out").innerHTML = html;
}

</script>

</body>

</html>
"""

# =========================
# 🏠 HOME
# =========================
@app.route("/")
def home():
    return render_template_string(HTML)

# =========================
# 🔎 SEARCH API
# =========================
@app.route("/search")
def search():

    q = request.args.get("q", "")

    if not q:
        return jsonify([])

    ads = generate_ads(q)

    market = market_price(ads)

    results = []

    for a in ads:

        results.append({
            "title": a["title"],
            "price": a["price"],
            "score": score(a["price"], market),
            "explain": explain(a["price"], market, a["title"])
        })

    return jsonify(results)

# =========================
# 🚀 START SERVER
# =========================
port = int(os.environ.get("PORT", 10000))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=port)
