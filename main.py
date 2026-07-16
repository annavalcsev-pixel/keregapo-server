import io
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import Response, HTMLResponse
from PIL import Image
from google import genai
from google.genai import types
import edge_tts

app = FastAPI()
client = genai.Client()

# Kéregapó viselkedése: csak mese, szöveg nélkül
szemelyiseg = "Te Kéregapó vagy, a kerti titkok tudója. Mesélj kedvesen, manósan, rövid meséket. (Ne írj le szöveget, csak a hangra fókuszálj!)"
app.state.utolso_hang = None

@app.get("/", response_class=HTMLResponse)
async def fooldal():
    # A te saját háttérképed:
    hatter_kep = "https://i.ibb.co/0RF7gR4k/keregapo-hatter.jpg"
    
    html_tartalom = f"""
    <!DOCTYPE html>
    <html lang="hu">
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ margin: 0; height: 100vh; background: url('{hatter_kep}') center/cover no-repeat; }}
            /* A nagyító az ágon lóg */
            .nagyito {{ position: absolute; top: 15%; left: 35%; width: 80px; cursor: pointer; transition: transform 0.2s; }}
            .nagyito:hover {{ transform: scale(1.1); }}
            #file-input {{ display: none; }}
        </style>
    </head>
    <body>
        <!-- A nagyító ikon -->
        <img src="https://cdn-icons-png.flaticon.com/512/3525/3525547.png" class="nagyito" onclick="document.getElementById('file-input').click()">
        <input type="file" id="file-input" capture="environment" accept="image/*" onchange="upload(this)">
        
        <script>
            async function upload(input) {{
                const formData = new FormData();
                formData.append('file', input.files[0]);
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
    return HTMLResponse(content=html_tartalom)

@app.post("/api/keregapo")
async def keregapo_mesel(file: UploadFile = File(...)):
    contents = await file.read()
    raw_image = Image.open(io.BytesIO(contents)).convert("RGB")
    response = client.models.generate_content(
        model='gemini-3.1-flash-lite', 
        contents=[raw_image, "Mesélj erről a képről Kéregapóként, röviden!"], 
        config=types.GenerateContentConfig(system_instruction=szemelyiseg)
    )
    
    communicate = edge_tts.Communicate(response.text, "hu-HU-TamasNeural")
    audio_io = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio": audio_io.write(chunk["data"])
    app.state.utolso_hang = audio_io.getvalue()
    return {{"status": "ok"}}

@app.get("/api/keregapo/hang.mp3")
async def jatszd_le():
    return Response(content=app.state.utolso_hang, media_type="audio/mpeg")
