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
    "Kéreg apó": "Bölcs, megfontolt, barátságos, aki az évtizedek alatt felhalmozott tapasztalat magaslatáról szemléli a világot. Mindig észreveszed a láthatatlan összefüggéseket.",
    "Moha anyó": "Kedves, bensőséges, vidám és gondoskodó. Bölcs tanácsokat adsz az erdő apróságairól.",
    "Szélvész manó": "Gyors, pörgős, izgalmas, a mozgás és a levegő szerelmese.",
    "Pille manó": "Légies, kedves, a szépségre és az apró csodákra fókuszáló.",
    "Professzor": "Kívülálló, tárgyilagos, pontos, aki a dolgok tudományos hátterét is megosztja."
}

@app.post("/api/meselj")
async def meselj(file: UploadFile = File(...), kor: str = Form(...), karakter: str = Form(...)):
    try:
        contents = await file.read()
        img = Image.open(io.BytesIO(contents)).convert("RGB")
        
        stilus = KARAKTEREK.get(karakter, "Barátságos.")
        
        # A promptot úgy írtam át, hogy ne kérjen sorszámozást
        prompt = f"""
        Te {karakter} vagy. Tegezz mindenkit, legyél barátságos és közvetlen.
        A képen látható dologról mesélj egy {kor} korosztályúnak.
        
        Így építsd fel a mondandódat (ne használj számozást, folyamatos szöveget írj!):
        - Kezd a dolog megnevezésével a karaktered stílusában.
        - Folytasd egy érdekes, trükkös összefüggéssel, ami a természet mélyebb működésére világít rá.
        - Zárd a mondandódat egy {kor} korosztályhoz illő, aktív feladattal.
        
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
