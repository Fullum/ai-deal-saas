def explain(price, market, title):

    if not GEMINI_API_KEY:
        return "Clé Gemini manquante"

    prompt = f"""
Produit: {title}
Prix: {price}€
Marché: {market}€

Analyse en 2 phrases max.
"""

    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

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

        # 🔥 DEBUG 1 : erreur API
        if "error" in data:
            return f"Erreur Gemini: {data['error']['message']}"

        # 🔥 DEBUG 2 : format inattendu
        if "candidates" not in data:
            return f"Réponse inconnue: {data}"

        # 🔥 OK
        return data["candidates"][0]["content"]["parts"][0]["text"]

    except Exception as e:
        return f"Erreur IA: {str(e)}"
