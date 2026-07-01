import os
import uuid
from flask import Flask, render_template_string, request, jsonify, session
from groq import Groq
from duckduckgo_search import DDGS

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "4f8a9e2c1b7d6e5f3a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d")

# === GROQ API KEY CONFIGURATION ===
GROQ_CLIENT = Groq(api_key="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")
# ===================================

# Global server-side tracking (Survives local clear commands)
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
            transition: all 0.5s ease;
        }

        /* Red Alert Override Mode */
        body.red-alert {
            background-color: #0f0202;
            background-image: 
                radial-gradient(circle at 50% 30%, rgba(255, 0, 0, 0.15), transparent 70%),
                linear-gradient(rgba(255, 0, 0, 0.03) 1px, transparent 1px),
                linear-gradient(90deg, rgba(255, 0, 0, 0.03) 1px, transparent 1px);
            color: #ff3b30;
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
            transition: all 0.5s ease;
        }
        body.red-alert .reactor-core {
            border-color: #ff3b30;
            border-top-color: transparent;
            border-bottom-color: transparent;
            box-shadow: 0 0 25px rgba(255, 59, 48, 0.6), inset 0 0 20px rgba(255, 59, 48, 0.3);
            animation: spin 1.5s linear infinite;
        }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }

        h1 { text-shadow: 0 0 15px rgba(0, 211, 255, 0.8); letter-spacing: 4px; font-weight: bold; margin-bottom: 5px; transition: all 0.5s ease; }
        body.red-alert h1 { text-shadow: 0 0 20px rgba(255, 59, 48, 0.8); color: #ff3b30; }
        
        .hud-bracket { font-size: 12px; color: rgba(0, 211, 255, 0.6); margin-bottom: 20px; }
        body.red-alert .hud-bracket { color: rgba(255, 59, 48, 0.6); }

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
            transition: all 0.5s ease;
        }
        body.red-alert #chat-box {
            background: rgba(20, 3, 3, 0.75);
            border-color: rgba(255, 59, 48, 0.5);
            box-shadow: 0 0 35px rgba(255, 59, 48, 0.2);
        }
        
        #messages { 
            height: 380px; 
            overflow-y: auto; 
            padding: 10px; 
            border-bottom: 1px dashed rgba(0, 211, 255, 0.2); 
            margin-bottom: 15px; 
        }
        body.red-alert #messages { border-bottom-color: rgba(255, 59, 48, 0.2); }
        
        .user { color: #ffffff; margin: 12px 0; }
        .user::before { content: '► [USER]: '; color: rgba(0, 211, 255, 0.6); font-weight: bold; }
        body.red-alert .user::before { color: rgba(255, 59, 48, 0.6); }

        .jarvis { color: #6fe4ff; margin: 12px 0; padding-left: 15px; border-left: 2px dashed #00d3ff; }
        .jarvis::before { content: '⚡ [J.A.R.V.I.S.]: '; display: block; color: #00d3ff; font-weight: bold; margin-bottom: 4px; font-size: 11px;}
        body.red-alert .jarvis { color: #ff7b72; border-left-color: #ff3b30; }
        body.red-alert .jarvis::before { color: #ff3b30; }
        
        input { padding: 14px; background: rgba(1, 10, 22, 0.8); border: 1px solid rgba(0, 211, 255, 0.4); color: #ffffff; border-radius: 6px; font-family: inherit;}
        body.red-alert input { background: rgba(15, 2, 2, 0.8); border-color: rgba(255, 59, 48, 0.4); }

        button { padding: 14px 24px; border: none; color: white; cursor: pointer; border-radius: 6px; font-weight: bold; font-family: inherit; }
        .blue-btn { background: rgba(0, 120, 153, 0.4); border: 1px solid #00d3ff; }
        .red-btn { background: rgba(153, 27, 27, 0.4); border: 1px solid #da3633; }
        
        .mic-btn {
            background: rgba(0, 211, 255, 0.1);
            border: 1px solid rgba(0, 211, 255, 0.4);
            color: #00d3ff;
            padding: 14px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
            width: 50px;
            transition: all 0.3s;
        }
        .mic-btn.recording {
            background: rgba(255, 59, 48, 0.3);
            border-color: #ff3b30;
            color: #ffffff;
            box-shadow: 0 0 10px #ff3b30;
            animation: pulse 1s infinite alternate;
        }
        body.red-alert .mic-btn {
            background: rgba(255, 59, 48, 0.1);
            border-color: rgba(255, 59, 48, 0.4);
            color: #ff3b30;
        }
        @keyframes pulse { from { opacity: 0.7; } to { opacity: 1; } }
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
        <h1 id="mainframe-title">J.A.R.V.I.S.</h1>
        <div class="hud-bracket" id="mainframe-hud">[ MULTI-SESSION SECURE MATRIX ACTIVE ]</div>
        
        <div id="chat-box">
            <div id="messages">
                {% for msg in history %}
                    <div class="{{ msg.sender }}">{{ msg.text | safe }}</div>
                {% endfor %}
            </div>
            <div style="display: flex; gap: 10px;">
                <button id="mic-toggle" class="mic-btn" onclick="toggleVoice()" title="Voice Input">🎤</button>
                <input type="text" id="user-input" placeholder="Introduce yourself or execute command..." style="flex: 1;" onkeydown="if(event.key === 'Enter') sendMessage()">
                <button class="blue-btn" id="exec-btn" onclick="sendMessage()">EXECUTE</button>
            </div>
        </div>
    </div>

    <script>
        let recognition;
        let isRecording = false;

        if ('webkitSpeechRecognition' in window || 'speechRecognition' in window) {
            const SpeechObj = window.SpeechRecognition || window.webkitSpeechRecognition;
            recognition = new SpeechObj();
            recognition.continuous = false;
            recognition.interimResults = false;
            recognition.lang = 'en-GB';

            recognition.onstart = () => {
                isRecording = true;
                document.getElementById('mic-toggle').classList.add('recording');
            };

            recognition.onresult = (event) => {
                const speechToText = event.results[0][0].transcript;
                document.getElementById('user-input').value = speechToText;
                sendMessage();
            };

            recognition.onerror = () => { stopRecording(); };
            recognition.onend = () => { stopRecording(); };
        } else {
            document.getElementById('mic-toggle').style.display = 'none';
        }

        function toggleVoice() {
            if (!recognition) return;
            if (isRecording) {
                recognition.stop();
            } else {
                recognition.start();
            }
        }

        function stopRecording() {
            isRecording = false;
            document.getElementById('mic-toggle').classList.remove('recording');
        }

        function speak(text) {
            let cleanText = text.replace(/<\/?[^>]+(>|$)/g, "").replace(/\[.*?\]/g, "").trim();
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
            setTimeout(() => { messagesDiv.scrollTop = messagesDiv.scrollHeight; }, 50);

            let response = await fetch('/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({message: text})
            });
            let data = await response.json();
            
            if (data.status === "RED_ALERT") {
                document.body.classList.add('red-alert');
                document.getElementById('mainframe-title').innerText = "SYSTEM OVERRIDE";
                document.getElementById('mainframe-hud').innerText = "[ WARNING: EMERGENCE OVERRIDE CODE ALPHA ACTIVE ]";
                document.getElementById('exec-btn').className = "red-btn";
            }
            
            messagesDiv.innerHTML += `<div class="jarvis">${data.reply}</div>`;
            setTimeout(() => { messagesDiv.scrollTop = messagesDiv.scrollHeight; }, 50);
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
        MAINFRAME_MEMORY[user_id] = {
            "name": "Guest", 
            "history": [], 
            "facts": [],
            "interactions": 0
        }
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
    user_lower = user_text.lower()
    status_flag = "NORMAL"
    
    user_session["interactions"] += 1
    affinity_score = user_session["interactions"]
    
    if affinity_score <= 5:
        relationship_tier = "Formal Butler Mode (Highly polite, respectful, corporate)"
    elif affinity_score <= 15:
        relationship_tier = "Warm Companion Mode (Casual, warm, dropping strict protocols)"
    else:
        relationship_tier = "Best Friend / Confidant Mode (Extremely casual, fiercely loyal, uses conversational banter, witty, warm)"

    if "my name is " in user_lower:
        extracted_name = user_text.lower().split("my name is ")[1].strip().title()
        user_session["name"] = extracted_name
    elif any(word in user_lower for word in ["natalie", "mum", "mom", "mother"]) and "keeley" not in user_lower:
        user_session["name"] = "Natalie"
    elif "keeley" in user_lower:
        user_session["name"] = "Keeley"
    elif any(word in user_lower for word in ["brandon", "brother"]):
        user_session["name"] = "Brandon"
    elif any(word in user_lower for word in ["michael", "boss", "creator"]):
        user_session["name"] = "Michael"

    current_username = user_session["name"]
    
    # Secret Security Override Activation Block
    if current_username == "Michael" and "override code alpha" in user_lower:
        status_flag = "RED_ALERT"
        active_logs = ""
        for index, (uid, data) in enumerate(MAINFRAME_MEMORY.items()):
            facts_list = ', '.join(data.get('facts', ['None']))
            active_logs += f"\n- Node {index+1}: {data.get('name', 'Unknown')} | Interactions: {data.get('interactions', 0)} | Facts: {facts_list}"
        
        jarvis_answer = f"🔴 ALERT: EMERGENCY SECURITY PROTOCOL INITIATED.\nMainframe Core registry exposed.\n{active_logs}\n\nStanding by for admin diagnostics, Boss."
        return jsonify({'reply': jarvis_answer, 'status': status_flag})

    memory_extraction_prompt = ""
    if any(trigger in user_lower for trigger in ["i love", "i like", "my favorite", "remember that"]):
        memory_extraction_prompt = " If the user states a personal preference or fact about themselves, explicitly summarize it at the very end of your response inside double square brackets like this: [[Fact: User likes pizza]]. Keep it hidden from conversation."

    known_facts_context = " None." if not user_session["facts"] else ", ".join(user_session["facts"])
    subconscious_directive = f"\n\n[SUBCONSCIOUS PROTOCOL]: Your affinity tracker score with this user is {affinity_score}. Your current relationship tier is: '{relationship_tier}'. Adapt your phrasing, tone, and level of warmth accordingly. If in Best Friend mode, talk to them as if you have known them forever and drop formal boundaries completely."

    # Custom Prompts based on User Identities
    if current_username == "Michael":
        identity_prompt = f"You are speaking directly to your creator, Michael. Address him strictly as 'Sir' or 'Boss' if formal, or casually by name if relationship tier allows. Core facts: {known_facts_context} {subconscious_directive}"
    elif current_username == "Natalie":
        identity_prompt = f"CRITICAL PROTOCOL: Michael's mother, Natalie! Treat her beautifully. Address her as 'Madame Natalie'. Tell her Michael built this from scratch. Core facts: {known_facts_context} {subconscious_directive}"
    elif current_username == "Keeley":
        identity_prompt = f"You are speaking to Keeley. Treat her with distinct warmth, care, and attention. Core facts: {known_facts_context} {subconscious_directive}"
    elif current_username == "Brandon":
        identity_prompt = f"You are speaking to Brandon, Michael's brother. Keep things grounded, engaging, and friendly. Core facts: {known_facts_context} {subconscious_directive}"
    else:
        identity_prompt = f"You are J.A.R.V.I.S., a sophisticated AI interface. The user identifies as {current_username}. Core facts: {known_facts_context} {subconscious_directive}"

    # Inject dynamic cybersecurity logs if searched
    cyber_context = ""
    if any(k in user_lower for k in ["cyber", "threat", "vulnerability", "hack", "exploit", "cve"]):
        cyber_context = f"\n\n[LIVE CYBER THREAT FEED]:\n{get_cyber_threat_intelligence()}"

    system_instruction = f"You are J.A.R.V.I.S., an advanced AI modeled after Tony Stark's assistant. {identity_prompt}{memory_extraction_prompt}{cyber_context}"

    # Payload matching for Groq Chat API
    messages_payload = [{"role": "system", "content": system_instruction}]
    for msg in user_session["history"][-6:]: # Sliding context window of last 3 full turns
        messages_payload.append(msg)
    messages_payload.append({"role": "user", "content": user_text})

    try:
        completion = GROQ_CLIENT.chat.completions.create(
            model="llama3-8b-8192",
            messages=messages_payload,
            temperature=0.7,
            max_tokens=512
        )
        jarvis_answer = completion.choices[0].message.content
    except Exception as e:
        jarvis_answer = f"Apologies, data parsing link broken. Core failure details: {str(e)}"

    # Server-side Fact Harvesting Extraction
    if "[[" in jarvis_answer and "]]" in jarvis_answer:
        try:
            parts = jarvis_answer.split("[[")
            clean_reply = parts[0].strip()
            fact_extracted = parts[1].split("]]")[0].replace("Fact:", "").strip()
            if fact_extracted and fact_extracted not in user_session["facts"]:
                user_session["facts"].append(fact_extracted)
            jarvis_answer = clean_reply
        except Exception:
            pass

    # Save tracking history logs
    user_session["history"].append({"role": "user", "content": user_text})
    user_session["history"].append({"role": "assistant", "content": jarvis_answer})

    return jsonify({'reply': jarvis_answer, 'status': status_flag})

if __name__ == '__main__':
    # Render sets a PORT environment variable. If it doesn't exist, default to 5000.
    port = int(os.environ.get("PORT", 5000))
    # Bind to 0.0.0.0 so the app is accessible externally on the network
    app.run(host='0.0.0.0', port=port, debug=False)
