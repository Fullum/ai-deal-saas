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
    return max(
        0,
        min(
            100,
            round(50 + ((market - price) / market) * 120, 1)
        )
    )

# =========================
# FALLBACK SI IA HS
# =========================
def fallback_analysis(price, market):

    diff = price - market

    if diff <= -50:
        return "🔥 Excellente affaire. Le prix est largement inférieur au marché."

    elif diff < 0:
        return "✅ Bonne affaire. Prix légèrement inférieur au marché."

    elif diff <= 50:
        return "⚠️ Prix correct mais peu intéressant."

    else:
        return "❌ Trop cher par rapport au prix moyen du marché."

# =========================
# GEMINI AI ANALYSIS
# =========================
def explain(price, market, title):

    # =========================
    # PAS DE CLÉ
    # =========================
    if not GEMINI_API_KEY:
        return fallback_analysis(price, market)

    prompt = f"""
Tu es un expert en analyse de prix.

Produit : {title}
Prix affiché : {price}€
Prix moyen du marché : {market}€

Donne une analyse courte en français.
Maximum 2 phrases.
"""

    url = (
        "https://generativelanguage.googleapis.com/v1/models/"
        f"gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ]
    }

    try:

        response = requests.post(
            url,
            json=payload,
            timeout=10
        )

        data = response.json()

        # =========================
        # ERREUR API
        # =========================
        if "error" in data:

            error_msg = str(data["error"])

            # QUOTA GOOGLE
            if "quota" in error_msg.lower():
                return fallback_analysis(price, market)

            return "⚠️ IA temporairement indisponible."

        # =========================
        # FORMAT INVALIDE
        # =========================
        if "candidates" not in data:
            return fallback_analysis(price, market)

        # =========================
        # RÉPONSE IA
        # =========================
        return data["candidates"][0]["content"]["parts"][0]["text"]

    except:
        return fallback_analysis(price, market)

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
        ads = [
            a for a in ads
            if q in a["title"].lower()
        ]

    results = []

    for a in ads:

        results.append({

            "title": a["title"],

            "price": a["price"],

            "market": a["market"],

            "score": score(
                a["price"],
                a["market"]
            ),

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
    app.run(
        host="0.0.0.0",
        port=port
    )
