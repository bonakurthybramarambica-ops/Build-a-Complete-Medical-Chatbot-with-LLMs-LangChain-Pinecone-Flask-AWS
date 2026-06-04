from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
import requests

# -----------------------
# LOAD ENV
# -----------------------
load_dotenv()

app = Flask(__name__)
CORS(app)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# -----------------------
# FALLBACK MEDICAL RULES
# -----------------------
MEDICAL_RESPONSES = {
    "headache": "For headaches: Drink water, rest in a dark room, and consider OTC pain relief. If severe or persistent, consult a doctor.",
    "fever": "For fever: Monitor temperature, stay hydrated, and rest. If above 103°F (39.4°C) or lasting more than 3 days, seek medical care.",
    "cough": "For cough: Drink warm fluids, use honey (if not allergic), and try steam inhalation. If it lasts more than 2 weeks, see a doctor.",
    "dizzy": "For dizziness: Sit or lie down immediately, hydrate, and avoid sudden movements. Seek emergency care if accompanied by chest pain.",
    "stomach": "For stomach pain: Drink clear fluids, rest, and avoid heavy food. If severe or persistent, consult a doctor.",
    "pain": "For pain: Rest the affected area, apply ice or heat, and consider OTC pain relief. If persistent, seek medical advice.",
    "default": "Hello! I am your AI medical assistant. Please describe your symptoms clearly."
}

# -----------------------
# HOME ROUTE
# -----------------------
@app.route("/")
def home():
    return render_template("chat.html")

# -----------------------
# CHAT API ROUTE
# -----------------------
@app.route("/get", methods=["POST"])
def get_response():
    try:
        user_input = request.form.get("msg") or request.json.get("msg", "")

        if not user_input or not user_input.strip():
            return jsonify({"answer": "Please enter a message."}), 400

        user_input = user_input.strip()

        # -----------------------
        # GROQ LLM RESPONSE
        # -----------------------
        if GROQ_API_KEY:
            try:
                response = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {GROQ_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "llama-3.1-8b-instant",
                        "messages": [
                            {
                                "role": "system",
                                "content": (
                                    "You are a helpful medical assistant. "
                                    "Give simple, safe health guidance. "
                                    "Always include a disclaimer: you are not a substitute for professional medical care."
                                )
                            },
                            {
                                "role": "user",
                                "content": user_input
                            }
                        ],
                        "temperature": 0.4
                    },
                    timeout=20
                )

                if response.status_code == 200:
                    data = response.json()
                    answer = data["choices"][0]["message"]["content"]
                    return jsonify({"answer": answer})

                print("Groq Error:", response.text)

            except Exception as e:
                print("Groq Exception:", str(e))

        # -----------------------
        # FALLBACK RULE ENGINE
        # -----------------------
        text = user_input.lower()
        answer = MEDICAL_RESPONSES["default"]

        for keyword, response in MEDICAL_RESPONSES.items():
            if keyword != "default" and keyword in text:
                answer = response
                break

        return jsonify({"answer": answer})

    except Exception as e:
        print("Server Error:", str(e))
        return jsonify({
            "answer": "Something went wrong. Please try again later."
        }), 500

# -----------------------
# HEALTH CHECK (RENDER)
# -----------------------
@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "service": "medical-chatbot",
        "mode": "groq" if GROQ_API_KEY else "fallback"
    })

# -----------------------
# MAIN
# -----------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)