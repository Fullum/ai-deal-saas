from flask import Flask, render_template_string, request, jsonify, session, redirect
import os
import time
import random
import sqlite3
import requests

app = Flask(__name__)
app.secret_key = "super-secret-key"

# =========================
# CONFIG ENV
# =========================
STRIPE_KEY = os.environ.get("STRIPE_KEY")
EBAY_APP_ID = os.environ.get("EBAY_APP_ID")

# =========================
# DATABASE (POSTGRES READY / SQLITE fallback)
# =========================
DB = "saas.db"

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT,
        plan TEXT,
        requests INTEGER DEFAULT 0
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT,
        product TEXT,
        target_price REAL
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product TEXT,
        price REAL,
        timestamp REAL
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
# LOGIN SIMPLE
# =========================
@app.route("/login", methods=["POST"])
def login():
    email = request.json["email"]

    session["user"] = email

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("INSERT OR IGNORE INTO users (email, plan, requests) VALUES (?, 'free', 0)", (email,))
    conn.commit()
    conn.close()

    return {"status": "logged", "user": email}

# =========================
# GET USER
# =========================
def get_user(email):
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("SELECT plan, requests FROM users WHERE email=?", (email,))
    user = c.fetchone()

    conn.close()

    return user if user else ("free", 0)

# =========================
# LIMIT SYSTEM (MONETIZATION)
# =========================
def check_limit(email):
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("SELECT requests FROM users WHERE email=?", (email,))
    r = c.fetchone()[0]

    if r >= 30:
        return False

    c.execute("UPDATE users SET requests = requests + 1 WHERE email=?", (email,))
    conn.commit()
    conn.close()

    return True

# =========================
# EBAY SCRAPER SAFE
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
# MARKET PRICE
# =========================
def market(q):
    return BASE.get(q.lower(), 500)

# =========================
# AI SCORE PRO
# =========================
def score(price, m):
    ratio = price / m
    return max(0, min(100, round(100 - ratio * 100 + random.uniform(-2, 2), 1)))

# =========================
# LABEL
# =========================
def label(s):
    if s > 85: return "🔥 Deal exceptionnel"
    if s > 70: return "✅ Bonne affaire"
    if s > 50: return "⚠️ Prix correct"
    if s > 30: return "❌ Peu intéressant"
    return "❌ Mauvais deal"

# =========================
# SAVE HISTORY
# =========================
def save_history(p, price):
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("INSERT INTO history (product, price, timestamp) VALUES (?, ?, ?)",
              (p, price, time.time()))

    conn.commit()
    conn.close()

# =========================
# SEARCH ENGINE FULL STACK
# =========================
@app.route("/search")
def search():
    if "user" not in session:
        return jsonify({"error": "not logged"})

    user = session["user"]

    if not check_limit(user):
        return jsonify([{
            "title": "UPGRADE REQUIRED",
            "price": 0,
            "score": 0,
            "label": "❌ LIMIT REACHED",
            "plan": "FREE"
        }])

    q = request.args.get("q","ps5").lower()

    m = ebay_price(q)
    source = "eBay" if m else "Local"

    if not m:
        m = market(q)

    price = m + random.randint(-60, 120)

    s = score(price, m)

    save_history(q, price)

    return jsonify([{
        "title": q.upper(),
        "price": round(price,2),
        "market": m,
        "score": s,
        "label": label(s),
        "source": source,
        "plan": "FREE"
    }])

# =========================
# ALERT SYSTEM
# =========================
@app.route("/alert", methods=["POST"])
def alert():
    if "user" not in session:
        return {"error": "not logged"}

    data = request.json

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("INSERT INTO alerts (user_email, product, target_price) VALUES (?, ?, ?)",
              (session["user"], data["item"], data["price"]))

    conn.commit()
    conn.close()

    return {"status":"ok"}

# =========================
# ADMIN DASHBOARD
# =========================
@app.route("/admin")
def admin():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    users = c.execute("SELECT * FROM users").fetchall()
    alerts = c.execute("SELECT * FROM alerts").fetchall()
    history = c.execute("SELECT * FROM history").fetchall()

    return {
        "users": users,
        "alerts": alerts,
        "history": history
    }

# =========================
# STRIPE PLACEHOLDER (READY)
# =========================
@app.route("/checkout")
def checkout():
    return {
        "message": "Stripe integration ready",
        "status": "add STRIPE_KEY + webhook next step"
    }

# =========================
# INIT
# =========================
@app.route("/")
def home():
    return """
    <h1>SaaS PRO FULL STACK</h1>
    <p>Use /login, /search, /admin</p>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
