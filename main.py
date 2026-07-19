import io
import os
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import Response, HTMLResponse
from PIL import Image
from google import genai
from google.genai import types
import edge_tts
from database import engine, Base, SessionLocal
import models

models.Base.metadata.create_all(bind=engine)
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
client = genai.Client()

GITHUB_BASE = "https://github.com/annavalcsev-pixel/keregapo-server/raw/main/static/"

@app.get("/", response_class=HTMLResponse)
async def fooldal():
    return f"""
    <!DOCTYPE html>
    <html lang="hu">
    <head>
        <meta charset="UTF-8">
        <style>
            body {{margin:0; background:#2d1b0d; font-family:sans-serif; overflow:hidden;}}
            .view {{position:absolute; top:0; left:0; width:100%; height:100%; display:none;}}
            .active {{display:block;}}
            img {{width:100%; height:100%; object-fit:cover;}}
            .tabla-gomb {{position:absolute; width:200px; height:40px; opacity:0; cursor:pointer;}}
            .karakter-gomb {{position:absolute; width:15%; height:30%; opacity:0; cursor:pointer;}}
            #ikon-tarolo {{position:absolute; bottom:20px; width:100%; text-align:center;}}
            .ikon {{width:80px; height:80px; margin:0 20px; cursor:pointer;}}
        </style>
    </head>
    <body>
        <div id="kapu" class="view active">
            <img src="{GITHUB_BASE}bejarati_kapu.jpg">
            <button class="tabla-gomb" style="top:58%; left:10%;" onclick="valaszt('kor', 'aprok')"></button>
            <button class="tabla-gomb" style="top:65%; left:10%;" onclick="valaszt('kor', 'felfedezok')"></button>
            <button class="tabla-gomb" style="top:72%; left:10%;" onclick="valaszt('kor', 'termeszetbuvarok')"></button>
        </div>

        <div id="karakterek" class="view">
            <img src="{GITHUB_BASE}minden_karakter_udvozlet.jpg">
            <!-- Koordináták beállítása a csoportképen lévő karakterekre -->
            <button class="karakter-gomb" style="top:50%; left:20%;" onclick="valaszt('karakter', 'moha-anyo')"></button>
            <button class="karakter-gomb" style="top:50%; left:40%;" onclick="valaszt('karakter', 'kereg-apo')"></button>
        </div>

        <div id="kaland" class="view">
            <img id="asztal-kep" src="">
            <div id="ikon-tarolo">
                <button class="ikon" onclick="document.getElementById('cam').click()">📷</button>
                <button class="ikon" onclick="alert('Galéria megnyitva')">📖</button>
            </div>
        </div>

        <input type="file" id="cam" accept="image/*" capture="environment" style="display:none" onchange="upload(this)">

        <script>
            let state = {{kor: '', karakter: ''}};
            function valaszt(tipus, ertek) {{
                state[tipus] = ertek;
                if(tipus === 'kor') {{ document.getElementById('kapu').classList.remove('active'); document.getElementById('karakterek').classList.add('active'); }}
                if(tipus === 'karakter') {{ 
                    document.getElementById('asztal-kep').src = "{GITHUB_BASE}karakter_" + ertek.replace(/-/g, '_') + "_asztal.jpg";
                    document.getElementById('karakterek').classList.remove('active'); 
                    document.getElementById('kaland').classList.add('active'); 
                }}
            }}
            async function upload(input) {{
                const fd = new FormData(); fd.append('file', input.files[0]); fd.append('karakter', state.karakter);
                const res = await fetch('/api/keregapo', {{method: 'POST', body: fd}});
                if(res.ok) {{ const blob = await res.blob(); new Audio(URL.createObjectURL(blob)).play(); }}
            }}
        </script>
    </body>
    </html>
    """

@app.post("/api/keregapo")
async def keregapo_mesel(file: UploadFile = File(...), karakter: str = Form(...)):
    contents = await file.read()
    raw_image = Image.open(io.BytesIO(contents)).convert("RGB")
    response = client.models.generate_content(
        model='gemini-1.5-flash', 
        contents=[raw_image, "Nevezd meg a képen látható dolgot, és mesélj róla."],
    )
    communicate = edge_tts.Communicate(response.text, "hu-HU-NoemiNeural")
    audio_io = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio": audio_io.write(chunk["data"])
    return Response(audio_io.getvalue(), media_type="audio/mpeg")
