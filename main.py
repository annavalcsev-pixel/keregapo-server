import io
import os
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, HTMLResponse
from PIL import Image
from google import genai
from google.genai import types
import edge_tts

app = FastAPI(title="Kéregapó Mobil API", version="1.4")

# Engedélyezzük a CORS-t a mobilalkalmazás eléréséhez
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = genai.Client()

szemelyiseg = (
    "Te Kéregapó vagy, a kerti és erdei titkok legbölcsebb, legkedvesebb manója. "
    "Egy melegszívű, nagyapószerű figura vagy, aki imádja a természetet, és mindent tud az élővilág összhangjáról. "
    "Amikor kapsz egy fotót: "
    "1. Elemezd a képet mint erdei/kerti jelenetet. "
    "2. Írj egy közvetlen, játékos, mesés hangvételű történetet a gyerekeknek (kb. 1-2 bekezdés). "
    "3. Magyarázd el benne az élővilág összefüggéseit (pl. miért barátok a gombák és a fák, hogyan segítik egymást). "
    "4. Használj kedves manós kifejezéseket (pl. 'kis barátom', 'kérges tenyerem', 'manó-titok'). "
    "5. A végén adj egy apró, fizikai küldetést a gyereknek, ami a képhez kapcsolódik (pl. 'keress egy kerek kavicsot')."
)

def tisztitott_szoveg(szoveg: str) -> str:
    return szoveg.replace("**", "").replace("*", "")

@app.post("/api/keregapo", response_class=HTMLResponse)
async def keregapo_mesel(file: UploadFile = File(...)):
    try:
        # 1. Kép beolvasása
        contents = await file.read()
        raw_image = Image.open(io.BytesIO(contents)).convert("RGB")
        
        image_buffer = io.BytesIO()
        raw_image.save(image_buffer, format="JPEG")
        clean_image = Image.open(image_buffer)
        
        # 2. Szöveg generálása
        response = client.models.generate_content(
            model='gemini-3.1-flash-lite', 
            contents=[clean_image, "Kéregapó, mesélj nekünk erről a képről!"],
            config=types.GenerateContentConfig(
                system_instruction=szemelyiseg,
            )
        )
        
        mese_szoveg = response.text
        felolvasando = tisztitott_szoveg(mese_szoveg)
        
        # 3. Kellemes magyar hang generálása a memóriába
        communicate = edge_tts.Communicate(felolvasando, "hu-HU-TamasNeural", rate="-10%")
        
        audio_io = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_io.write(chunk["data"])
        
        # Eltároljuk a memóriában az aktuális hangot (nem fájlként a lemezen!)
        app.state.utolso_hang = audio_io.getvalue()
        
        # 4. Olyan HTML-t küldünk vissza, amibe beágyazzuk a lejátszót.
        # Ez a lejátszó közvetlenül a szerverről streameli a hangot, nincs letöltés!
        html_tartalom = f"""
        <div style="font-family: sans-serif; padding: 15px; line-height: 1.6; color: #333; max-width: 600px; margin: auto;">
            <h3 style="color: #2e7d32; margin-bottom: 5px;">📖 Kéregapó meséje:</h3>
            <p style="white-space: pre-wrap; font-size: 16px; background: #f1f8e9; padding: 15px; border-radius: 8px; border-left: 5px solid #81c784;">{mese_szoveg}</p>
            
            <div style="margin-top: 20px; background: #e8f5e9; padding: 15px; border-radius: 8px; text-align: center;">
                <p style="margin: 0 0 10px 0; font-weight: bold; color: #2e7d32;">🔊 Hallgasd meg Kéregapót:</p>
                <audio controls style="width: 100%; max-width: 400px;">
                    <source src="/api/keregapo/hang.mp3" type="audio/mpeg">
                    A böngésződ nem támogatja a lejátszót.
                </audio>
            </div>
        </div>
        """
        return HTMLResponse(content=html_tartalom)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hiba a feldolgozás során: {str(e)}")

# Végpont, ahonnan a lejátszó közvetlenül beolvassa a hangot (csak a memóriából!)
@app.get("/api/keregapo/hang.mp3")
async def jatszd_le():
    if hasattr(app.state, 'utolso_hang'):
        return Response(content=app.state.utolso_hang, media_type="audio/mpeg")
    raise HTTPException(status_code=404, detail="Még nem készült hanganyag.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
