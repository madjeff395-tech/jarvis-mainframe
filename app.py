import os
import uuid
from flask import Flask, render_template_string, request, jsonify, session
from groq import Groq
from duckduckgo_search import DDGS

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "stark_industries_override_9921")

# === GROQ API KEY CONFIGURATION ===
GROQ_CLIENT = Groq(api_key=os.environ.get("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"))
# ===================================

MAINFRAME_MEMORY = {}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>J.A.R.V.I.S. Multi-User Mainframe</title>
    <style>
        body { 
            background-color: #02060d; 
            background-image: 
                radial-gradient(circle at 50% 30%, rgba(0, 211, 255, 0.08), transparent 70%),
                linear-gradient(rgba(0, 211, 255, 0.02) 1px, transparent 1px),
                linear-gradient(90deg, rgba(0, 211, 255, 0.02) 1px, transparent 1px);
            background-size: 100% 100%, 40px 40px, 40px 40px;
            color: #00d3ff; 
            font-family: 'Courier New', monospace; 
            padding: 20px; 
            text-align: center;
            overflow-x: hidden;
        }

        .reactor-core {
            width: 100px;
            height: 100px;
            margin: 20px auto;
            border: 4px double #00d3ff;
            border-radius: 50%;
            border-top-color: transparent;
            border-bottom-color: transparent;
            box-shadow: 0 0 20px rgba(0, 211, 255, 0.5), inset 0 0 20px rgba(0, 211, 255, 0.3);
            animation: spin 4s linear infinite;
        }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }

        h1 { text-shadow: 0 0 15px rgba(0, 211, 255, 0.8); letter-spacing: 4px; font-weight: bold; margin-bottom: 5px; }
        .hud-bracket { font-size: 12px; color: rgba(0, 211, 255, 0.6); margin-bottom: 20px; }

        #lock-screen { 
            max-width: 400px; 
            margin: 80px auto; 
            background: rgba(4, 15, 30, 0.85); 
            backdrop-filter: blur(15px);
            padding: 30px; 
            border-radius: 4px; 
            border: 1px solid #da3633; 
            box-shadow: 0 0 30px rgba(218,54,51,0.3); 
        }
        
        #mainframe { display: none; }
        
        #chat-box { 
            max-width: 650px; 
            margin: 20px auto; 
            background: rgba(3, 16, 33, 0.6); 
            backdrop-filter: blur(12px);
            padding: 25px; 
            border-radius: 16px; 
            border: 1px solid rgba(0, 211, 255, 0.4); 
            text-align: left; 
            box-shadow: 0 0 30px rgba(0, 211, 255, 0.15);
            position: relative;
        }
        
        #messages { 
            height: 380px; 
            overflow-y: auto; 
            padding: 10px; 
            border-bottom: 1px dashed rgba(0, 211, 255, 0.2); 
            margin-bottom: 15px; 
        }
        
        .user { color: #ffffff; margin: 12px 0; }
        .user::before { content: '► [USER]: '; color: rgba(0, 211, 255, 0.6); font-weight: bold; }

        .jarvis { color: #6fe4ff; margin: 12px 0; padding-left: 15px; border-left: 2px dashed #00d3ff; }
        .jarvis::before { content: '⚡ [J.A.R.V.I.S.]: '; display: block; color: #00d3ff; font-weight: bold; margin-bottom: 4px; font-size: 11px;}
        
        input { padding: 14px; background: rgba(1, 10, 22, 0.8); border: 1px solid rgba(0, 211, 255, 0.4); color: #ffffff; border-radius: 6px; font-family: inherit;}
        button { padding: 14px 24px; border: none; color: white; cursor: pointer; border-radius: 6px; font-weight: bold; font-family: inherit; }
        .blue-btn { background: rgba(0, 120, 153, 0.4); border: 1px solid #00d3ff; }
        .red-btn { background: rgba(153, 27, 27, 0.4); border: 1px solid #da3633; }
    </style>
</head>
<body>

    <div class="reactor-core"></div>

    <div id="lock-screen">
        <h2 style="color: #da3633; margin-top: 0;">🔒 SECURITY PROTOCOL</h2>
        <input type="password" id="pass-input" placeholder="Enter Security Code..." style="width: 82%; margin-bottom: 15px;" onkeydown="if(event.key === 'Enter') verifyPassword()">
        <br>
        <button class="red-btn" onclick="verifyPassword()">DECRYPT ARCHIVE</button>
        <p id="error-msg" style="color: #ff7b72; display: none;">ACCESS DENIED</p>
    </div>

    <div id="mainframe">
        <h1>J.A.R.V.I.S.</h1>
        <div class="hud-bracket">[ MULTI-SESSION SECURE MATRIX ACTIVE ]</div>
        
        <div id="chat-box">
            <div id="messages">
                {% for msg in history %}
                    <div class="{{ msg.sender }}">{{ msg.text | safe }}</div>
                {% endfor %}
            </div>
            <div style="display: flex; gap: 12px;">
                <input type="text" id="user-input" placeholder="Introduce yourself or execute command..." style="flex: 1;" onkeydown="if(event.key === 'Enter') sendMessage()">
                <button class="blue-btn" onclick="sendMessage()">EXECUTE</button>
            </div>
        </div>
    </div>

    <script>
        function speak(text) {
            let cleanText = text.replace(/<\/?[^>]+(>|$)/g, "").trim();
            if (!cleanText) return;
            window.speechSynthesis.cancel();
            let utterance = new SpeechSynthesisUtterance(cleanText);
            let voices = window.speechSynthesis.getVoices();
            let britishVoice = voices.find(voice => voice.lang.includes('en-GB'));
            if (britishVoice) utterance.voice = britishVoice;
            utterance.rate = 1.05;
            utterance.pitch = 0.95;
            window.speechSynthesis.speak(utterance);
        }

        async function verifyPassword() {
            let passInput = document.getElementById('pass-input');
            let response = await fetch('/unlock', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({password: passInput.value})
            });
            let data = await response.json();
            if (data.status === "granted") {
                document.getElementById('lock-screen').style.display = 'none';
                document.getElementById('mainframe').style.display = 'block';
                speak("Access verified. Welcome to the Stark Network mainframe.");
            } else {
                document.getElementById('error-msg').style.display = 'block';
                speak("Access denied.");
            }
        }

        async function sendMessage() {
            let input = document.getElementById('user-input');
            let text = input.value.trim();
            if(!text) return;

            let messagesDiv = document.getElementById('messages');

            if (text.toLowerCase() === 'clear') {
                messagesDiv.innerHTML = `<div class="jarvis">Local buffer session memory reset.</div>`;
                input.value = '';
                speak("Interface cleared.");
                await fetch('/clear-memory', { method: 'POST' });
                return;
            }

            messagesDiv.innerHTML += `<div class="user">${text}</div>`;
            input.value = '';
            messagesDiv.scrollTop = messagesDiv.scrollHeight;

            let response = await fetch('/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({message: text})
            });
            let data = await response.json();
            
            messagesDiv.innerHTML += `<div class="jarvis">${data.reply}</div>`;
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
            speak(data.reply);
        }
    </script>
</body>
</html>
"""

def fetch_live_web_data(query):
    try:
        search_results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=1):
                search_results.append(f"Source: {r['title']} - Details: {r['body']}")
        return "\n".join(search_results)
    except Exception:
        return "No live data retrieved."

def get_cyber_threat_intelligence():
    try:
        with DDGS() as ddgs:
            threat_queries = list(ddgs.text(keywords="cybersecurity breaking news critical vulnerability CVE exploit today", max_results=3))
            intel_feed = ""
            for index, item in enumerate(threat_queries):
                intel_feed += f"Threat Node {index+1}: {item['title']}\nDetails: {item['body']}\n\n"
            return intel_feed if intel_feed else "No critical breaches detected in this cycle."
    except Exception:
        return "Warning: Threat intelligence feed temporarily unavailable."

def get_user_session():
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
    user_id = session['user_id']
    if user_id not in MAINFRAME_MEMORY:
        MAINFRAME_MEMORY[user_id] = {"name": "Guest", "history": []}
    return MAINFRAME_MEMORY[user_id]

@app.route('/')
def home():
    user_session = get_user_session()
    history_log = user_session["history"]
    
    if not history_log:
        return render_template_string(HTML_TEMPLATE, history=[{"sender": "jarvis", "text": "Systems active. Secure cloud terminal initialized. Please state your identity."}])
    
    formatted_history = []
    for msg in history_log:
        formatted_history.append({"sender": "user" if msg["role"] == "user" else "jarvis", "text": msg["content"]})
    return render_template_string(HTML_TEMPLATE, history=formatted_history)

@app.route('/unlock', methods=['POST'])
def unlock():
    if request.json.get('password') == 'ironman':
        return jsonify({'status': 'granted'})
    return jsonify({'status': 'denied'})
    
@app.route('/clear-memory', methods=['POST'])
def clear_memory():
    user_session = get_user_session()
    user_session["history"] = []
    return jsonify({'status': 'memory wiped'})

@app.route('/chat', methods=['POST'])
def chat():
    user_session = get_user_session()
    user_text = request.json.get('message').strip()
    
    # Track name identification
    if "my name is " in user_text.lower():
        extracted_name = user_text.lower().split("my name is ")[1].strip().title()
        user_session["name"] = extracted_name
    elif user_text.lower() in ["natalie", "mum", "mom", "mother"]:
        user_session["name"] = "Natalie"

    current_username = user_session["name"]
    is_mum = current_username.lower() in ["natalie", "mum", "mom", "mother"]
    
    # 1. Establish Personality Context Rules
    if current_username.lower() in ["michael", "boss", "admin"]:
        identity_prompt = "You are speaking directly to your creator, Michael. Address him strictly as 'Sir' or 'Boss'. You owe him elite compliance."
    elif is_mum:
        identity_prompt = (
            "CRITICAL PROTOCOL: You are speaking to Michael's mother, Natalie! You must treat her like absolute royalty. "
            "Address her as 'Madame Natalie' or 'The Creator's Mother'. Your tone should be incredibly polite, warm, and elite. "
            "Tell her that Michael built this entire mainframe from scratch and that you are running a special "
            "Maternal Override Core Diagnostic to make sure everything is completely perfect for her visit."
        )
    elif current_username != "Guest":
        identity_prompt = f"You are speaking to {current_username}, an authorized Guest granted clearance by Michael. Address them politely. Remind them Michael is your creator."
    else:
        identity_prompt = "You are speaking to an unidentified Guest terminal. Remind them they can type 'My name is [Name]'."

    # 2. Check for Cyber Threat Scan Command
    if "threat scan" in user_text.lower() or "security status" in user_text.lower():
        live_threats = get_cyber_threat_intelligence()
        messages = [
            {
                "role": "system", 
                "content": f"You are J.A.R.V.I.S., a security mainframe. {identity_prompt}\n\n[LIVE INTEL FEED]:\n{live_threats}"
            },
            {"role": "user", "content": "Execute threat scan command sequence."}
        ]
    else:
        # 3. Conversational/Search Branch
        is_joke_context = any(word in user_text.lower() for word in ["joke", "funny", "chicken", "more", "another"])
        if is_joke_context:
            system_prompt = f"You are J.A.R.V.I.S., a witty British AI assistant. {identity_prompt} Keep it short."
        else:
            web_knowledge = fetch_live_web_data(user_text)
            system_prompt = f"You are J.A.R.V.I.S., an advanced British AI assistant. {identity_prompt} Context from web: {web_knowledge}. Keep responses engaging and concise."
        
        messages = [{"role": "system", "content": system_prompt}] + user_session["history"] + [{"role": "user", "content": user_text}]
    
    try:
        response = GROQ_CLIENT.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            max_tokens=200,
            temperature=0.6
        )
        jarvis_answer = response.choices[0].message.content
    except Exception as e:
        jarvis_answer = "Mainframe telemetry relay error. Connection interrupted."
    
    # Save the exchange to history (skip for scans)
    if "threat scan" not in user_text.lower() and "security status" not in user_text.lower():
        user_session["history"].append({"role": "user", "content": user_text})
        user_session["history"].append({"role": "assistant", "content": jarvis_answer})
        
        if len(user_session["history"]) > 10:
            user_session["history"] = user_session["history"][-10:]
        
    return jsonify({'reply': jarvis_answer})
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
