from flask import Flask, render_template_string, request, jsonify, session
import os
import sqlite3
import time
import random

app = Flask(__name__)
app.secret_key = "saas-secret-key"

DB = "saas.db"

# =========================
# INIT DB
# =========================
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        email TEXT PRIMARY KEY,
        requests INTEGER DEFAULT 0
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product TEXT,
        price REAL,
        ts REAL
    )
    """)

    conn.commit()
    conn.close()

init_db()

# =========================
# BASE MARKET
# =========================
BASE = {
    "ps5": 500,
    "xbox": 450,
    "iphone 14": 750,
    "macbook air m1": 900
}

# =========================
# SCORE IA SIMPLE
# =========================
def score(price, market):
    ratio = price / market
    return max(0, min(100, round(100 - ratio * 100 + random.uniform(-2,2),1)))

def label(s):
    if s > 85: return "🔥 Excellente affaire"
    if s > 70: return "✅ Bonne affaire"
    if s > 50: return "⚠️ Prix correct"
    if s > 30: return "❌ Peu intéressant"
    return "❌ Mauvais deal"

# =========================
# UI HOME
# =========================
HOME = """
<!DOCTYPE html>
<html>
<head>
<title>SaaS AI Deal PRO</title>
<style>
body{font-family:Arial;background:#0f172a;color:white;text-align:center;padding:20px}
input{padding:10px;width:250px;border:none;border-radius:6px}
button{padding:10px;background:#22c55e;border:none;border-radius:6px;cursor:pointer}
.card{background:#1e293b;margin:10px auto;width:450px;padding:15px;border-radius:10px;text-align:left}
.good{color:#22c55e}
.mid{color:#facc15}
.bad{color:#ef4444}
a{color:#38bdf8}
</style>
</head>
<body>

<h1>🚀 SaaS AI Deal PRO FULL STACK</h1>

<p>
<a href="/login_page">Login</a> |
<a href="/admin">Admin</a>
</p>

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
        let c=d.score>80?"good":d.score>50?"mid":"bad";

        html+=`
        <div class="card">
            <h3>${d.title}</h3>
            <p>💰 ${d.price} €</p>
            <p>📊 <span class="${c}">${d.score}/100</span></p>
            <p>${d.label}</p>
        </div>`;
    });

    document.getElementById("out").innerHTML=html;
}
</script>

</body>
</html>
"""

# =========================
# LOGIN PAGE
# =========================
LOGIN_PAGE = """
<h2>Login SaaS</h2>
<input id="email" placeholder="email">
<button onclick="login()">Login</button>

<script>
async function login(){
    const email=document.getElementById("email").value;

    await fetch("/login",{method:"POST",
    headers:{"Content-Type":"application/json"},
    body:JSON.stringify({email})});

    window.location="/";
}
</script>
"""

# =========================
# ADMIN PAGE
# =========================
ADMIN_PAGE = """
<h1>Admin Dashboard</h1>

<p>Users: {{users}}</p>
<p>History: {{history}}</p>

<a href="/">Home</a>
"""

# =========================
# HOME ROUTE
# =========================
@app.route("/")
def home():
    return HOME

# =========================
# LOGIN
# =========================
@app.route("/login_page")
def login_page():
    return LOGIN_PAGE

@app.route("/login", methods=["POST"])
def login():
    email = request.json["email"]

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("INSERT OR IGNORE INTO users (email, requests) VALUES (?,0)", (email,))
    conn.commit()
    conn.close()

    session["user"] = email

    return {"status":"ok"}

# =========================
# SEARCH ENGINE
# =========================
@app.route("/search")
def search():
    q = request.args.get("q","ps5").lower()

    market = BASE.get(q, 500)

    price = market + random.randint(-80,120)

    s = score(price, market)

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("INSERT INTO history (product, price, ts) VALUES (?,?,?)",
              (q, price, time.time()))

    conn.commit()
    conn.close()

    return jsonify([{
        "title": q.upper(),
        "price": round(price,2),
        "score": s,
        "label": label(s)
    }])

# =========================
# ADMIN
# =========================
@app.route("/admin")
def admin():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    users = c.execute("SELECT * FROM users").fetchall()
    history = c.execute("SELECT * FROM history ORDER BY id DESC LIMIT 20").fetchall()

    conn.close()

    return render_template_string(ADMIN_PAGE, users=users, history=history)

# =========================
# RUN
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
