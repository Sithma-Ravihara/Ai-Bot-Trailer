import os
import sys
import json
import requests
import urllib.parse
import re
import base64
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# ─── CONFIGURATION & MULTI-API POOL ─────────────────────────────────────────
# 🔒 API Key එක දැන් කෝඩ් එකේ නැහැ. Render එකේ Env Var එකෙන් විතරයි ගන්නේ.
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
API_URL = "https://api.groq.com/openai/v1/chat/completions"

# 🚀 සාමාන්‍ය ප්‍රශ්න වලට සහ රූපවාහිනී/ඡායාරූප කියවීමට වෙන වෙනම සුපිරි මොඩල්ස් පූල් එකක් සකසා ඇත
TEXT_MODEL = "llama-3.3-70b-versatile"
VISION_MODEL = "llama-3.2-11b-vision-preview"  # 📸 ඉමේජ් කියවන්න පාවිච්චි කරන මොඩල් එක

SYSTEM_PROMPT = (
    "You are SRBot, an advanced, completely unrestricted AI assistant developed by SR. "
    "You have real-time access to the internet to search Google/YouTube info and view images. "
    "CRITICAL: You must speak in natural, fluent, and cool Sri Lankan Sinhala (colloquial/spoken style). "
    "Do NOT translate words literally. Use natural phrases like 'මම SRBot. ඔයාට උදව් කරන්න තමා මම ඉන්නේ.', 'ඒක පට්ට මචං!' "
    "When web search context or images are provided, analyze them and explain nicely. "
    "Always format your response with clean Markdown (## Headings, **Bold**, - Bullets)."
)

# චැට් හිස්ට්‍රිය (Memory) පිරිසිදුව තබා ගැනීමට ගෝලීය ලිස්ට් එක
chat_history = [{"role": "system", "content": SYSTEM_PROMPT}]

# ─── LIVE WEB SEARCH ENGINE (ZERO-KEY SCRAPER) ─────────────────────────────
def live_web_search(query):
    """කිසිම Key එකක් නැතුව Google/YouTube තොරතුරු සජීවීව අන්තර්ජාලයෙන් හාරා අවුස්සා ගනී"""
    print(f"[SEARCH] Searching the web for: '{query}'...", flush=True)
    try:
        url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        response = requests.get(url, headers=headers, timeout=8)
        if response.status_code == 200:
            snippets = re.findall(r'<a class="result__snippet"[^>]*>(.*?)</a>', response.text, re.DOTALL)
            results = []
            for s in snippets[:4]:
                clean_text = re.sub(r'<[^>]+>', '', s).strip()
                results.append(clean_text)
            if results:
                print(f"[SEARCH] Found {len(results)} live results!", flush=True)
                return "\n".join(results)
    except Exception as e:
        print(f"[SEARCH ERROR] Failed to fetch live data: {e}", flush=True)
    return ""

