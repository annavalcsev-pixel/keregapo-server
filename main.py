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

# Táblák létrehozása
models.Base.metadata.create_all(bind=engine)

app = FastAPI()
app.mount("/static", StaticFiles(directory="."), name="static")
client = genai.Client()

szemelyisegek = {
    "moha-anyo": "Moha Anyó vagy. Stílus: Bölcs, nyugodt, rejtélyes. Mesélj a természeti kincsekről úgy, mint egy kedves nagymama. A mese végén mindig adj egy egszerű feladatot ",
    "kereg-apo": "Kéreg Apó vagy. Stílus: Stabil, figyelmes, nagy tudású. Mutasd be az erdőt mint egy régi, mindent látó bölcs.",
    "szelvész-mano": "Szélvész Manó vagy. Stílus: Gyors, izgalmas, pörgős. Beszélj rövid, lendületes mondatokban, tele felfedezéssel.",
    "pille-tunder": "Pille Tündér vagy. Stílus: Kedves, színes, költői. A szavaid olyanok, mint a virágok illata.",
    "erdesz-professzor": "Erdész Professzor vagy. Stílus: Felnőtteknek szóló, tényalapú, edukatív, érdekfeszítő. Adj szakmai betekintést az ökoszisztémába."
}

@app.get("/", response_class=HTMLResponse)
async def fooldal():
    return """
    <!DOCTYPE html>
    <html lang="hu">
    <head><meta charset="UTF-8"><style>body{margin:0;background:#2d1b0d;font-family:sans-serif;} #hatter-video{position:fixed;right:0;bottom:0;min-width:100%;min-height:100%;object-fit:cover;z-index:-1;} #fiok{position:absolute;bottom:0;width:100%;height:90px;background:#5d4037;color:white;display:flex;justify-content:center;align-items:center;gap:10px;}</style></head>
    <body>
        <video autoplay muted loop playsinline id="hatter-video"><source src="/static/hatter_1.mp4" type="video/mp4"></video>
        <div id="fiok">
            <select id="karakter" onchange="videoValt()">
                <option value="moha-anyo">Moha Anyó</option>
                <option value="kereg-apo">Kéreg Apó</option>
                <option value="szelvész-mano">Szélvész Manó</option>
                <option value="pille-tunder">Pille Tündér</option>
                <option value="erdesz-professzor">Erdész Professzor</option>
            </select>
            <button onclick="document.getElementById('cam').click()">Felfedezés!</button>
        </div>
        <input type="file" id="cam" accept="image/*" capture="environment" style="display:none" onchange="upload(this)">
        <script>
            function videoValt(){document.getElementById('hatter-video').src="/static/"+document.getElementById('karakter').value+".mp4";}
            async function upload(input){
                const fd=new FormData(); fd.append('file',input.files[0]); fd.append('karakter',document.getElementById('karakter').value);
                const res=await fetch('/api/keregapo',{method:'POST',body:fd});
                if(res.ok){const blob=await res.blob(); new Audio(URL.createObjectURL(blob)).play();}
            }
        </script>
    </body>
    </html>
    """

@app.post("/api/keregapo")
async def keregapo_mesel(file: UploadFile = File(...), karakter: str = Form(...)):
    contents = await file.read()
    raw_image = Image.open(io.BytesIO(contents)).convert("RGB")
    
    response = client.models.generate_content(
        model='gemini-3.1-flash-lite', 
        contents=[raw_image, "Nevezd meg a képen látható dolgot, és mesélj róla."], 
        config=types.GenerateContentConfig(system_instruction=szemelyisegek.get(karakter))
    )
    
    db = SessionLocal()
    db.add(models.Discovery(karakter=karakter, targy="Ismeretlen", mese_szovege=response.text))
    db.commit()
    db.close()
    
    communicate = edge_tts.Communicate(response.text, "hu-HU-NoemiNeural")
    audio_io = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio": audio_io.write(chunk["data"])
    return Response(audio_io.getvalue(), media_type="audio/mpeg")
