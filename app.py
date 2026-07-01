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

# Global server-side tracking
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
            let cleanText = text.replace(/<\/?[^>]+(>|$)/
