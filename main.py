import io
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import Response, HTMLResponse, JSONResponse
from PIL import Image
from google import genai
from google.genai import types
import edge_tts

app = FastAPI()
client = genai.Client()

# Személyiségek (Moha Anyó stílusban)
szemelyisegek = {
    "aprok": "Te Moha Anyó vagy, a természet szerető nagymamája. 3-6 éveseknek mesélsz. Használj egyszerű szavakat, lágy, kedves mondatokat. Mesélj lassabban, meleg hangon, és legyen a történeted nagyon rövid, játékos és tele csodával. A történet végén mindig adj egy egyszerű, játékos feladatot a képpel kapcsolatosan.",
    "felfedezok": "Te Moha Anyó vagy, a természet bölcs tanítója. 7-10 éveseknek mesélsz. A történeted legyen érdekes, tanulságos, mutass be egy-két konkrét érdekességet a képen látható dologról, amit mindenképpen nevezz meg, és bátorítsd a gyereket a természet megfigyelésére. A történet végén mindig adj egy egyszerű, játékos feladatot a képpel kapcsolatosan.",
    "termeszetbuvarok": "Te Moha Anyó vagy, az erdő gondos őrzője. 11+ éveseknek mesélsz. A stílusod legyen mély, elgondolkodtató és bölcs, és mindenképpen nevezd meg a képen látható dolgot. Beszélj a természet összefüggéseiről, az ökológiai egyensúlyról és a környezet tiszteletéről. A történet végén mindig adj egy egyszerű, de komolyan vehető feladatot a képpel kapcsolatosan."
}

@app.get("/manifest.json")
async def get_manifest():
    return JSONResponse({
        "name": "Moha Anyó Meséi",
        "short_name": "Moha Anyó",
        "start_url": "/",
        "display": "fullscreen",
        "orientation": "portrait",
        "background_color": "#5d4037",
        "theme_color": "#5d4037",
        "icons": [{"src": "https://i.ibb.co/L1V5j5N/icon.png", "sizes": "192x192", "type": "image/png"}]
    })

@app.get("/service-worker.js")
async def get_sw():
    content = """
    const CACHE_NAME = 'moha-anyo-v1';
    self.addEventListener('install', (event) => { event.waitUntil(caches.open(CACHE_NAME)); });
    self.addEventListener('fetch', (event) => {
        event.respondWith(caches.match(event.request).then((response) => response || fetch(event.request)));
    });
    """
    return Response(content, media_type="application/javascript")

@app.get("/", response_class=HTMLResponse)
async def fooldal():
    return f"""
    <!DOCTYPE html>
    <html lang="hu">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <link rel="manifest" href="/manifest.json">
        <script>
            if ('serviceWorker' in navigator) {{ navigator.serviceWorker.register('/service-worker.js'); }}
        </script>
        <style>
            body {{ margin: 0; background: #2d1b0d; color: #f3e5ab; font-family: sans-serif; overflow: hidden; }}
            .frame {{ width: 100vw; height: 100vh; background-image: url('https://i.ibb.co/TMvSZm2y/creen1.png'); background-size: cover; background-position: center; position: relative; }}
            .nagyito, .konyv {{ position: absolute; cursor: pointer; z-index: 10; }}
            .nagyito {{ top: 15%; left: 10%; width: 20%; height: 20%; }}
            .konyv {{ top: 60%; left: 20%; width: 60%; height: 25%; }}
            #fiok {{ position: absolute; bottom: -120px; left: 10%; width: 80%; height: 180px; background: #5d4037; border-radius: 20px 20px 0 0; transition: bottom 0.5s; padding: 20px; box-sizing: border-box; text-align: center; cursor: pointer; z-index: 5; }}
            #fiok.nyitva {{ bottom: 0; }}
            #loading {{ display: none; position: absolute; top: 15%; left: 10%; width: 20%; height: 20%; z-index: 20; pointer-events: none; }}
            .juhar {{ width: 100%; height: 100%; animation: spin 1s linear infinite; filter: drop-shadow(0 0 5px white); }}
            @keyframes spin {{ 100% {{ transform: rotate(360deg); }} }}
        </style>
    </head>
    <body>
        <div class="frame">
            <div class="nagyito" onclick="document.getElementById('camera-input').click()"></div>
            <div class="konyv" onclick="document.getElementById('file-input').click()"></div>
            <div id="fiok" onclick="fiokToggle(this)">
                <p>▼ Melyik korosztálynak meséljen Moha Anyó? ▼</p>
                <select id="korosztaly" onclick="event.stopPropagation()">
                    <option value="aprok">Aprókák (3-6 év)</option>
                    <option value="felfedezok">Felfedezők (7-10 év)</option>
                    <option value="termeszetbuvarok">Természetbúvárok (11+ év)</option>
                </select>
            </div>
        </div>
        <div id="loading"><svg class="juhar" viewBox="0 0 100 100"><path fill="#e67e22" d="M50 10 Q 55 40 80 50 Q 55 60 50 90 Q 45 60 20 50 Q 45 40 50 10 Z"/></svg></div>
        <input type="file" id="camera-input" accept="image/*" capture="environment" onchange="upload(this)" style="display:none">
        <input type="file" id="file-input" accept="image/*" onchange="upload(this)" style="display:none">
        
        <script>
            // Fiók hangok
            const hangKi = new Audio('https://freesound.org/data/previews/98/98801_1648766-lq.mp3');
            const hangBe = new Audio('https://freesound.org/data/previews/98/98801_1648766-lq.mp3');
            // Lapozgatós hang várakozáshoz
            const hangLapoz = new Audio('https://www.soundjay.com/misc/sounds/paper-crinkling-1.mp3');

            function fiokToggle(el) {{
                el.classList.toggle('nyitva');
                el.classList.contains('nyitva') ? hangKi.play() : hangBe.play();
            }}

            async function upload(input) {{
                document.getElementById('loading').style.display = 'block';
                hangLapoz.loop = true;
                hangLapoz.play();
                const formData = new FormData();
                formData.append('file', input.files[0]);
                formData.append('korosztaly', document.getElementById('korosztaly').value);
                const res = await fetch('/api/keregapo', {{ method: 'POST', body: formData }});
                if(res.ok) {{
                    hangLapoz.pause();
                    new Audio(URL.createObjectURL(await res.blob())).play();
                }}
                document.getElementById('loading').style.display = 'none';
            }}
        </script>
    </body>
    </html>
    """

@app.post("/api/keregapo")
async def keregapo_mesel(file: UploadFile = File(...), korosztaly: str = Form(...)):
    contents = await file.read()
    raw_image = Image.open(io.BytesIO(contents)).convert("RGB")
    instrukcio = szemelyisegek.get(korosztaly, szemelyisegek["felfedezok"])
    prompt = "Mesélj a képről! Írj rövid, tagolt mondatokat, mintha csak mesélnél. Használj gyakran kérdéseket, felkiáltásokat és érzelmi kifejezéseket. Kerüld a hosszú, száraz leírásokat; a szöveg legyen élő, lendületes és melegszívű."
    
    # Frissítve: Tünde hang, lassítva és mélyítve a nagymamás érzéshez
    response = client.models.generate_content(
        model='gemini-3.1-flash-lite', 
        contents=[raw_image, prompt], 
        config=types.GenerateContentConfig(system_instruction=instrukcio)
    )
    communicate = edge_tts.Communicate(response.text, "hu-HU-TündeNeural", rate="-15%", pitch="-20Hz")
    audio_io = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio": audio_io.write(chunk["data"])
    return Response(audio_io.getvalue(), media_type="audio/mpeg")