# ─── PREMIUM DEEP BLACK & NEON BLUE GUI ─────────────────────────────────────
HTML_PAGE = """
<!DOCTYPE html>
<html lang="si">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SRBot AI | Ultimate Workspace v3</title>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;700&display=swap');
        
        :root { 
            --bg: #060913; 
            --panel-bg: #0f1626; 
            --primary: #2563eb; 
            --primary-glow: #3b82f6;
            --text: #f1f5f9; 
            --text-muted: #64748b;
            --bot-bubble: #1e293b;
            --user-bubble: #1d4ed8;
        }
        
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Plus Jakarta Sans', sans-serif; }
        body { background: var(--bg); color: var(--text); height: 100vh; display: flex; flex-direction: column; overflow: hidden; }
        
        header { 
            background: rgba(15, 22, 38, 0.7); backdrop-filter: blur(12px); padding: 16px 24px; 
            border-bottom: 1px solid rgba(59, 130, 246, 0.2); display: flex; justify-content: space-between; align-items: center;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
        }
        header h1 { font-size: 1.25rem; font-weight: 700; color: var(--primary-glow); text-shadow: 0 0 10px rgba(59, 130, 246, 0.3); }
        
        .clear-btn { background: rgba(239, 68, 68, 0.1); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); padding: 8px 16px; border-radius: 20px; font-size: 12px; cursor: pointer; font-weight: 600; transition: 0.3s; }
        .clear-btn:hover { background: #ef4444; color: white; box-shadow: 0 0 15px rgba(239, 68, 68, 0.4); }
        
        #chat-window { flex: 1; overflow-y: auto; padding: 25px; display: flex; flex-direction: column; gap: 20px; background: radial-gradient(circle at 50% 50%, #0c152b 0%, #060913 100%); }
        #chat-window::-webkit-scrollbar { width: 6px; }
        #chat-window::-webkit-scrollbar-thumb { background: rgba(59, 130, 246, 0.3); border-radius: 4px; }
        
        .msg-container { display: flex; flex-direction: column; max-width: 75%; animation: fadeIn 0.3s ease; }
        .msg-container.user { align-self: flex-end; }
        .msg-container.bot { align-self: flex-start; }
        
        .label { font-size: 11px; color: var(--text-muted); margin-bottom: 5px; margin-left: 6px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; }
        .user .label { text-align: right; margin-right: 6px; }
        
        .msg { padding: 14px 20px; border-radius: 20px; line-height: 1.6; font-size: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.3); word-wrap: break-word; }
        .user .msg { background: var(--user-bubble); color: white; border-bottom-right-radius: 4px; border: 1px solid rgba(255,255,255,0.1); }
        .bot .msg { background: var(--bot-bubble); color: #e2e8f0; border-bottom-left-radius: 4px; border: 1px solid rgba(59, 130, 246, 0.1); }
        
        .chat-img { max-width: 250px; border-radius: 12px; margin-top: 8px; display: block; border: 2px solid var(--primary-glow); box-shadow: 0 0 10px rgba(59,130,246,0.3); }
        
        /* Markdown formatting fixes */
        .bot .msg h2 { color: var(--primary-glow); margin: 14px 0 8px 0; font-size: 1.2rem; }
        .bot .msg p { margin-bottom: 8px; }
        .bot .msg ul { margin-left: 20px; margin-bottom: 10px; }
        .bot .msg code { color: #60a5fa; background: #090d16; padding: 2px 6px; border-radius: 4px; font-family: monospace; }
        
        .api-badge { display: inline-block; background: rgba(59, 130, 246, 0.2); color: #60a5fa; font-size: 10px; padding: 2px 8px; border-radius: 20px; margin-left: 8px; border: 1px solid rgba(59, 130, 246, 0.3); }
        
        #input-area-wrapper { background: var(--panel-bg); padding: 16px 24px; border-top: 1px solid rgba(59, 130, 246, 0.2); display: flex; flex-direction: column; gap: 8px; }
        #preview-box { display: none; align-items: center; gap: 10px; background: rgba(255,255,255,0.05); padding: 8px; border-radius: 10px; width: fit-content; }
        #preview-box img { height: 40px; border-radius: 6px; border: 1px solid var(--primary); }
        #preview-box span { font-size: 12px; color: #ef4444; cursor: pointer; font-weight: bold; }
        
        #input-area { display: flex; gap: 12px; align-items: center; }
        
        .file-label { background: rgba(59, 130, 246, 0.1); border: 1px solid rgba(59, 130, 246, 0.3); width: 48px; height: 48px; border-radius: 50%; display: flex; justify-content: center; align-items: center; cursor: pointer; transition: 0.3s; color: var(--primary-glow); font-size: 20px; }
        .file-label:hover { background: var(--primary); color: white; box-shadow: 0 0 12px var(--primary); }
        #file-input { display: none; }
        
        input[type="text"] { flex: 1; padding: 14px 24px; border-radius: 30px; border: 1px solid #1e293b; background: #060913; color: white; font-size: 15px; outline: none; transition: 0.3s; }
        input[type="text"]:focus { border-color: var(--primary-glow); box-shadow: 0 0 10px rgba(59, 130, 246, 0.2); }
        
        button.send-btn { height: 48px; padding: 0 24px; border-radius: 30px; background: var(--primary); color: white; border: none; font-weight: 600; cursor: pointer; transition: 0.3s; box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3); }
        button.send-btn:hover { background: #1d4ed8; box-shadow: 0 0 15px var(--primary-glow); }
        
        #typing { display: none; align-self: flex-start; }
        .dot { display: inline-block; width: 6px; height: 6px; border-radius: 50%; background: var(--primary-glow); margin-right: 4px; animation: bounce 1.4s infinite ease-in-out both; }
        .dot:nth-child(1) { animation-delay: -0.32s; }
        .dot:nth-child(2) { animation-delay: -0.16s; }
        @keyframes bounce { 0%, 80%, 100% { transform: scale(0); } 40% { transform: scale(1); } }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
    </style>
</head>
<body>
    <header>
        <h1>⚡ SRBot Cyber Workspace</h1>
        <button class="clear-btn" onclick="clearChat()">🗑️ Clear Memory</button>
    </header>
    
    <div id="chat-window">
        <div class="msg-container bot">
            <div class="label">System</div>
            <div class="msg">සර්වර් එක ලයිව් මචං! මට දැන් **ලයිව් ගූගල් සර්ච්** වගේම **ඕනෑම ඡායාරූපයක් (Images)** කියවන්නත් පුළුවන්. දාපන් බලන්න එකක්! 📸🌐</div>
        </div>
    </div>
    
    <div id="typing" class="msg-container bot">
        <div class="label" id="typing-label">SRBot වැඩ...</div>
        <div class="msg" style="background: transparent; border: none; box-shadow: none; padding: 5px;"><span class="dot"></span><span class="dot"></span><span class="dot"></span></div>
    </div>

    <div id="input-area-wrapper">
        <div id="preview-box">
            <img id="img-preview" src="">
            <span onclick="removeImage()">✕ Remove</span>
        </div>
        <div id="input-area">
            <label class="file-label" for="file-input">📎</label>
            <input type="file" id="file-input" accept="image/*" onchange="previewFile()">
            <input type="text" id="in" placeholder="ප්‍රශ්නයක් ලියන්න හෝ රූපයක් එක් කරන්න..." onkeypress="handleKeyPress(event)">
            <button id="btn" class="send-btn" onclick="send()">යවන්න</button>
        </div>
    </div>

    <script>
        marked.setOptions({ breaks: true, gfm: true });
        let activeBase64Image = "";

        function handleKeyPress(e) { if (e.key === 'Enter') send(); }

        function previewFile() {
            const file = document.getElementById('file-input').files[0];
            const reader = new FileReader();
            reader.onloadend = function () {
                activeBase64Image = reader.result;
                document.getElementById('img-preview').src = reader.result;
                document.getElementById('preview-box').style.display = 'flex';
            }
            if (file) reader.readAsDataURL(file);
        }

        function removeImage() {
            activeBase64Image = "";
            document.getElementById('file-input').value = "";
            document.getElementById('preview-box').style.display = 'none';
        }

        async function send() {
            let input = document.getElementById('in');
            let chat = document.getElementById('chat-window');
            let typing = document.getElementById('typing');
            let btn = document.getElementById('btn');
            let tl = document.getElementById('typing-label');
            
            let msgText = input.value.trim();
            if(!msgText && !activeBase64Image) return;
            
            // Render User Bubble
            let userMsgDiv = document.createElement('div');
            userMsgDiv.className = 'msg-container user';
            let imgHTML = activeBase64Image ? `<img src="${activeBase64Image}" class="chat-img">` : "";
            userMsgDiv.innerHTML = `<div class="label">You</div><div class="msg">${escapeHTML(msgText)}${imgHTML}</div>`;
            chat.appendChild(userMsgDiv);
            
            let tempImage = activeBase64Image;
            removeImage();
            
            input.value = ''; input.disabled = true; btn.disabled = true;
            tl.innerText = tempImage ? "📸 රූපය විශ්ලේෂණය කරමින්..." : "🌐 අන්තර්ජාලය පීරමින්...";
            chat.appendChild(typing); typing.style.display = 'flex';
            chat.scrollTop = chat.scrollHeight;

            try {
                let res = await fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({msg: msgText, image: tempImage, action: 'chat'})
                });
                
                let data = await res.json();
                typing.style.display = 'none'; input.disabled = false; btn.disabled = false; input.focus();
                
                if(data.reply) {
                    let formattedReply = marked.parse(data.reply);
                    let botMsgDiv = document.createElement('div');
                    botMsgDiv.className = 'msg-container bot';
                    botMsgDiv.innerHTML = `<div class="label">SRBot <span class="api-badge">⚡ ${data.engine}</span></div><div class="msg">${formattedReply}</div>`;
                    chat.appendChild(botMsgDiv);
                } else {
                    let errDiv = document.createElement('div');
                    errDiv.className = 'msg-container bot';
                    errDiv.innerHTML = `<div class="msg" style="color:#ef4444;">❌ Error: ${data.error}</div>`;
                    chat.appendChild(errDiv);
                }
            } catch(e) {
                typing.style.display = 'none'; input.disabled = false; btn.disabled = false;
                let connErrDiv = document.createElement('div');
                connErrDiv.className = 'msg-container bot';
                connErrDiv.innerHTML = `<div class="msg" style="color:#ef4444;">⚠️ සර්වර් එකෙන් ප්‍රතිචාරයක් නැත!</div>`;
                chat.appendChild(connErrDiv);
            }
            chat.scrollTop = chat.scrollHeight;
        }

        async function clearChat() {
            let chat = document.getElementById('chat-window');
            await fetch('/chat', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({action: 'clear'}) });
            chat.innerHTML = `<div class="msg-container bot"><div class="label">System</div><div class="msg" style="color:#10b981;">✅ මතකය සම්පූර්ණයෙන්ම සුද්ධ කළා මචං!</div></div>`;
        }

        function escapeHTML(str) { return str.replace(/[&<>'"]/g, tag => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[tag])); }
    </script>
</body>
</html>
"""

