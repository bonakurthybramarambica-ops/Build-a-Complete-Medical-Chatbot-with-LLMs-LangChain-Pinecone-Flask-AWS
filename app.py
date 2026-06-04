from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
import requests

load_dotenv()

app = Flask(__name__)
CORS(app)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

MEDICAL_RESPONSES = {
    "headache": "For headaches: 1) Drink water, 2) Rest in dark room, 3) Consider OTC pain relievers. If severe, see a doctor.",
    "fever": "For fever: 1) Monitor temperature, 2) Stay hydrated, 3) Rest. If >103°F or >3 days, see doctor.",
    "cough": "For cough: 1) Warm fluids, 2) Honey (if not allergic), 3) Humidifier. If >2 weeks, see doctor.",
    "dizzy": "For dizziness: 1) Sit/lie down, 2) Drink water, 3) Avoid sudden movements. If chest pain, emergency.",
    "stomach": "For stomach pain: 1) Clear fluids, 2) Warm compress, 3) Avoid solid foods. If severe, see doctor.",
    "pain": "For pain: Rest, apply ice/heat, consider OTC pain relievers. If persistent, consult a doctor.",
    "default": "Hello! I am your AI medical assistant. Please describe your symptoms or ask a health question."
}

@app.route("/")
def home():
    return render_template("chat.html")

@app.route("/get", methods=["POST"])
def get_response():
    try:
        user_input = request.form.get("msg") or request.json.get("msg", "")
        
        if not user_input or not user_input.strip():
            return jsonify({"answer": "Please enter a message"}), 400
        
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
                            {"role": "system", "content": "You are a helpful medical assistant. Provide clear, simple medical advice. Always include a disclaimer that you are not a substitute for professional medical care."},
                            {"role": "user", "content": user_input}
                        ],
                        "temperature": 0.4
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    answer = data["choices"][0]["message"]["content"]
                    return jsonify({"answer": answer})
            except Exception as e:
                print(f"Groq API error: {e}")
        
        user_lower = user_input.lower()
        answer = MEDICAL_RESPONSES["default"]
        
        for keyword, response in MEDICAL_RESPONSES.items():
            if keyword != "default" and keyword in user_lower:
                answer = response
                break
        
        return jsonify({"answer": answer})
        
    except Exception as e:
        return jsonify({"answer": f"Error: {str(e)}"}), 500

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok", "mode": "groq" if GROQ_API_KEY else "demo"})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080)