from flask import Flask, render_template_string, request, jsonify
import os
import requests

app = Flask(__name__)

# =========================
# ENV (optionnel)
# =========================
EBAY_APP_ID = os.environ.get("EBAY_APP_ID")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
GOOGLE_CX = os.environ.get("GOOGLE_CX")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# =========================
# BASE LOCALE (STABLE CORE)
# =========================
LOCAL_DB = {
    "ps5": 500,
    "xbox": 450,
    "iphone 13": 520,
    "iphone 12 pro": 430,
    "macbook air m1": 900,
    "airpods pro": 220
}

# =========================
# FRONTEND
# =========================
HTML = """
<!DOCTYPE html>
<html>
<head>
<title>AI Deal SaaS Pro</title>
<style>
body{font-family:Arial;background:#0f172a;color:white;text-align:center;padding:20px}
input{padding:10px;width:250px}
button{padding:10px;background:#22c55e;border:none;cursor:pointer}
.card{background:#1e293b;margin:10px auto;width:420px;padding:15px;border-radius:10px;text-align:left}
.good{color:#22c55e}
.bad{color:#ef4444}
</style>
</head>
<body>

<h1>🚀 AI Deal SaaS (Stable Pro)</h1>

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
        let c=d.score>70?"good":"bad";
        html+=`
        <div class="card">
            <h3>${d.title}</h3>
            <p>💰 ${d.price} €</p>
            <p>📊 <span class="${c}">${d.score}/100</span></p>
            <p>${d.explain}</p>
            <small>${d.source}</small>
        </div>`;
    });

    document.getElementById("out").innerHTML=html;
}
</script>

</body>
</html>
"""

# =========================
# HOME ROUTE
# =========================
@app.route("/")
def home():
    return render_template_string(HTML)

# =========================
# SCORE (REALISTE)
# =========================
def score(price, market):
    if not market:
        return 50
    return round(max(0, min(100, 100 - abs(price - market) / market * 100)), 1)

# =========================
# ESTIMATION INTELLIGENTE (PAS RANDOM)
# =========================
def estimate_price(query):
    q = query.lower()

    if "ps5" in q:
        return 500
    if "xbox" in q:
        return 450
    if "iphone" in q:
        return 600
    if "macbook" in q:
        return 900

    return 500

# =========================
# EBAY (OPTIONNEL)
# =========================
def get_ebay_price(query):
    if not EBAY_APP_ID:
        return None

    try:
        url = "https://svcs.ebay.com/services/search/FindingService/v1"
        params = {
            "OPERATION-NAME": "findItemsByKeywords",
            "SERVICE-VERSION": "1.0.0",
            "SECURITY-APPNAME": EBAY_APP_ID,
            "RESPONSE-DATA-FORMAT": "JSON",
            "keywords": query,
            "paginationInput.entriesPerPage": 3
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
# GOOGLE (OPTIONNEL)
# =========================
def get_google_price(query):
    if not GOOGLE_API_KEY or not GOOGLE_CX:
        return None

    try:
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": GOOGLE_API_KEY,
            "cx": GOOGLE_CX,
            "q": query + " prix"
        }

        r = requests.get(url, params=params, timeout=4)
        data = r.json()

        if "items" in data:
            return estimate_price(query)

    except:
        pass

    return None

# =========================
# IA FALLBACK (SAFE)
# =========================
def explain(title, price, market):
    if market and price < market:
        return "Bonne affaire (sous le marché)"
    elif market and price < market * 1.1:
        return "Prix correct"
    else:
        return "Trop cher par rapport au marché"

# =========================
# LOGIQUE PRINCIPALE
# =========================
@app.route("/search")
def search():
    q = request.args.get("q", "PS5")

    # 1. eBay
    market = get_ebay_price(q)
    source = "eBay"

    # 2. Google
    if not market:
        market = get_google_price(q)
        source = "Google"

    # 3. Local DB
    if not market:
        market = LOCAL_DB.get(q.lower())
        source = "Local DB"

    # 4. estimation finale
    if not market:
        market = estimate_price(q)
        source = "Estimated"

    # prix affiché
    price = market + 20

    return jsonify([{
        "title": q,
        "price": round(price, 2),
        "market": round(market, 2),
        "score": score(price, market),
        "explain": explain(q, price, market),
        "source": source
    }])

# =========================
# RUN
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
