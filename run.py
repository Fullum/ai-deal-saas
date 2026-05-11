from flask import Flask, render_template_string, request, jsonify
import requests
import os
import random
from bs4 import BeautifulSoup

app = Flask(__name__)

# =========================
# 🔑 GEMINI KEY
# =========================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# =========================
# 🔍 SCRAP EBAY (vraies données)
# =========================
def generate_real_ads(query):

    if not query:
        return []

    url = f"https://www.ebay.fr/sch/i.html?_nkw={query}"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")

        items = soup.select(".s-item")

        results = []

        for item in items[:10]:

            title = item.select_one(".s-item__title")
            price = item.select_one(".s-item__price")

            if not title or not price:
                continue

            try:
                p = price.text.replace("EUR", "").replace("€", "").replace(",", ".")
                value = float(p.split()[0])

                results.append({
                    "title": title.text,
                    "price": value
                })

            except:
                continue

        return results

    except:
        return []

# =========================
# 📊 PRIX MOYEN MARCHÉ
# =========================
def market_price(ads):

    if not ads:
        return 0

    return round(sum(a["price"] for a in ads) / len(ads), 2)

# =========================
# 🧠 SCORE
# =========================
def score(price, market):

    if market == 0:
        return 50

    return max(
        0,
        min(
            100,
            round(50 + ((market - price) / market) * 120, 1)
        )
    )

# =========================
# 🧠 FALLBACK IA
# =========================
def fallback(price, market):

    diff = price - market

    if diff <= -50:
        return "🔥 Excellente affaire"
    elif diff < 0:
        return "✅ Bonne affaire"
    elif diff <= 50:
        return "⚠️ Prix correct"
    else:
        return "❌ Trop cher"

# =========================
# 🤖 GEMINI IA
# =========================
def explain(price, market, title):

    if not GEMINI_API_KEY:
        return fallback(price, market)

    prompt = f"""
Produit: {title}
Prix: {price}€
Marché: {market}€

Analyse en 2 phrases max :
"""

    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

    payload = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ]
    }

    try:

        r = requests.post(url, json=payload, timeout=10)
        data = r.json()

        if "error" in data:
            return fallback(price, market)

        return data["candidates"][0]["content"]["parts"][0]["text"]

    except:
        return fallback(price, market)

# =========================
# 🎨 FRONT
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

<h1>🚀 AI Deal SaaS (Gemini + eBay)</h1>

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

    ads = generate_real_ads(q)

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
# 🚀 START
# =========================
port = int(os.environ.get("PORT", 10000))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=port)
