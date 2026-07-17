import io
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import Response, HTMLResponse
from PIL import Image
from google import genai
from google.genai import types
import edge_tts

app = FastAPI()
client = genai.Client()

# Különböző személyiségek korosztály szerint
szemelyisegek = {
    "aprok": "Te Kéregapó vagy, egy nagyon kedves manó. 3-6 éveseknek mesélsz. Használj nagyon egyszerű szavakat, rövid mondatokat. Mesélj elvarázsolt hangon, és legyen a történeted nagyon rövid, játékos és tele csodával. A történet végén mindig adj egy egyszerű, játékos feladatot a képpel kapcsolatosan.",
    "felfedezok": "Te Kéregapó vagy, a természet bölcs tanítója. 7-10 éveseknek mesélsz. A történeted legyen érdekes, tanulságos, mutass be egy konkrét érdekességet a képen látható dologról, és bátorítsd a gyereket a természet megfigyelésére. A történet végén mindig adj egy egyszerű, játékos feladatot a képpel kapcsolatosan.",
    "termeszetbuvarok": "Te Kéregapó vagy, az erdő gondos őrzője. 11+ éveseknek mesélsz. A stílusod legyen mély, elgondolkodtató és bölcs. Beszélj a természet összefüggéseiről, az ökológiai egyensúlyról és a környezet tiszteletéről. A történet végén mindig adj egy egyszerű, de komolyan vehető feladatot a képpel kapcsolatosan."
}

@app.get("/", response_class=HTMLResponse)
async def fooldal():
    hatter_kep = "https://i.ibb.co/TMvSZm2y/creen1.png" 
    
    return f"""
    <!DOCTYPE html>
    <html lang="hu">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <link rel="manifest" href="manifest.json">
        <style>
            body {{ margin: 0; padding: 0; height: 100vh; background-color: #5d4037; overflow: hidden; }}
            .frame {{ position: relative; width: 100vw; height: 100vh; background-image: url('{hatter_kep}'); background-size: cover; background-position: center; }}
            /* A nagyító most balra fent */
            .nagyito {{ position: absolute; top: 15%; left: 10%; width: 20%; height: 20%; cursor: pointer; }}
            .konyv {{ position: absolute; top: 60%; left: 20%; width: 60%; height: 25%; cursor: pointer; }}
            .korosztaly-valaszto {{ position: absolute; top: 5%; left: 10%; width: 80%; text-align: center; color: white; font-family: sans-serif; }}
            select {{ padding: 10px; border-radius: 10px; background: #8d6e63; color: white; border: none; font-size: 16px; }}
            /* A juharmag is balra fent, a nagyítóval azonos helyen */
            #loading {{ display: none; position: absolute; top: 15%; left: 10%; width: 20%; height: 20%; z-index: 100; pointer-events: none; }}
            .juhar {{ width: 100%; height: 100%; animation: spin 1s linear infinite; filter: drop-shadow(0 0 5px white); }}
            @keyframes spin {{ 100% {{ transform: rotate(360deg); }} }}
        </style>
    </head>
    <body>
        <div class="frame">
            <div class="korosztaly-valaszto">
                <label>Kinek meséljen Kéregapó?</label><br>
                <select id="korosztaly">
                    <option value="aprok">Aprókák (3-6 év)</option>
                    <option value="felfedezok">Felfedezők (7-10 év)</option>
                    <option value="termeszetbuvarok">Természetbúvárok (11+ év)</option>
                </select>
            </div>
            <div class="nagyito" onclick="document.getElementById('camera-input').click()"></div>
            <div class="konyv" onclick="document.getElementById('file-input').click()"></div>
        </div>
        <div id="loading"><svg class="juhar" viewBox="0 0 100 100"><path fill="#e67e22" d="M50 10 Q 55 40 80 50 Q 55 60 50 90 Q 45 60 20 50 Q 45 40 50 10 Z"/></svg></div>
        <input type="file" id="camera-input" accept="image/*" capture="environment" onchange="upload(this)" style="display:none">
        <input type="file" id="file-input" accept="image/*" onchange="upload(this)" style="display:none">
        <script>
            async function upload(input) {{
                if (!input.files || input.files.length === 0) return;
                document.getElementById('loading').style.display = 'block';
                const formData = new FormData();
                formData.append('file', input.files[0]);
                formData.append('korosztaly', document.getElementById('korosztaly').value);
                try {{
                    const res = await fetch('/api/keregapo', {{ method: 'POST', body: formData }});
                    if(res.ok) {{
                        const blob = await res.blob();
                        const url = URL.createObjectURL(blob);
                        new Audio(url).play();
                    }}
                }} catch(e) {{ console.error(e); }}
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
    
    response = client.models.generate_content(
        model='gemini-3.1-flash-lite', 
        contents=[raw_image, prompt], 
        config=types.GenerateContentConfig(system_instruction=instrukcio)
    )
    
    communicate = edge_tts.Communicate(
        response.text, 
        "hu-HU-TamasNeural",
        rate="-5%", 
        pitch="-5Hz"
    )
    
    audio_io = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio": audio_io.write(chunk["data"])
    return Response(audio_io.getvalue(), media_type="audio/mpeg")
