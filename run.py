from flask import Flask, render_template_string, request, jsonify
import os
import time
import random

app = Flask(__name__)

# =========================
# USERS + SUBSCRIPTION SYSTEM
# =========================
USERS = {
    "free": {"requests": 0, "limit": 20}
}

# =========================
# PRICE HISTORY (DATA CORE)
# =========================
PRICE_HISTORY = {}

# =========================
# ALERTS SYSTEM
# =========================
ALERTS = []

# =========================
# BASE MARKET
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
# FRONTEND SaaS DASHBOARD
# =========================
HTML = """
<!DOCTYPE html>
<html>
<head>
<title>SaaS Monetization PRO</title>
<style>
body{font-family:Arial;background:#0f172a;color:white;text-align:center;padding:20px}
input{padding:10px;width:250px;border-radius:6px;border:none}
button{padding:10px;background:#22c55e;border:none;border-radius:6px;cursor:pointer}
.card{background:#1e293b;margin:10px auto;width:460px;padding:15px;border-radius:10px;text-align:left}
.good{color:#22c55e}
.mid{color:#facc15}
.bad{color:#ef4444}
small{color:#94a3b8}
.section{margin-top:20px}
.badge{background:#334155;padding:5px;border-radius:6px;font-size:12px}
</style>
</head>
<body>

<h1>🚀 SaaS Monetization PRO</h1>

<p class="badge">Free plan: 20 recherches</p>

<input id="q" placeholder="ex: PS5">
<button onclick="search()">Search</button>

<div id="out"></div>

<h2 class="section">🔔 Alertes</h2>

<input id="item" placeholder="produit">
<input id="price" placeholder="prix cible">
<button onclick="addAlert()">Ajouter</button>

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
            <small>Plan: ${d.plan}</small>
        </div>`;
    });

    document.getElementById("out").innerHTML=html;
}

async function addAlert(){
    const item=document.getElementById("item").value;
    const price=document.getElementById("price").value;

    await fetch("/alert",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({item,price})});

    loadAlerts();
}

async function loadAlerts(){
    const res=await fetch("/alerts");
    const data=await res.json();

    let html="<h3>Mes alertes</h3>";

    data.forEach(a=>{
        html+=`<div class="card">${a.item} → ${a.price}€</div>`;
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
# SUBSCRIPTION CHECK
# =========================
def check_limit(user="free"):
    if USERS[user]["requests"] >= USERS[user]["limit"]:
        return False
    USERS[user]["requests"] += 1
    return True

# =========================
# MARKET PRICE
# =========================
def market_price(q):
    return BASE_MARKET.get(q.lower(), 500)

# =========================
# AI SCORING PRO
# =========================
def score(price, market):
    ratio = price / market

    noise = random.uniform(-2, 2)

    return max(0, min(100, round(100 - ratio * 100 + noise, 1)))

# =========================
# LABEL ENGINE
# =========================
def label(s):
    if s >= 85:
        return "🔥 Deal exceptionnel"
    elif s >= 70:
        return "✅ Bonne affaire"
    elif s >= 50:
        return "⚠️ Prix correct"
    elif s >= 30:
        return "❌ Peu intéressant"
    return "❌ Mauvais deal"

# =========================
# PRICE HISTORY
# =========================
def add_history(p, price):
    PRICE_HISTORY.setdefault(p, []).append({
        "price": price,
        "time": time.time()
    })

# =========================
# SEARCH ENGINE
# =========================
@app.route("/search")
def search():
    q = request.args.get("q","ps5").lower()

    # LIMIT SYSTEM (MONETIZATION CORE)
    if not check_limit():
        return jsonify([{
            "title": "LIMIT REACHED",
            "price": 0,
            "score": 0,
            "label": "❌ Upgrade required",
            "explain": "Limite gratuite atteinte. Passe au plan Pro.",
            "plan": "FREE"
        }])

    market = market_price(q)

    price = market + random.randint(-70, 120)

    s = score(price, market)

    add_history(q, price)

    return jsonify([{
        "title": q.upper(),
        "price": round(price,2),
        "market": market,
        "score": s,
        "label": label(s),
        "explain": "IA scoring + historique + système SaaS",
        "plan": "FREE"
    }])

# =========================
# ALERT SYSTEM
# =========================
@app.route("/alert", methods=["POST"])
def alert():
    data = request.json
    ALERTS.append(data)
    return {"status":"ok"}

@app.route("/alerts")
def alerts():
    return jsonify(ALERTS)

# =========================
# ANALYTICS (PRO SaaS CORE)
# =========================
@app.route("/analytics")
def analytics():
    return jsonify({
        "users": len(USERS),
        "requests_used": USERS["free"]["requests"],
        "limit": USERS["free"]["limit"],
        "products_tracked": len(PRICE_HISTORY),
        "alerts": len(ALERTS)
    })

# =========================
# RUN
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
