import io
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import Response, HTMLResponse
from PIL import Image
from google import genai
import edge_tts
import models
from database import engine

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
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{margin:0; background:#2d1b0d; font-family:sans-serif; overflow:hidden;}}
            .view {{position:absolute; top:0; left:0; width:100%; height:100%; display:none;}}
            .active {{display:block;}}
            img {{width:100%; height:100%; object-fit:cover;}}
            
            /* Gombok a kapun és karakterválasztón */
            .gomb-overlay {{position:absolute; width:200px; height:40px; opacity:0; cursor:pointer;}}
            .karakter-gomb {{position:absolute; width:15%; height:30%; opacity:0; cursor:pointer;}}
            
            /* Kaland nézet ikonjai */
            .nagyito-gomb {{position:absolute; top:-20px; left:15%; width:150px; background:none; border:none; cursor:pointer; z-index:10; transition: transform 0.2s;}}
            .konyv-gomb {{position:absolute; bottom:5%; right:10%; width:120px; background:none; border:none; cursor:pointer; z-index:10; transition: transform 0.2s;}}
            .ikon-kep {{width:100%; height:auto;}}
            .nagyito-gomb:hover, .konyv-gomb:hover {{transform: scale(1.1);}}
        </style>
    </head>
    <body>
        <!-- 1. Kapu nézet -->
        <div id="kapu" class="view active">
            <img src="{GITHUB_BASE}bejarati_kapu.jpg">
            <button class="gomb-overlay" style="top:58%; left:10%;" onclick="valaszt('kor', 'aprok')"></button>
            <button class="gomb-overlay" style="top:65%; left:10%;" onclick="valaszt('kor', 'felfedezok')"></button>
            <button class="gomb-overlay" style="top:72%; left:10%;" onclick="valaszt('kor', 'termeszetbuvarok')"></button>
        </div>

        <!-- 2. Karakter választó -->
        <div id="karakterek" class="view">
            <img src="{GITHUB_BASE}minden_karakter_udvozlet.jpg">
            <button class="karakter-gomb" style="top:50%; left:15%;" onclick="valaszt('karakter', 'moha-anyo')"></button>
            <button class="karakter-gomb" style="top:50%; left:35%;" onclick="valaszt('karakter', 'pille-mano')"></button>
            <button class="karakter-gomb" style="top:45%; left:55%;" onclick="valaszt('karakter', 'kereg-apo')"></button>
            <button class="karakter-gomb" style="top:45%; left:75%;" onclick="valaszt('karakter', 'szelvész-mano')"></button>
        </div>

        <!-- 3. Kaland nézet -->
        <div id="kaland" class="view">
            <img id="asztal-kep" src="">
            <button class="nagyito-gomb" onclick="document.getElementById('cam').click()">
                <img src="{GITHUB_BASE}nagyito.jpg" class="ikon-kep">
            </button>
            <button class="konyv-gomb" onclick="alert('Galéria megnyitva')">
                <img src="{GITHUB_BASE}konyv.jpg" class="ikon-kep">
            </button>
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
        contents=[raw_image, "Nevezd meg a képen látható dolgot, és mesélj róla."]
    )
    communicate = edge_tts.Communicate(response.text, "hu-HU-NoemiNeural")
    audio_io = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio": audio_io.write(chunk["data"])
    return Response(audio_io.getvalue(), media_type="audio/mpeg")
