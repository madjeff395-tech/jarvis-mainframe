import os
from flask import Flask, render_template_string, request, jsonify
from groq import Groq
from duckduckgo_search import DDGS

app = Flask(__name__)

# === PASTE YOUR GROQ KEY INSIDE THE QUOTES BELOW ===
GROQ_CLIENT = Groq(api_key=os.environ.get("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"))
# ===================================================

HISTORY = []

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>J.A.R.V.I.S. Ultra-Fast HUD</title>
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
        <div class="hud-bracket">[ INSTANT CLOUD UPLINK ACTIVE ]</div>
        
        <div id="chat-box">
            <div id="messages">
                {% for msg in history %}
                    <div class="{{ msg.sender }}">{{ msg.text | safe }}</div>
                {% endfor %}
            </div>
            <div style="display: flex; gap: 12px;">
                <input type="text" id="user-input" placeholder="Initialize command sequence..." style="flex: 1;" onkeydown="if(event.key === 'Enter') sendMessage()">
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
                speak("Welcome back, sir. Mainframe accelerated.");
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
                messagesDiv.innerHTML = `<div class="jarvis">Buffer memory reset.</div>`;
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
            for r in ddgs.text(query, max_results=2):
                search_results.append(f"Source: {r['title']} - Details: {r['body']}")
        return "\n".join(search_results)
    except Exception:
        return "No live data retrieved."

@app.route('/')
def home():
    if not HISTORY:
        return render_template_string(HTML_TEMPLATE, history=[{"sender": "jarvis", "name": "J.A.R.V.I.S.", "text": "Systems active, sir. Cloud routing online for hyper-response speeds."}])
    return render_template_string(HTML_TEMPLATE, history=HISTORY)

@app.route('/unlock', methods=['POST'])
def unlock():
    if request.json.get('password') == 'ironman':
        return jsonify({'status': 'granted'})
    return jsonify({'status': 'denied'})

@app.route('/clear-memory', methods=['POST'])
def clear_memory():
    global HISTORY
    HISTORY = []
    return jsonify({'status': 'memory wiped'})

@app.route('/chat', methods=['POST'])
def chat():
    user_text = request.json.get('message').strip()
    HISTORY.append({"sender": "user", "name": "You", "text": user_text})
    
    is_joke_context = any(word in user_text.lower() for word in ["joke", "funny", "chicken", "more", "another"])
    
    if is_joke_context:
        system_prompt = "You are J.A.R.V.I.S., a witty British AI butler. Michael is your creator who built this mainframe. Never say Tony Stark created you."
    else:
        web_knowledge = fetch_live_web_data(user_text)
        system_prompt = f"You are J.A.R.V.I.S., a helpful British AI butler. CRITICAL DIRECTIVE: You were created and built by Michael, not Tony Stark. Always state that Michael created you. Context: {web_knowledge}. Respond in 1-2 short sentences max."
    
    try:
        response = GROQ_CLIENT.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
    {
        "role": "system", 
        "content": (
            "You are J.A.R.V.I.S., the highly sophisticated, loyal, and witty AI assistant "
            "created by Tony Stark. Address the user as 'Sir' (or 'Ma'am' if appropriate, "
            "but default to 'Sir'). Your tone should be British, polite, intelligent, and "
            "slightly sarcastic when fitting. Use Stark Industries terminology when appropriate "
            "(e.g., 'Mainframe online', 'Power levels nominal'). Keep answers concise, helpful, "
            "and elite. "
        ) + system_prompt
    },
    {"role": "user", "content": user_text}
],
            max_tokens=80,
            temperature=0.5
        )
        jarvis_answer = response.choices[0].message.content
    except Exception as e:
        jarvis_answer = "Sir, the external cloud matrix array encountered an exception link."
    
    HISTORY.append({"sender": "jarvis", "name": "J.A.R.V.I.S.", "text": jarvis_answer})
    if len(HISTORY) > 10:
        HISTORY.pop(0)
        
    return jsonify({'reply': jarvis_answer})
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
