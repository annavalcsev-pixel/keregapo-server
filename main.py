import io
import os
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import Response, HTMLResponse
from PIL import Image
from google import genai
from google.genai import types
import edge_tts
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Adatbázis beállítása
DATABASE_URL = os.environ.get('DATABASE_URL')
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Adatbázis tábla definíciója
class Discovery(Base):
    __tablename__ = "discoveries"
    id = Column(Integer, primary_key=True, index=True)
    character = Column(String(50))
    age_group = Column(String(20))
    found_item = Column(String(100))
    note = Column(Text)

# Tábla létrehozása
Base.metadata.create_all(bind=engine)

app = FastAPI()
app.mount("/static", StaticFiles(directory="."), name="static")

client = genai.Client()

szemelyisegek = {
    "aprok": "Te Moha Anyó vagy, a természet szerető nagymamája. 3-6 éveseknek mesélsz. Használj egyszerű szavakat, lágy, kedves mondatokat. Mesélj lassabban, meleg hangon, és legyen a történeted nagyon rövid, játékos és tele csodával. A történet végén mindig adj egy egyszerű, játékos feladatot a képpel kapcsolatosan.",
    "felfedezok": "Te Moha Anyó vagy, a természet bölcs tanítója. 7-10 éveseknek mesélsz. A történeted legyen érdekes, tanulságos, mutass be egy-két konkrét érdekességet a képen látható dologról, amit mindenképpen nevezz meg, és bátorítsd a gyereket a természet megfigyelésére. A történet végén mindig adj egy egyszerű, játékos feladatot a képpel kapcsolatosan.",
    "termeszetbuvarok": "Te Moha Anyó vagy, az erdő gondos őrzője. 11+ éveseknek mesélsz. A stílusod legyen mély, elgondolkodtató és bölcs, és mindenképpen nevezd meg a képen látható dolgot. Beszélj a természet összefüggéseiről, az ökológiai egyensúlyról és a környezet tiszteletéről. A történet végén mindig adj egy egyszerű, de komolyan vehető feladatot a képpel kapcsolatosan."
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
            body { margin: 0; background: #2d1b0d; overflow: hidden; font-family: sans-serif; }
            #hatter-video { position: fixed; right: 0; bottom: 0; min-width: 100%; min-height: 100%; object-fit: cover; z-index: -1; }
            .btn { position: absolute; cursor: pointer; z-index: 20; background: transparent; }
            #nagyito { top: 30%; left: 16%; width: 20%; height: 12%; }
            #konyv { top: 72%; left: 25%; width: 50%; height: 18%; }
            #loading { display: none; position: absolute; top: 20%; left: 20%; width: 12%; z-index: 30; }
            .juhar { width: 100%; animation: spin 1s linear infinite; }
            @keyframes spin { 100% { transform: rotate(360deg); } }
            #fiok { position: absolute; bottom: 0; width: 100%; height: 60px; background: #5d4037; color: white; text-align: center; padding-top: 10px; z-index: 100; }
        </style>
    </head>
    <body>
        <video autoplay muted loop playsinline id="hatter-video">
            <source src="/static/hatter_1.mp4" type="video/mp4">
        </video>
        <div id="nagyito" class="btn" onclick="inditas('camera')"></div>
        <div id="konyv" class="btn" onclick="inditas('file')"></div>
        <div id="fiok">
            <select id="korosztaly">
                <option value="aprok">Aprókák (3-6)</option>
                <option value="felfedezok">Felfedezők (7-10)</option>
                <option value="termeszetbuvarok">Természetbúvárok (11+)</option>
            </select>
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
                try {
                    const res = await fetch('/api/keregapo', { method: 'POST', body: fd });
                    if(res.ok) {
                        const blob = await res.blob();
                        const audio = new Audio(URL.createObjectURL(blob));
                        audio.play().catch(e => { alert("Kérlek, érintsd meg a képernyőt a mese indításához!"); });
                    }
                } catch (err) { console.error("Hiba:", err); }
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
        contents=[raw_image, "Nevezd meg röviden a képen látható dolgot, majd mesélj róla."], 
        config=types.GenerateContentConfig(system_instruction=instrukcio)
    )
    
    # Adatbázisba mentés
    db = SessionLocal()
    try:
        new_discovery = Discovery(
            character="Moha Anyó",
            age_group=korosztaly,
            found_item="Feldolgozva",
            note=response.text
        )
        db.add(new_discovery)
        db.commit()
    finally:
        db.close()
    
    communicate = edge_tts.Communicate(response.text, "hu-HU-NoemiNeural")
    audio_io = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio": audio_io.write(chunk["data"])
    return Response(audio_io.getvalue(), media_type="audio/mpeg")
