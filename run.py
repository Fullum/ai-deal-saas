from flask import Flask, render_template_string, request, jsonify
import random
import os

app = Flask(__name__)

# -----------------------------
# BASE DE DONNÉES SIMULÉE
# -----------------------------
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

def generate_ads():
    return [
        {
            "title": name,
            "price": market + random.randint(-150, 150),
            "market": market
        }
        for name, market in MARKET_DB.items()
    ]

def score(price, market):
    return max(0, min(100, round(50 + ((market - price) / market) * 120, 1)))

def explain(price, market):
    if price < market * 0.85:
        return "🔥 Très bonne affaire"
    elif price < market:
        return "👍 Bon prix"
    return "⚠️ Trop cher"


# -----------------------------
# FRONTEND HTML
# -----------------------------
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
<h1>🚀 AI Deal SaaS</h1>
<input id="q" placeholder="ex: iPhone">
<button onclick="search()">Search</button>
<div id="out"></div>

<script>
async function search(){
    const q=document.getElementById("q").value;
    const res=await fetch("/search?q="+q);
    const data=await res.json();

    let html="";
    data.forEach(d=>{
        let c=d.score>75?"good":"bad";
        html+=`
        <div class="card">
            <h3>${d.title}</h3>
            <p>💰 ${d.price} €</p>
            <p>📊 <span class="${c}">${d.score}/100</span></p>
            <p>${d.explain}</p>
        </div>`;
    });

    document.getElementById("out").innerHTML=html;
}
</script>
</body>
</html>
"""


# -----------------------------
# ROUTES FLASK
# -----------------------------
@app.route("/")
def home():
    return render_template_string(HTML)

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
            "explain": explain(a["price"], a["market"])
        })

    return jsonify(sorted(results, key=lambda x: x["score"], reverse=True))


# -----------------------------
# RENDER CONFIG (IMPORTANT)
# -----------------------------
port = int(os.environ.get("PORT", 10000))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=port)