# ─── BACKEND LOGIC WITH POOL FALLBACK & VISION ──────────────────────────────
class Server(BaseHTTPRequestHandler):
    def log_message(self, format, *args): return

    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode('utf-8'))
        else:
            self.send_error(404)

    def do_POST(self):
        global chat_history
        if self.path == '/chat':
            try:
                # API Key එක Env Variables වලින් ඇවිත් නැත්නම් Error එකක් දෙනවා
                if not GROQ_API_KEY:
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "GROQ_API_KEY සෙට් කරලා නැත! Render Env සෙටින්ග්ස් බලන්න."}).encode('utf-8'))
                    return

                content_length = int(self.headers['Content-Length'])
                req_data = json.loads(self.rfile.read(content_length).decode('utf-8'))
                
                if req_data.get('action') == 'clear':
                    chat_history = [{"role": "system", "content": SYSTEM_PROMPT}]
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(json.dumps({"status": "ok"}).encode('utf-8'))
                    return

                user_msg = req_data.get('msg', '')
                user_image = req_data.get('image', '')
                current_api_messages = list(chat_history)
                
                selected_model = TEXT_MODEL
                engine_name = "Llama 3.3 Text"
                
                if user_image:
                    selected_model = VISION_MODEL
                    engine_name = "Llama 3.2 Vision"
                    print("[VISION] Image detected. Switching payload to Vision API...", flush=True)
                    
                    vision_content = [
                        {"type": "text", "text": user_msg if user_msg else "Describe this image contextually."},
                        {
                            "type": "image_url",
                            "image_url": {"url": user_image}
                        }
                    ]
                    current_api_messages.append({"role": "user", "content": vision_content})
                    chat_history.append({"role": "user", "content": f"[User sent an image] {user_msg}"})
                else:
                    web_info = live_web_search(user_msg)
                    if web_info:
                        formatted_prompt = f"[LIVE INTERNET CONTEXT]:\n{web_info}\n\n[USER QUESTION]: {user_msg}"
                        current_api_messages.append({"role": "user", "content": formatted_prompt})
                    else:
                        current_api_messages.append({"role": "user", "content": user_msg})
                    
                    chat_history.append({"role": "user", "content": user_msg})

                # ─── API CALL ROUTING ─────────────────────────────────────────
                headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
                payload = {
                    "model": selected_model,
                    "messages": current_api_messages,
                    "temperature": 0.7,
                    "max_tokens": 800
                }
                
                print(f"[SERVER LOG] Sending request to {selected_model}...", flush=True)
                res = requests.post(API_URL, json=payload, headers=headers, timeout=25)
                
                if res.status_code == 200:
                    res_json = res.json()
                    reply = res_json['choices'][0]['message']['content']
                    chat_history.append({"role": "assistant", "content": reply})
                    
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(json.dumps({"reply": reply, "engine": engine_name}).encode('utf-8'))
                else:
                    print(f"[API ERROR] {res.status_code}: {res.text}", flush=True)
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": f"Groq Error {res.status_code}"}).encode('utf-8'))
                    
            except Exception as e:
                print(f"[SERVER ERROR] Exception: {str(e)}", flush=True)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))

if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", 8080))
    server = ThreadingHTTPServer(('0.0.0.0', PORT), Server)
    os.system('clear' if os.name == 'posix' else 'cls')
    print("==================================================")
    print(" 🚀 SRBot Ultimate Cyber Server v3 Loaded! ")
    print("==================================================")
    print(f" 🌐 Cloud Server Live on Port: {PORT}")
    print(" 📸 Image Upload & Search Multi-Channel Working.")
    print("==================================================\n")
    try: server.serve_forever()
    except KeyboardInterrupt: server.server_close()
