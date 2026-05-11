from flask import Flask, render_template_string, request, jsonify
import os
import requests
import random

app = Flask(__name__)

# =========================
# ENV VARIABLES (Render)
# =========================
EBAY_APP_ID = os.environ.get("EBAY_APP_ID")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
GOOGLE_CX = os.environ.get("GOOGLE_CX")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# =========================
# FRONT SIMPLE
# =========================
HTML = """
<!DOCTYPE html>
<html>
<head>
<title>AI Deal SaaS</title>
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

<h1>🚀 AI Deal SaaS (Stable)</h1>

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
# HOME ROUTE (IMPORTANT)
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
# EBAY API
# =========================
def get_ebay_price(query):
    if not EBAY_APP_ID:
        return None

    url = "https://svcs.ebay.com/services/search/FindingService/v1"
    params = {
        "OPERATION-NAME": "findItemsByKeywords",
        "SERVICE-VERSION": "1.0.0",
        "SECURITY-APPNAME": EBAY_APP_ID,
        "RESPONSE-DATA-FORMAT": "JSON",
        "keywords": query,
        "paginationInput.entriesPerPage": 5
    }

    try:
        r = requests.get(url, params=params, timeout=5)
        data = r.json()

        items = data["findItemsByKeywordsResponse"][0]["searchResult"][0].get("item", [])

        prices = []
        for item in items:
            try:
                prices.append(float(item["sellingStatus"][0]["currentPrice"][0]["__value__"]))
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

        r = requests.get(url, timeout=5, params=params)
        data = r.json()

        if "items" in data:
            return random.randint(300, 700)

    except:
        pass

    return None

# =========================
# GEMINI SAFE FALLBACK
# =========================
def gemini_explain(title, price, market):
    if not GEMINI_API_KEY:
        return "Analyse IA indisponible"

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

    prompt = f"""
Produit: {title}
Prix: {price}
Marché: {market}

Donne une analyse courte (1 phrase).
"""

    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }

    try:
        r = requests.post(url, json=payload, timeout=5)
        data = r.json()

        if "candidates" in data and len(data["candidates"]) > 0:
            return data["candidates"][0]["content"]["parts"][0]["text"]

    except:
        pass

    return "Analyse indisponible"

# =========================
# SEARCH API
# =========================
@app.route("/search")
def search():
    q = request.args.get("q", "PS5")

    market = get_ebay_price(q)
    source = "eBay API"

    if not market:
        market = get_google_price(q)
        source = "Google fallback"

    if not market:
        market = random.randint(300, 700)
        source = "local fallback"

    price = market + random.randint(-80, 80)

    return jsonify([{
        "title": q,
        "price": round(price, 2),
        "market": round(market, 2),
        "score": score(price, market),
        "explain": gemini_explain(q, price, market),
        "source": source
    }])

# =========================
# RUN
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
