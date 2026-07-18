import io
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import Response, HTMLResponse
from PIL import Image
from google import genai
from google.genai import types
import edge_tts

app = FastAPI()
client = genai.Client()

szemelyisegek = {
    "aprok": "Te Moha Anyó vagy, a természet szerető nagymamája. 3-6 éveseknek mesélsz. Használj egyszerű szavakat, lágy, kedves mondatokat. Mesélj lassabban, meleg hangon, és legyen a történeted nagyon rövid, játékos és tele csodával. A történet végén mindig adj egy egyszerű, játékos feladatot a képpel kapcsolatosan.",
    "felfedezok": "Te Moha Anyó vagy, a természet bölcs tanítója, gondos őre. 7-10 éveseknek mesélsz. A történeted legyen érdekes, tanulságos, mutass be egy-két konkrét érdekességet a képen látható dologról, amit mindenképpen nevezz meg, és bátorítsd a gyereket a természet megfigyelésére. A történet végén mindig adj egy egyszerű, játékos feladatot a képpel kapcsolatosan.",
    "termeszetbuvarok": "Te Moha Anyó vagy, az erdő gondos őrzője, bölcs tanítója. 11+ éveseknek mesélsz. A stílusod legyen mély, elgondolkodtató és bölcs, és mindenképpen nevezd meg a képen látható dolgot. Beszélj a természet összefüggéseiről, az ökológiai egyensúlyról és a környezet tiszteletéről. A történet végén mindig adj egy egyszerű, de komolyan vehető feladatot a képpel kapcsolatosan."
}

@app.get("/", response_class=HTMLResponse)
async def fooldal():
    return """
    <!DOCTYPE html>
    <html lang="hu">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <style>
            body { margin: 0; background: #2d1b0d; overflow: hidden; }
            .frame { width: 100vw; height: 100vh; background-image: url('https://i.ibb.co/XhH2NxP/Moha-any-2.png'); background-size: cover; background-position: center; position: relative; }
            
            /* Gombok - finomhangolt pozíciók */
            .btn { position: absolute; cursor: pointer; z-index: 20; background: transparent; }
            #nagyito { top: 35%; left: 22%; width: 20%; height: 12%; }
            #konyv { top: 68%; left: 25%; width: 50%; height: 18%; }
            
            #loading { display: none; position: absolute; top: 20%; left: 20%; width: 12%; z-index: 30; }
            .juhar { width: 100%; animation: spin 1s linear infinite; }
            @keyframes spin { 100% { transform: rotate(360deg); } }
            
            /* Fiók és választó - z-index növelve */
            #fiok { position: absolute; bottom: 0; width: 100%; height: 60px; background: #5d4037; color: white; text-align: center; padding-top: 10px; z-index: 100; }
            select { font-size: 16px; padding: 5px; z-index: 101; }
        </style>
    </head>
    <body>
        <div class="frame">
            <div id="nagyito" class="btn" onclick="inditas('camera')"></div>
            <div id="konyv" class="btn" onclick="inditas('file')"></div>
            <div id="fiok">
                <select id="korosztaly">
                    <option value="aprok">Aprókák (3-6)</option>
                    <option value="felfedezok">Felfedezők (7-10)</option>
                    <option value="termeszetbuvarok">Természetbúvárok (11+)</option>
                </select>
            </div>
        </div>
        <div id="loading"><svg class="juhar" viewBox="0 0 100 100"><path fill="#e67e22" d="M50 10 Q 55 40 80 50 Q 55 60 50 90 Q 45 60 20 50 Q 45 40 50 10 Z"/></svg></div>
        <input type="file" id="cam" accept="image/*" capture="environment" style="display:none" onchange="upload(this)">
        <input type="file" id="fil" accept="image/*" style="display:none" onchange="upload(this)">
        <script>
            function inditas(tipus) { tipus === 'camera' ? document.getElementById('cam').click() : document.getElementById('fil').click(); }
            async function upload(input) {
                document.getElementById('loading').style.display = 'block';
                const fd = new FormData();
                fd.append('file', input.files[0]);
                fd.append('korosztaly', document.getElementById('korosztaly').value);
                const res = await fetch('/api/keregapo', { method: 'POST', body: fd });
                if(res.ok) {
                    const audio = new Audio(URL.createObjectURL(await res.blob()));
                    audio.play();
                }
                document.getElementById('loading').style.display = 'none';
            }
        </script>
    </body>
    </html>
    """

@app.post("/api/keregapo")
async def keregapo_mesel(file: UploadFile = File(...), korosztaly: str = Form(...)):
    contents = await file.read()
    raw_image = Image.open(io.BytesIO(contents)).convert("RGB")
    instrukcio = szemelyisegek.get(korosztaly, szemelyisegek["felfedezok"])
    
    response = client.models.generate_content(
        model='gemini-3.1-flash-lite', 
        contents=[raw_image, "Mesélj a képről."], 
        config=types.GenerateContentConfig(system_instruction=instrukcio)
    )
    
    # Új, meleg női hang: Noémi
    communicate = edge_tts.Communicate(response.text, "hu-HU-NoemiNeural")
    audio_io = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio": audio_io.write(chunk["data"])
    return Response(audio_io.getvalue(), media_type="audio/mpeg")
