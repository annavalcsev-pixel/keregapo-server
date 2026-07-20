import io
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import Response, HTMLResponse
from PIL import Image
from google import genai
import edge_tts

app = FastAPI()
client = genai.Client()

# Ezt a linket ellenőrizd: pontosan ez a repo neve?
GITHUB_BASE = "https://raw.githubusercontent.com/annavalcsev-pixel/keregapo-server/main/static/"

@app.get("/", response_class=HTMLResponse)
async def fooldal():
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{margin:0; background:#2d1b0d; overflow:hidden;}}
            .view {{position:absolute; width:100%; height:100%; display:none; background-size:cover;}}
            .active {{display:block;}}
            .gomb {{position:absolute; cursor:pointer;}}
        </style>
    </head>
    <body>
        <div id="kapu" class="view active" style="background-image:url('{GITHUB_BASE}bejarati_kapu.jpg')">
            <button class="gomb" style="top:50%; left:20%; width:50%; height:20%; opacity:0" onclick="valaszt('karakter', 'kereg-apo')">Kezdés</button>
        </div>
        <div id="kaland" class="view">
            <button class="gomb" style="top:10%; left:10%; width:30%;" onclick="document.getElementById('input').click()">Nagyító</button>
            <input type="file" id="input" style="display:none" onchange="upload(this)">
        </div>
        <script>
            let char = 'kereg-apo';
            function valaszt(t, v) {{ document.getElementById('kapu').classList.remove('active'); document.getElementById('kaland').classList.add('active'); }}
            async function upload(i) {{
                const fd = new FormData(); fd.append('file', i.files[0]); fd.append('karakter', char);
                const r = await fetch('/api/keregapo', {{method: 'POST', body: fd}});
                if(r.ok) {{ const b = await r.blob(); new Audio(URL.createObjectURL(b)).play(); }}
                else {{ alert('Hiba történt a szerveren!'); }}
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
        contents=[raw_image, "Írj egy rövid, 3 mondatos természetvédelmi oktató szöveget mint egy manó."]
    )
    
    communicate = edge_tts.Communicate(response.text, "hu-HU-TamasNeural")
    audio_io = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio": audio_io.write(chunk["data"])
    return Response(audio_io.getvalue(), media_type="audio/mpeg")
