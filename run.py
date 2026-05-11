from flask import Flask, render_template_string, request, jsonify
import random
import os
import requests

# =========================
# FLASK APP
# =========================
app = Flask(__name__)

# =========================
# GEMINI API KEY
# =========================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# =========================
# BASE DE DONNÉES SIMULÉE
# =========================
MARKET_DB = {
    "iPhone 13": 520,
    "iPhone 12 Pro": 430,
    "MacBook Air M1": 900,
    "PS5": 500,
    "Samsung S21": 360,
    "AirPods Pro": 220,
    "iPad 9": 340,
    "Apple Watch": 300
}

# =========================
# GÉNÉRATION PRODUITS
# =========================
def generate_ads():
    return [
        {
            "title": name,
            "price": market + random.randint(-150, 150),
            "market": market
        }
        for name, market in MARKET_DB.items()
    ]

# =========================
# SCORE IA
# =========================
def score(price, market):
    return max(0, min(100, round(50 + ((market - price) / market) * 120, 1)))

# =========================
# GEMINI AI ANALYSIS
# =========================
def explain(price, market, title):

    if not GEMINI_API_KEY:
        return "Clé Gemini manquante"

    prompt = f"""
Tu es un expert en analyse de prix.

Produit : {title}
Prix affiché : {price}€
Prix moyen du marché : {market}€

Donne une analyse courte en français (2 phrases max).
Dis si c'est une bonne affaire ou non.
"""

    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }

    try:
        response = requests.post(url, json=payload, timeout=10)

        data = response.json()

        # =========================
        # DEBUG ERREUR API
        # =========================
        if "error" in data:
            return f"Erreur Gemini: {data['error']['message']}"

        # =========================
        # DEBUG FORMAT
        # =========================
        if "candidates" not in data:
            return f"Réponse inconnue: {data}"

        # =========================
        # RÉPONSE IA
        # =========================
        return data["candidates"][0]["content"]["parts"][0]["text"]

    except Exception as e:
        return f"Erreur IA: {str(e)}"

# =========================
# FRONTEND HTML
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
}

.card{
    background:#1e293b;
    margin:10px auto;
    width:420px;
    padding:15px;
    border-radius:10px;
    text-align:left;
}

.good{
    color:#22c55e;
}

.bad{
    color:#ef4444;
}
</style>
</head>

<body>

<h1>🚀 AI Deal SaaS (Gemini)</h1>

<input id="q" placeholder="ex: iPhone">
<button onclick="search()">Search</button>

<div id="out"></div>

<script>
async function search(){

    const q = document.getElementById("q").value;

    const res = await fetch("/search?q=" + q);

    const data = await res.json();

    let html = "";

    data.forEach(d => {

        let c = d.score > 75 ? "good" : "bad";

        html += `
        <div class="card">
            <h3>${d.title}</h3>

            <p>💰 ${d.price} €</p>

            <p>
                📊
                <span class="${c}">
                    ${d.score}/100
                </span>
            </p>

            <p>${d.explain}</p>
        </div>
        `;
    });

    document.getElementById("out").innerHTML = html;
}
</script>

</body>
</html>
"""

# =========================
# HOME
# =========================
@app.route("/")
def home():
    return render_template_string(HTML)

# =========================
# SEARCH API
# =========================
@app.route("/search")
def search():

    q = request.args.get("q", "").lower()

    ads = generate_ads()

    if q:
        ads = [a for a in ads if q in a["title"].lower()]

    results = []

    for a in ads:

        results.append({
            "title": a["title"],
            "price": a["price"],
            "market": a["market"],
            "score": score(a["price"], a["market"]),
            "explain": explain(
                a["price"],
                a["market"],
                a["title"]
            )
        })

    return jsonify(
        sorted(
            results,
            key=lambda x: x["score"],
            reverse=True
        )
    )

# =========================
# START SERVER
# =========================
port = int(os.environ.get("PORT", 10000))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=port)
