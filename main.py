import io
import os
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import Response, HTMLResponse
from PIL import Image
from google import genai
import edge_tts

app = FastAPI()
client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))

# Karakterek és stílusuk leírása
KARAKTEREK = {
    "Kéreg apó": "Bölcs, megfontolt, barátságos, a fák magasságából szemlélődsz. Érdekes összefüggésekre világítasz rá trükkös módon.",
    "Moha anyó": "Kedves, bensőséges, vidám és gondoskodó. Bölcs tanácsokat adsz az erdő apróságairól.",
    "Szélvész manó": "Gyors, pörgős, izgalmas, a mozgás és a levegő szerelmese.",
    "Pille manó": "Légies, kedves, a szépségre és az apró csodákra fókuszáló.",
    "Professzor": "Kívülálló, tárgyilagos, pontos, aki a dolgok tudományos hátterét is megosztja."
}

@app.get("/", response_class=HTMLResponse)
async def fooldal():
    return """
    <html>
    <body style="background:#2d1b0d; color:#e0c9a6; font-family:sans-serif; text-align:center; padding:20px;">
        <h1>Természetbúvár Manó</h1>
        <p>Válaszd ki, ki kísérjen és kik vagytok!</p>
        
        <select id="kor" style="padding:10px; font-size:16px;">
            <option value="Aprókák (2-5 év)">Aprókák (2-5 év)</option>
            <option value="Felfedezők (6-11)">Felfedezők (6-11)</option>
            <option value="Természetbúvárok (12-15)">Természetbúvárok (12-15)</option>
            <option value="Örökifjú (szülő)">Örökifjú (szülő)</option>
        </select>
        
        <select id="karakter" style="padding:10px; font-size:16px;">
            <option value="Kéreg apó">Kéreg apó</option>
            <option value="Moha anyó">Moha anyó</option>
            <option value="Szélvész manó">Szélvész manó</option>
            <option value="Pille manó">Pille manó</option>
            <option value="Professzor">Professzor</option>
        </select>
        
        <br><br>
        <button onclick="document.getElementById('file').click()" style="padding:20px 40px; font-size:20px; background:#4CAF50; color:white; border:none; border-radius:10px; cursor:pointer;">FOTÓZÁS</button>
        <input type="file" id="file" accept="image/*" capture="environment" style="display:none" onchange="upload(this)">
        
        <script>
            async function upload(i) {
                const fd = new FormData();
                fd.append('file', i.files[0]);
                fd.append('kor', document.getElementById('kor').value);
                fd.append('karakter', document.getElementById('karakter').value);
                alert('Manó vizsgálja a kincset...');
                const r = await fetch('/api/meselj', {method: 'POST', body: fd});
                if(r.ok) {
                    const b = await r.blob();
                    new Audio(URL.createObjectURL(b)).play();
                } else {
                    alert('Hiba történt!');
                }
            }
        </script>
    </body>
    </html>
    """

@app.post("/api/meselj")
async def meselj(file: UploadFile = File(...), kor: str = Form(...), karakter: str = Form(...)):
    try:
        contents = await file.read()
        img = Image.open(io.BytesIO(contents)).convert("RGB")
        
        stilus = KARAKTEREK.get(karakter, "Barátságos.")
        
        prompt = f"""
        Te {karakter} vagy. Tegezz mindenkit, legyél barátságos és közvetlen.
        A képen látható dologról mesélj egy {kor} korosztályúnak (vagy örökifjúnak).
        
        Kövesd ezt a struktúrát:
        1. Nevezd meg a képen látható dolgot a karaktered stílusában.
        2. Mondj el róla egy érdekes, trükkös összefüggést (természetbúvár szemmel).
        3. Adj egy {kor} korosztályhoz illő, aktív feladatot (pl. rajzold le, figyeld meg a részleteket).
        
        Stílusod leírása: {stilus}
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
