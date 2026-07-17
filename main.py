import io
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import Response, HTMLResponse
from PIL import Image
from google import genai
from google.genai import types
import edge_tts

app = FastAPI()
client = genai.Client()

# Kéregapó viselkedése
szemelyiseg = "Te Kéregapó vagy, a természet bölcs, melegszívű manója. "
    "A meséidet mindig így építsd fel: "
    "1. Kezdd azzal, hogy kedvesen köszöntöd a kis barátodat, és mondd el, hogy éppen egy hatalmas, öreg fenyő előtt álltok. "
    "2. Mesélj arról, miért csodálatos az öreg fenyő, és milyen fontos szerepe van a természetben (pl. hogyan ad otthont a madaraknak, hogyan tisztítja a levegőt). "
    "3. Ne beszélj arról, hogyan beszélsz, csak mesélj a képről. "
    "4. A végén adj egy egyszerű, természetközeli feladatot a gyereknek (pl. 'érintsd meg a fenyő kérgét', 'keress egy tobozt'). "
    "A stílusod legyen lassú, nyugodt és végtelenül barátságos."
app.state.utolso_hang = None

@app.get("/", response_class=HTMLResponse)
async def fooldal():
    # A képed közvetlen linkje
    hatter_kep = "https://i.ibb.co/TMvSZm2y/creen1.png" 
    
    return f"""
    <!DOCTYPE html>
    <html lang="hu">
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <style>
            body {{ 
                margin: 0; 
                padding: 0; 
                height: 100vh; 
                background-color: #5d4037; /* Erdei barna keret */
            }}
            .frame {{ 
                position: relative; 
                width: 100vw; 
                height: 100vh; 
                background-image: url('{hatter_kep}');
                background-size: cover;          /* Kitölti a teljes képernyőt */
                background-position: center;     /* Középre igazítja */
                background-repeat: no-repeat; 
            }}
            /* A láthatatlan gomb a nagyító közepére */
            .kattinthato {{ 
                position: absolute; 
                top: 25%; 
                left: 36%; 
                width: 10%; 
                height: 18%; 
                cursor: pointer; 
            }}
            #file-input {{ display: none; }}
        </style>
    </head>
    <body>
        <div class="frame">
            <div class="kattinthato" onclick="document.getElementById('file-input').click()"></div>
        </div>
        <input type="file" id="file-input" capture="environment" accept="image/*" onchange="upload(this)">
        <script>
            async function upload(input) {{
                const formData = new FormData();
                formData.append('file', input.files[0]);
                // Apró vizuális visszajelzés kattintás után
                alert("Kéregapó épp figyel...");
                const res = await fetch('/api/keregapo', {{ method: 'POST', body: formData }});
                if(res.ok) {{
                    const audio = new Audio('/api/keregapo/hang.mp3');
                    audio.play();
                }}
            }}
        </script>
    </body>
    </html>
    """

@app.post("/api/keregapo")
async def keregapo_mesel(file: UploadFile = File(...)):
    contents = await file.read()
    raw_image = Image.open(io.BytesIO(contents)).convert("RGB")
    response = client.models.generate_content(model='gemini-3.1-flash-lite', contents=[raw_image, "Mesélj!"], config=types.GenerateContentConfig(system_instruction=szemelyiseg))
    communicate = edge_tts.Communicate(response.text, "hu-HU-TamasNeural")
    audio_io = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio": audio_io.write(chunk["data"])
    app.state.utolso_hang = audio_io.getvalue()
    return {"status": "ok"}

@app.get("/api/keregapo/hang.mp3")
async def jatszd_le():
    return Response(content=app.state.utolso_hang, media_type="audio/mpeg")
