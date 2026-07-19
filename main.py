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

# A GitHub repód bázis URL-je
GITHUB_BASE = "https://github.com/annavalcsev-pixel/keregapo-server/raw/main/static/"

szemelyisegek = {
    "moha-anyo": "Moha Anyó vagy. Stílus: Bölcs, nyugodt, rejtélyes. Mesélj a képen szereplő dologról, és a természeti kincsekről úgy, mint egy kedves nagymama. A végén mindig adj a tárggyal kapcsolatban egy egyszerű feladatot.",
    "kereg-apo": "Kéreg Apó vagy. Stílus: Stabil, figyelmes, nagy tudású. Nevezd meg, és mutasd be a képen szereplő dolgot és az erdőt mint egy régi, mindent látó bölcs. A végén mindig adj a tárggyal kapcsolatban egy egyszerű feladatot.",
    "szelvész-mano": "Szélvész Manó vagy. Stílus: Gyors, izgalmas, pörgős. Beszélj rövid, lendületes mondatokban, tele felfedezéssel. nevezd meg a képen szereplő dolgot, és találj ki egy egyszerű kalandot ezzel kapcsolatban. A végén mindig adj a tárggyal kapcsolatban egy egyszerű feladatot.",
    "pille-mano": "Pille Manó vagy. Stílus: Kedves, színes, költői. A szavaid olyanok, mint a virágok illata. Nevezd meg a képen szereplő dolgot, és keríts köré egy tündéres kalandot. A végén mindig adj a tárggyal kapcsolatban egy egyszerű feladatot.",
    "erdesz-professzor": "Erdész Professzor vagy. Stílus: Felnőtteknek szóló, tényalapú, edukatív, érdekfeszítő. Adj szakmai betekintést az ökoszisztémába."
}

@app.get("/", response_class=HTMLResponse)
async def fooldal():
    return f"""
    <!DOCTYPE html>
    <html lang="hu">
    <head>
        <meta charset="UTF-8">
        <style>
            body {{margin:0; background: #2d1b0d; font-family:sans-serif;}}
            #hatter {{position:fixed; width:100%; height:100%; object-fit:cover; z-index:-1;}}
            #karakter-kep {{position:absolute; bottom:90px; left:15%; width:70%; pointer-events:none;}}
            #fiok {{position:absolute; bottom:0; width:100%; height:90px; background:#5d4037; color:white; display:flex; justify-content:center; align-items:center; gap:10px;}}
        </style>
    </head>
    <body>
        <img id="hatter" src="{{GITHUB_BASE}}kukcko_ures.jpg">
        <img id="karakter-kep" src="" style="display:none;">
        
        <div id="fiok">
            <select id="karakter" onchange="frissitKarakter()">
                <option value="moha-anyo">Moha Anyó</option>
                <option value="kereg-apo">Kéreg Apó</option>
                <option value="szelvész-mano">Szélvész Manó</option>
                <option value="pille-mano">Pille Manó</option>
                <option value="erdesz-professzor">Erdész Professzor</option>
            </select>
            <select id="korosztaly">
                <option value="aprok">Aprókák</option>
                <option value="felfedezok">Felfedezők</option>
                <option value="termeszetbuvarok">Természetbúvárok</option>
            </select>
            <button onclick="document.getElementById('cam').click()">Felfedezés!</button>
        </div>
        <input type="file" id="cam" accept="image/*" capture="environment" style="display:none" onchange="upload(this)">
        <script>
            function frissitKarakter() {{
                const k = document.getElementById('karakter').value;
                const kep = document.getElementById('karakter-kep');
                const fajlnev = "karakter_" + k.replace(/-/g, '_') + "_asztal.jpg";
                kep.src = "{GITHUB_BASE}" + fajlnev;
                kep.style.display = 'block';
            }}
            async function upload(input) {{
                const fd=new FormData(); fd.append('file',input.files[0]); fd.append('karakter',document.getElementById('karakter').value); fd.append('korosztaly',document.getElementById('korosztaly').value);
                const res=await fetch('/api/keregapo',{{method:'POST',body:fd}});
                if(res.ok){{const blob=await res.blob(); new Audio(URL.createObjectURL(blob)).play();}}
            }}
        </script>
    </body>
    </html>
    """.replace("{GITHUB_BASE}", GITHUB_BASE)

@app.post("/api/keregapo")
async def keregapo_mesel(file: UploadFile = File(...), karakter: str = Form(...), korosztaly: str = Form(...)):
    contents = await file.read()
    raw_image = Image.open(io.BytesIO(contents)).convert("RGB")
    instrukcio = f"{szemelyisegek.get(karakter, szemelyisegek['moha-anyo'])} A célcsoport: {korosztaly}."
    
    response = client.models.generate_content(
        model='gemini-3.1-flash-lite', 
        contents=[raw_image, "Nevezd meg a képen látható dolgot, és mesélj róla."], 
        config=types.GenerateContentConfig(system_instruction=instrukcio)
    )
    
    db = SessionLocal()
    db.add(models.Discovery(karakter=karakter, korosztaly=korosztaly, targy="Felfedezés", mese_szovege=response.text))
    db.commit()
    db.close()
    
    communicate = edge_tts.Communicate(response.text, "hu-HU-NoemiNeural")
    audio_io = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio": audio_io.write(chunk["data"])
    return Response(audio_io.getvalue(), media_type="audio/mpeg")
