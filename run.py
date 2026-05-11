def explain(price, market, title):

    if not GEMINI_API_KEY:
        return fallback(price, market)

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

    prompt = f"""
Produit: {title}
Prix: {price}€
Marché: {market}€

Dis si c'est une bonne affaire en 1-2 phrases.
"""

    payload = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ]
    }

    try:
        r = requests.post(url, json=payload, timeout=10)
        data = r.json()

        # 🔥 DEBUG IMPORTANT
        if "error" in data:
            return fallback(price, market)

        if "candidates" not in data:
            return fallback(price, market)

        return data["candidates"][0]["content"]["parts"][0]["text"]

    except Exception as e:
        print("GEMINI ERROR:", e)
        return fallback(price, market)
