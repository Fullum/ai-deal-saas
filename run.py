from flask import Flask, render_template_string, request, jsonify
import os
import time
import random

app = Flask(__name__)

# =========================
# CONFIG
# =========================
USERS_DB = {}
ALERTS_DB = []
PRICE_HISTORY = {}

# =========================
# BASE PRODUITS
# =========================
BASE_MARKET = {
    "ps5": 500,
    "xbox": 450,
    "iphone 13": 600,
    "iphone 14": 750,
    "macbook air m1": 900,
    "airpods pro": 220
}

# =========================
# FRONTEND DASHBOARD SaaS
# =========================
HTML = """
<!DOCTYPE html>
<html>
<head>
<title>SaaS V2 Monetization AI</title>
<style>
body{font-family:Arial;background:#0f172a;color:white;text-align:center;padding:20px}
input{padding:10px;width:250px;border-radius:6px;border:none}
button{padding:10px;background:#22c55e;border:none;border-radius:6px;cursor:pointer;margin:5px}
.card{background:#1e293b;margin:10px auto;width:450px;padding:15px;border-radius:10px;text-align:left}
.good{color:#22c55e}
.mid{color:#facc15}
.bad{color:#ef4444}
small{color:#94a3b8}
.section{margin-top:20px}
</style>
</head>
<body>

<h1>🚀 SaaS V2 AI Deal Platform</h1>

<input id="q" placeholder="ex: PS5">
<button onclick="search()">Search</button>

<div id="out"></div>

<h2 class="section">🔔 Alertes prix</h2>
<input id="alert_item" placeholder="produit">
<input id="alert_price" placeholder="prix cible">
<button onclick="addAlert()">Ajouter alerte</button>

<div id="alerts"></div>

<script>

async function search(){
    const q=document.getElementById("q").value;
    const res=await fetch("/search?q="+q);
    const data=await res.json();

    let html="";
    data.forEach(d=>{
        let c = d.score>=80?"good":d.score>=50?"mid":"bad";

        html+=`
        <div class="card">
            <h3>${d.title}</h3>
            <p>💰 ${d.price} €</p>
            <p>📊 <span class="${c}">${d.score}/100</span></p>
            <p><b>${d.label}</b></p>
            <p>${d.explain}</p>
            <small>Source: ${d.source}</small>
        </div>`;
    });

    document.getElementById("out").innerHTML=html;
}

async function addAlert(){
    const item=document.getElementById("alert_item").value;
    const price=document.getElementById("alert_price").value;

    await fetch("/alert",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({item,price})
    });

    loadAlerts();
}

async function loadAlerts(){
    const res=await fetch("/alerts");
    const data=await res.json();

    let html="<h3>Mes alertes</h3>";

    data.forEach(a=>{
        html+=`<div class="card">
            ${a.item} - cible: ${a.price}€
        </div>`;
    });

    document.getElementById("alerts").innerHTML=html;
}

loadAlerts();

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
# HISTORIQUE PRIX (DATA ENGINE)
# =========================
def add_history(product, price):
    if product not in PRICE_HISTORY:
        PRICE_HISTORY[product] = []

    PRICE_HISTORY[product].append({
        "price": price,
        "time": time.time()
    })

# =========================
# IA SCORING (ML LIGHT SIMULÉ)
# =========================
def ai_score(price, market):
    ratio = price / market

    noise = random.uniform(-3, 3)

    score = 100 - (ratio * 100) + noise

    return max(0, min(100, round(score, 1)))

# =========================
# LABELS
# =========================
def label(score):
    if score >= 85:
        return "🔥 Opportunité exceptionnelle"
    elif score >= 70:
        return "✅ Bonne affaire"
    elif score >= 50:
        return "⚠️ Prix correct"
    elif score >= 30:
        return "❌ Peu intéressant"
    return "❌ Mauvais deal"

# =========================
# MARKET ESTIMATION
# =========================
def estimate(q):
    q = q.lower()
    return BASE_MARKET.get(q, 500)

# =========================
# ENGINE PRINCIPAL
# =========================
@app.route("/search")
def search():
    q = request.args.get("q","ps5").lower()

    market = estimate(q)

    # simulation prix marché réel
    price = market + random.randint(-80, 120)

    score = ai_score(price, market)

    label_txt = label(score)

    # historique
    add_history(q, price)

    return jsonify([{
        "title": q.upper(),
        "price": round(price,2),
        "market": market,
        "score": score,
        "label": label_txt,
        "explain": "IA scoring + historique + simulation marché",
        "source": "AI Engine V2"
    }])

# =========================
# ALERTES PRIX
# =========================
@app.route("/alert", methods=["POST"])
def alert():
    data = request.json

    ALERTS_DB.append({
        "item": data["item"],
        "price": data["price"]
    })

    return {"status":"ok"}

@app.route("/alerts")
def alerts():
    return jsonify(ALERTS_DB)

# =========================
# ANALYTICS SIMPLE
# =========================
@app.route("/analytics")
def analytics():
    return jsonify({
        "tracked_products": len(PRICE_HISTORY),
        "alerts": len(ALERTS_DB),
        "history": PRICE_HISTORY
    })

# =========================
# RUN
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
