from flask import Flask, request, jsonify, render_template_string, session
import sqlite3
import random
import time
import os

app = Flask(__name__)
app.secret_key = "saas-secret-key"

DB = "saas.db"

# =========================
# INIT DATABASE
# =========================
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        email TEXT PRIMARY KEY,
        created_at REAL
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product TEXT,
        price REAL,
        market REAL,
        score REAL,
        ts REAL
    )
    """)

    conn.commit()
    conn.close()

init_db()

# =========================
# BASE PRIX MARCHE
# =========================
BASE_MARKET = {
    "ps5": 500,
    "xbox": 450,
    "iphone 14": 750,
    "macbook air m1": 900,
    "airpods pro": 220,
    "nintendo switch": 300
}

# =========================
# MARKET ENGINE (SAFE)
# =========================
def get_market(q):
    q = q.lower()
    base = BASE_MARKET.get(q)

    if base:
        return base * random.uniform(0.85, 1.15)

    return 500 + random.uniform(-120, 180)

# =========================
# SCORE FIX (TON LOGIC CORRIGÉE)
# =========================
def score(price, market):
    low = market * 0.8
    high = market * 1.2

    if price < low:
        return 90 + random.uniform(0, 5)

    if price > high:
        return max(10, 100 - ((price - high) / market) * 100)

    return 60 + random.uniform(-10, 10)

# =========================
# LABEL
# =========================
def label(s):
    if s > 85:
        return "🔥 Excellente affaire"
    if s > 70:
        return "✅ Bonne affaire"
    if s > 50:
        return "⚠️ Prix correct"
    if s > 20:
        return "❌ Trop cher"
    return "❌ Mauvais deal"

# =========================
# SAVE HISTORY
# =========================
def save_history(p, price, market, score_val):
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
        INSERT INTO history (product, price, market, score, ts)
        VALUES (?,?,?,?,?)
    """, (p, price, market, score_val, time.time()))

    conn.commit()
    conn.close()

# =========================
# LOGIN SIMPLE
# =========================
@app.route("/login", methods=["POST"])
def login():
    email = request.json.get("email")

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("INSERT OR IGNORE INTO users (email, created_at) VALUES (?,?)",
              (email, time.time()))

    conn.commit()
    conn.close()

    session["user"] = email

    return {"status": "logged"}

# =========================
# SEARCH API
# =========================
@app.route("/search")
def search():
    q = request.args.get("q", "ps5").lower()

    market = get_market(q)
    price = market * random.uniform(0.75, 1.35)

    s = score(price, market)

    save_history(q, price, market, s)

    return jsonify([{
        "title": q.upper(),
        "price": round(price, 2),
        "market": round(market, 2),
        "score": round(s, 1),
        "label": label(s)
    }])

# =========================
# ADMIN DASHBOARD
# =========================
@app.route("/admin")
def admin():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    users = c.execute("SELECT * FROM users").fetchall()
    history = c.execute("SELECT * FROM history ORDER BY id DESC LIMIT 20").fetchall()

    conn.close()

    return {
        "users": users,
        "history": history
    }

# =========================
# FRONTEND UI
# =========================
HOME = """
<!DOCTYPE html>
<html>
<head>
<title>SaaS IA DEAL PRO</title>
<style>
body{font-family:Arial;background:#0f172a;color:white;text-align:center;padding:20px}
input{padding:10px;width:260px;border-radius:8px;border:none}
button{padding:10px;border:none;background:#22c55e;color:white;border-radius:8px;cursor:pointer}
.card{background:#1e293b;margin:10px auto;width:420px;padding:15px;border-radius:12px;text-align:left}
.good{color:#22c55e}
.mid{color:#facc15}
.bad{color:#ef4444}
a{color:#38bdf8}
</style>
</head>
<body>

<h1>🚀 SaaS IA DEAL PRO FULL STACK</h1>

<p>
<a href="#" onclick="login()">Login test</a> |
<a href="/admin">Admin</a>
</p>

<input id="q" placeholder="ex: PS5">
<button onclick="search()">Search</button>

<div id="out"></div>

<script>
async function login(){
    await fetch("/login",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({email:"test@test.com"})
    });
    alert("Logged in");
}

async function search(){
    const q=document.getElementById("q").value;

    const res=await fetch("/search?q="+q);
    const data=await res.json();

    let html="";

    data.forEach(d=>{
        let c = d.score>80 ? "good" : d.score>50 ? "mid" : "bad";

        html+=`
        <div class="card">
            <h3>${d.title}</h3>
            <p>💰 ${d.price} €</p>
            <p>📊 <span class="${c}">${d.score}/100</span></p>
            <p>${d.label}</p>
            <p>📉 Market: ${d.market} €</p>
        </div>`;
    });

    document.getElementById("out").innerHTML=html;
}
</script>

</body>
</html>
"""

@app.route("/")
def home():
    return HOME

# =========================
# RUN
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
