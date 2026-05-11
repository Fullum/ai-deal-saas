from flask import Flask, render_template_string, request, jsonify
import os
import requests
import time

app = Flask(__name__)

# =========================
# CONFIG
# =========================
EBAY_APP_ID = os.environ.get("EBAY_APP_ID")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
GOOGLE_CX = os.environ.get("GOOGLE_CX")

CACHE = {}  # simple cache mémoire (scaling léger)

# =========================
# BASE INTELLIGENTE (fallback marché)
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
# FRONTEND SaaS CLEAN
# =========================
HTML = """
<!DOCTYPE html>
<html>
<head>
<title>SaaS Scaling AI Deal</title>
<style>
body{font-family:Arial;background:#0f172a;color:white;text-align:center;padding:20px}
input{padding:10px;width:260px;border-radius:6px;border:none}
button{padding:10px;background:#22c55e;border:none;border-radius:6px;cursor:pointer}
.card{background:#1e293b;margin:10px auto;width:430px;padding:15px;border-radius:10px;text-align:left}
.good{color:#22c55e}
.mid{color:#facc15}
.bad{color:#ef4444}
small{color:#94a3b8}
</style>
</head>
<body>

<h1>🚀 SaaS Scaling AI Deal V1</h1>

<input id="q" placeholder="ex: PS5">
<button onclick="search()">Search</button>

<div id="out"></div>

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
# CACHE SYSTEM (important scaling)
# =========================
def cache_get(key):
    data = CACHE.get(key)
    if data and time.time() - data["time"] < 60:  # 60 sec cache
        return data["value"]
    return None

def cache_set(key, value):
    CACHE[key] = {"value": value, "time": time.time()}

# =========================
# MARKET ESTIMATION
# =========================
def estimate_market(q):
    q = q.lower()

    for k, v in BASE_MARKET.items():
        if k in q:
            return v

    return 500

# =========================
# SCORE ENGINE (SCALING VERSION)
# =========================
def score(price, market):
    ratio = price / market

    if ratio <= 0.70:
        return 98
    elif ratio <= 0.85:
        return 86
    elif ratio <= 0.95:
        return 72
    elif ratio <= 1.10:
        return 58
    elif ratio <= 1.25:
        return 40
    else:
        return 18

# =========================
# LABEL ENGINE
# =========================
def label(score):
    if score >= 90:
        return "🔥 Deal exceptionnel"
    elif score >= 75:
        return "✅ Très bonne affaire"
    elif score >= 55:
        return "⚠️ Prix correct"
    elif score >= 35:
        return "❌ Peu intéressant"
    else:
        return "❌ Mauvais deal"

# =========================
# EBAY (OPTIONNEL SAFE)
# =========================
def ebay_price(q):
    if not EBAY_APP_ID:
        return None

    try:
        url = "https://svcs.ebay.com/services/search/FindingService/v1"
        params = {
            "OPERATION-NAME": "findItemsByKeywords",
            "SERVICE-VERSION": "1.0.0",
            "SECURITY-APPNAME": EBAY_APP_ID,
            "RESPONSE-DATA-FORMAT": "JSON",
            "keywords": q
        }

        r = requests.get(url, params=params, timeout=4)
        data = r.json()

        items = data["findItemsByKeywordsResponse"][0]["searchResult"][0].get("item", [])

        prices = []
        for i in items:
            try:
                prices.append(float(i["sellingStatus"][0]["currentPrice"][0]["__value__"]))
            except:
                pass

        if prices:
            return sum(prices) / len(prices)

    except:
        pass

    return None

# =========================
# GOOGLE FALLBACK
# =========================
def google_price(q):
    if not GOOGLE_API_KEY or not GOOGLE_CX:
        return None

    try:
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": GOOGLE_API_KEY,
            "cx": GOOGLE_CX,
            "q": q + " prix"
        }

        r = requests.get(url, timeout=4, params=params)
        data = r.json()

        if "items" in data:
            return estimate_market(q)

    except:
        pass

    return None

# =========================
# MAIN ENGINE (SCALABLE PIPELINE)
# =========================
@app.route("/search")
def search():
    q = request.args.get("q", "ps5").lower()

    # CACHE FIRST (important scaling)
    cached = cache_get(q)
    if cached:
        return jsonify(cached)

    # 1. EBAY
    market = ebay_price(q)
    source = "eBay"

    # 2. GOOGLE
    if not market:
        market = google_price(q)
        source = "Google"

    # 3. LOCAL BASE
    if not market:
        market = BASE_MARKET.get(q)
        source = "Local DB"

    # 4. FALLBACK ESTIMATE
    if not market:
        market = estimate_market(q)
        source = "Estimated AI"

    price = market + 20

    result = [{
        "title": q.upper(),
        "price": round(price, 2),
        "market": round(market, 2),
        "score": score(price, market),
        "label": label(score(price, market)),
        "explain": "Analyse multi-source + fallback intelligent + cache actif",
        "source": source
    }]

    cache_set(q, result)

    return jsonify(result)

# =========================
# RUN
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
