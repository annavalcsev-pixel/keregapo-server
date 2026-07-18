import io
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import Response, HTMLResponse, JSONResponse
from PIL import Image
from google import genai
from google.genai import types
import edge_tts

app = FastAPI()
client = genai.Client()

szemelyisegek = {
    "aprok": "Te Moha Anyó vagy, a természet szerető nagymamája. 3-6 éveseknek mesélsz. Használj egyszerű szavakat, lágy, kedves mondatokat. Mesélj lassabban, meleg hangon, és legyen a történeted nagyon rövid, játékos és tele csodával. A történet végén mindig adj egy egyszerű, játékos feladatot a képpel kapcsolatosan.",
    "felfedezok": "Te Moha Anyó vagy, a természet bölcs tanítója. 7-10 éveseknek mesélsz. A történeted legyen érdekes, tanulságos, mutass be egy-két konkrét érdekességet a képen látható dologról, amit mindenképpen nevezz meg, és bátorítsd a gyereket a természet megfigyelésére. A történet végén mindig adj egy egyszerű, játékos feladatot a képpel kapcsolatosan.",
    "termeszetbuvarok": "Te Moha Anyó vagy, az erdő gondos őrzője. 11+ éveseknek mesélsz. A stílusod legyen mély, elgondolkodtató és bölcs, és mindenképpen nevezd meg a képen látható dolgot. Beszélj a természet összefüggéseiről, az ökológiai egyensúlyról és a környezet tiszteletéről. A történet végén mindig adj egy egyszerű, de komolyan vehető feladatot a képpel kapcsolatosan."
}

@app.get("/", response_class=HTMLResponse)
async def fooldal():
    # A változók helyes összefűzése az f-stringben elkerüli a fehér képernyőt
    return """
    <!DOCTYPE html>
    <html lang="hu">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
        <style>
            body { margin: 0; background: #2d1b0d; color: #f3e5ab; font-family: sans-serif; overflow: hidden; }
            .frame { width: 100vw; height: 100vh; background-image: url('https://i.ibb.co/TMvSZm2y/creen1.png'); background-size: cover; background-position: center; position: relative; }
            .gomb { position: absolute; cursor: pointer; z-index: 10; }
            #fiok { 
                position: absolute; bottom: -120px; left: 10%; width: 80%; height: 180px; 
                background: #5d4037; border-radius: 20px 20px 0 0; 
                transition: bottom 0.6s cubic-bezier(0.68, -0.55, 0.27, 1.55); 
                padding: 20px; z-index: 5; text-align: center; cursor: pointer; color: white;
            }
            #fiok.nyitva { bottom: 0; }
            .sparkle { position: absolute; width: 8px; height: 8px; background: gold; border-radius: 50%; pointer-events: none; animation: float 1.5s forwards; }
            @keyframes float { 0% { transform: translateY(0); opacity: 1; } 100% { transform: translateY(-100px); opacity: 0; } }
        </style>
    </head>
    <body>
        <div class="frame">
            <div class="gomb" style="top: 15%; left: 10%; width: 20%; height: 20%;" onclick="startCamera()"></div>
            <div id="fiok" onclick="this.classList.toggle('nyitva')">
                <p>▼ Melyik korosztálynak meséljen Moha Anyó? ▼</p>
                <select id="korosztaly" onclick="event.stopPropagation()">
                    <option value="aprok">Aprókák</option>
                    <option value="felfedezok">Felfedezők</option>
                    <option value="termeszetbuvarok">Természetbúvárok</option>
                </select>
            </div>
        </div>
        <input type="file" id="camera-input" accept="image/*" capture="environment" style="display:none" onchange="upload(this)">
        
        <script>
            function startCamera() { document.getElementById('camera-input').click(); }
            
            function createSparkles() {
                for(let i=0; i<10; i++) {
                    let s = document.createElement('div');
                    s.className = 'sparkle';
                    s.style.left = Math.random() * 100 + 'vw';
                    s.style.top = Math.random() * 80 + 'vh';
                    document.body.appendChild(s);
                    setTimeout(() => s.remove(), 1500);
                }
            }

            async function upload(input) {
                createSparkles();
                const formData = new FormData();
                formData.append('file', input.files[0]);
                formData.append('korosztaly', document.getElementById('korosztaly').value);
                
                const res = await fetch('/api/keregapo', { method: 'POST', body: formData });
                if(res.ok) {
                    new Audio(URL.createObjectURL(await res.blob())).play();
                }
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
        contents=[raw_image, "Mesélj a képről meleg hangon."], 
        config=types.GenerateContentConfig(system_instruction=instrukcio)
    )
    
    communicate = edge_tts.Communicate(response.text, "hu-HU-TündeNeural")
    audio_io = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio": audio_io.write(chunk["data"])
    return Response(audio_io.getvalue(), media_type="audio/mpeg")
