import io
import os
from fastapi import FastAPI, File, UploadFile, Form, Optional
from fastapi.responses import Response, HTMLResponse
from PIL import Image
from google import genai
import edge_tts

app = FastAPI()
client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))

# Karakterek és stílusuk leírása
KARAKTEREK = {
    "Kéreg apó": "Bölcs, megfontolt, barátságos, aki az évtizedek alatt felhalmozott tapasztalat magaslatáról szemléli a világot. Mindig észreveszed a láthatatlan összefüggéseket.",
    "Moha anyó": "Kedves, bensőséges, vidám és gondoskodó. Bölcs tanácsokat adsz az erdő apróságairól.",
    "Szélvész manó": "Gyors, pörgős, izgalmas, a mozgás és a levegő szerelmese.",
    "Pille manó": "Légies, kedves, a szépségre és az apró csodákra fókuszáló.",
    "Professzor": "Kívülálló, tárgyilagos, pontos, aki a dolgok tudományos hátterét is megosztja."
}

@app.get("/", response_class=HTMLResponse)
async def fooldal():
    return """
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
    </head>
    <body style="background:#2d1b0d; color:#e0c9a6; font-family:sans-serif; text-align:center; padding:20px;">
        <h1>Természetbúvár Manó</h1>
        <p>Válaszd ki, ki kísérjen és kik vagytok!</p>
        
        <select id="kor" style="padding:10px; font-size:16px;">
            <option value="Aprókák (2-5 év)">Aprókák (2-5 év)</option>
            <option value="Felfedezők (6-11)">Felfedezők (6-11)</option>
            <option value="Természetbúvárok (12-15)">Természetbúvárok (12-15)</option>
            <option value="Örökifjú (szülő)">Örökifjú (szülő)</option>
        </select>
        <br><br>
        <select id="karakter" style="padding:10px; font-size:16px;">
            <option value="Kéreg apó">Kéreg apó</option>
            <option value="Moha anyó">Moha anyó</option>
            <option value="Szélvész manó">Szélvész manó</option>
            <option value="Pille manó">Pille manó</option>
            <option value="Professzor">Professzor</option>
        </select>
        
        <br><br>
        <button onclick="inditKaland()" style="padding:20px 40px; font-size:20px; background:#4CAF50; color:white; border:none; border-radius:10px; cursor:pointer;">FOTÓZÁS & GPS</button>
        <input type="file" id="file" accept="image/*" capture="environment" style="display:none" onchange="Feltolt(this)">
        
        <script>
            let globalLat = "";
            let globalLon = "";

            function inditKaland() {
                // GPS koordináta lekérése a háttérben
                if (navigator.geolocation) {
                    navigator.geolocation.getCurrentPosition(
                        (position) => {
                            globalLat = position.coords.latitude;
                            globalLon = position.coords.longitude;
                            document.getElementById('file').click();
                        },
                        (error) => {
                            // Ha nincs GPS vagy tiltva van, enélkül is elindul
                            document.getElementById('file').click();
                        },
                        { timeout: 10000 }
                    );
                } else {
                    document.getElementById('file').click();
                }
            }

            async function Feltolt(i) {
                const fd = new FormData();
                fd.append('file', i.files[0]);
                fd.append('kor', document.getElementById('kor').value);
                fd.append('karakter', document.getElementById('karakter').value);
                fd.append('lat', globalLat);
                fd.append('lon', globalLon);
                
                alert('Manó vizsgálja a kincset és a tájat...');
                
                try {
                    const r = await fetch('/api/meselj', {method: 'POST', body: fd});
                    if(r.ok) {
                        const b = await r.blob();
                        new Audio(URL.createObjectURL(b)).play();
                    } else {
                        const errText = await r.text();
                        alert('Hiba történt: ' + errText);
                    }
                } catch(e) {
                    alert('Hálózati hiba: ' + e);
                }
            }
        </script>
    </body>
    </html>
    """

@app.post("/api/meselj")
async def meselj(
    file: UploadFile = File(...), 
    kor: str = Form(...), 
    karakter: str = Form(...),
    lat: Optional[str] = Form(None),
    lon: Optional[str] = Form(None)
):
    try:
        contents = await file.read()
        img = Image.open(io.BytesIO(contents)).convert("RGB")
        
        stilus = KARAKTEREK.get(karakter, "Segítőkész természetbúvár.")
        
        gps_info = f"A pillanatnyi GPS koordináták: Szélesség {lat}, Hosszúság {lon}." if lat and lon "A GPS adatok jelenleg nem elérhetők."
        
        prompt = f"""
        TE KIZÁRÓLAG EZ A KARAKTER VAGY: {karakter}.
        A stílusod: {stilus}
        
        A feladatod:
        1. Nézd meg a képet, és tegező stílusban, folyamatos szövegként mesélj a rajta lévő dologról.
        2. SEMMIKÉPP NE HASZNÁLJ SZÁMOZÁST (pl. 1, 2, 3)!
        3. A gyerek/felnőtt korosztálya: {kor}.
        4. Helyszín információ: {gps_info} (ha van, utalhatsz a tájra vagy az erdőtípusra).
        5. Szerkezeti felépítés: 
           - Kezdd a dolog megnevezésével. 
           - Fűzz hozzá egy trükkös természeti összefüggést. 
           - Küldetésként adj egy olyan logikailag kapcsolódó feladatot, ami szorosan illeszkedik a fotózott tárgyhoz (pl. ha tölgyfalevél, keressen makkot; ha fenyőtű, keressen tobozt, vagy a környékre jellemző növényt/kincset).
        """
        
        res = client.models.generate_content(model='gemini-3.1-flash-lite', contents=[img, prompt])
        
        communicate = edge_tts.Communicate(res.text, "hu-HU-TamasNeural")
        audio_io = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio": audio_io.write(chunk["data"])
            
        return Response(audio_io.getvalue(), media_type="audio/mpeg")
        
    except Exception as e:
        print(f"HIBA: {str(e)}")
        return Response(str(e), status_code=500)
