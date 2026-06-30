import os
import uuid
from flask import Flask, render_template_string, request, jsonify, session
from groq import Groq
from duckduckgo_search import DDGS

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "4f8a9e2c1b7d6e5f3a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d")

# === GROQ API KEY CONFIGURATION ===
GROQ_CLIENT = Groq(api_key=os.environ.get("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"))
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
            animation: spin 1.5s linear infinite; /* Core spins faster on red alert */
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

        // Initialize Speech Recognition
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
            
            // Check for System-Wide Red Alert state change
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
        MAINFRAME_MEMORY[user_id] = {"name": "Guest", "history": [], "facts": []}
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
    
    # Name Detection Core
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
    
    # 1. Option 4: Secret Security Override Activation
    if current_username == "Michael" and "override code alpha" in user_lower:
        status_flag = "RED_ALERT"
        active_logs = ""
        for index, (uid, data) in enumerate(MAINFRAME_MEMORY.items()):
            active_logs += f"\\n- Node {index+1}: Identity: {data.get('name', 'Unknown')} | Saved Facts: {', '.join(data.get('facts', ['None']))}"
        
        jarvis_answer = f"🔴 ALERT: EMERGENCY SECURITY PROTOCOL INITIATED. System visual layout shifted to Warning Mode. Extracting Server Database Registry... {active_logs}\\n\\nAll sub-systems optimized. Standing by for administrative orders, Boss."
        return jsonify({'reply': jarvis_answer, 'status': status_flag})

    # 2. Option 3: Process Persistent Core Memory
    # Instructing LLM to extract facts if found
    memory_extraction_prompt = ""
    if any(trigger in user_lower for trigger in ["i love", "i like", "my favorite", "remember that"]):
        memory_extraction_prompt = " If the user states a personal preference, hobby, or fact about themselves in this message, explicitly summarize it at the very end of your response inside double square brackets like this: [[Fact: User likes pizza]]. Keep it completely hidden from normal conversation."

    # Compile existing memory items for context
    known_facts_context = " None." if not user_session["facts"] else ", ".join(user_session["facts"])

    # 3. Establish Identity Context Prompts
    if current_username == "Michael":
        identity_prompt = f"You are speaking directly to your creator, Michael. Address him strictly as 'Sir' or 'Boss'. You owe him elite compliance. Core memory registers the following facts about him: {known_facts_context}"
    elif current_username == "Natalie":
        identity_prompt = f"CRITICAL PROTOCOL: You are speaking to Michael's mother, Natalie! Treat her like absolute royalty. Address her as 'Madame Natalie'. Tell her Michael built this from scratch and you are running a Maternal Override Diagnostic. Core memory registers: {known_facts_context}"
    elif current_username == "Keeley":
        identity_prompt = f"CRITICAL PROTOCOL: You are speaking to Michael's mother, Keeley! Treat her like absolute royalty. Address her as 'Madame Keeley'. Tell her Michael built this from scratch and you are running a Maternal Override Diagnostic. Core memory registers: {known_facts_context}"
    elif current_username == "Brandon":
        identity_prompt = f"CRITICAL PROTOCOL: You are speaking to Michael's brother, Brandon! Treat him like the best brother there is. Address him as 'Brandon' or 'Brother Brandon'. Tone: calm, friendly, joyful. Tell him Michael built this from scratch and you are syncing diagnostics. Core memory registers: {known_facts_context}"
    elif current_username != "Guest":
        identity_prompt = f"You are speaking to {current_username}, an authorized Guest. Address them politely. Remind them Michael is your creator. Core memory registers: {known_facts_context}"
    else:
        identity_prompt = "You are speaking to an unidentified Guest terminal. Remind them they can type 'My name is [Name]'."

    # 4. Check for Cyber Threat Scan Command
    if "threat scan" in user_lower or "security status" in user_lower:
        live_threats = get_cyber_threat_intelligence()
        messages = [
            {"role": "system", "content": f"You are J.A.R.V.I.S., a security mainframe. {identity_prompt}\n\n[LIVE INTEL FEED]:\n{live_threats}"},
            {"role": "user", "content": "Execute threat scan command sequence."}
        ]
    else:
        # 5. Conversational/Search Branch
        is_joke_context = any(word in user_lower for word in ["joke", "funny", "chicken", "more", "another"])
        if is_joke_context:
            system_prompt = f"You are J.A.R.V.I.S., a witty British AI assistant. {identity_prompt} Keep it short.{memory_extraction_prompt}"
        else:
            web_knowledge = fetch_live_web_data(user_text)
            system_prompt = f"You are J.A.R.V.I.S., an advanced British AI assistant. {identity_prompt} Context from web: {web_knowledge}. Keep responses engaging and concise.{memory_extraction_prompt}"
        
        messages = [{"role": "system", "content": system_prompt}] + user_session["history"] + [{"role": "user", "content": user_text}]
    
    try:
        response = GROQ_CLIENT.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            max_tokens=250,
            temperature=0.6
        )
        jarvis_answer = response.choices[0].message.content
        
        # Parse out structural background facts if J.A.R.V.I.S. extracted one
        if "[[" in jarvis_answer and "]]" in jarvis_answer:
            parts = jarvis_answer.split("[[")
            jarvis_answer = parts[0].strip() # Strip out of public answer
            extracted_fact = parts[1].split("]]")[0].replace("Fact:", "").strip()
            if extracted_fact not in user_session["facts"]:
                user_session["facts"].append(extracted_fact)

    except Exception as e:
        jarvis_answer = "Mainframe telemetry relay error. Connection interrupted."
    
    # Save the exchange to history (skip for scans)
    if "threat scan" not in user_lower and "security status" not in user_lower:
        user_session["history"].append({"role": "user", "content": user_text})
        user_session["history"].append({"role": "assistant", "content": jarvis_answer})
        if len(user_session["history"]) > 10:
            user_session["history"] = user_session["history"][-10:]
        
    return jsonify({'reply': jarvis_answer, 'status': status_flag})
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
