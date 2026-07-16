import io
import os
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, HTMLResponse
from PIL import Image
from google import genai
from google.genai import types
import edge_tts

app = FastAPI(title="Kéregapó Mobil API", version="1.5")

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

# VADONATÚJ FŐOLDAL – Szép, mobilbarát felület közvetlenül a főcímen!
@app.get("/", response_class=HTMLResponse)
async def fooldal():
    html_tartalom = """
    <!DOCTYPE html>
    <html lang="hu">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Kéregapó Varázskönyve</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
                margin: 0;
                padding: 20px;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                color: #2e7d32;
            }
            .container {
                background: #ffffff;
                padding: 30px;
                border-radius: 20px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                text-align: center;
                max-width: 450px;
                width: 100%;
                border: 3px solid #81c784;
            }
            h1 { font-size: 24px; margin-bottom: 10px; color: #1b5e20; }
            p { font-size: 15px; color: #33691e; line-height: 1.5; }
            .file-input-wrapper {
                margin: 25px 0;
                position: relative;
            }
            input[type="file"] {
                display: none;
            }
            .custom-file-upload {
                background-color: #4caf50;
                color: white;
                padding: 15px 25px;
                border-radius: 50px;
                cursor: pointer;
                font-size: 16px;
                font-weight: bold;
                display: inline-block;
                transition: all 0.3s ease;
                box-shadow: 0 4px 15px rgba(76, 175, 80, 0.3);
            }
            .custom-file-upload:hover {
                background-color: #388e3c;
                transform: translateY(-2px);
            }
            #status {
                margin-top: 15px;
                font-weight: bold;
                font-size: 14px;
                color: #2e7d32;
            }
            #result {
                margin-top: 25px;
                text-align: left;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🌳 Kéregapó Varázskönyve 🌳</h1>
            <p>Üdvözöllek, kis barátom! Fotózz le egy szép növényt, virágot vagy erdei kincset, én pedig elmesélem a titkát!</p>
            
            <div class="file-input-wrapper">
                <label for="file-upload" class="custom-file-upload">
                    📸 Fénykép készítése / Kiválasztása
                </label>
                <input id="file-upload" type="file" accept="image/*" onchange="uploadImage(this)">
            </div>
            
            <div id="status"></div>
            <div id="result"></div>
        </div>

        <script>
            async function uploadImage(input) {
                if (!input.files || !input.files[0]) return;
                
                const statusDiv = document.getElementById('status');
                const resultDiv = document.getElementById('result');
                
                statusDiv.innerHTML = "⏳ Kéregapó épp lapozza a vaskos könyvet, kérlek várj...";
                resultDiv.innerHTML = "";
                
                const formData = new FormData();
                formData.append('file', input.files[0]);
                
                try {
                    const response = await fetch('/api/keregapo', {
                        method: 'POST',
                        body: formData
                    });
                    
                    if (response.ok) {
                        const htmlResult = await response.text();
                        resultDiv.innerHTML = htmlResult;
                        statusDiv.innerHTML = "✨ Kéregapó megtalálta a mesét!";
                        
                        // Automatikus hang lejátszás megkísérlése, miután betöltődött a HTML
                        setTimeout(() => {
                            const audioEl = resultDiv.querySelector('audio');
                            if (audioEl) {
                                audioEl.play().catch(e => console.log("Automatikus lejátszás blokkolva, kattints a lejátszás gombra."));
                            }
                        }, 500);
                    } else {
                        statusDiv.innerHTML = "❌ Ejha, valami hiba történt a varázslat során.";
                    }
                } catch (error) {
                    statusDiv.innerHTML = "❌ Sikertelen kapcsolódás Kéregapóhoz.";
                    console.error(error);
                }
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_tartalom)

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
        html_tartalom = f"""
        <div style="font-family: sans-serif; padding: 15px; line-height: 1.6; color: #333; max-width: 600px; margin: auto;">
            <h3 style="color: #2e7d32; margin-bottom: 5px;">📖 Kéregapó meséje:</h3>
            <p style="white-space: pre-wrap; font-size: 16px; background: #f1f8e9; padding: 15px; border-radius: 8px; border-left: 5px solid #81c784;">{mese_szoveg}</p>
            
            <div style="margin-top: 20px; background: #e8f5e9; padding: 15px; border-radius: 8px; text-align: center;">
                <p style="margin: 0 0 10px 0; font-weight: bold; color: #2e7d32;">🔊 Hallgasd meg Kéregapót:</p>
                <audio id="keregapo-audio" controls style="width: 100%; max-width: 400px;">
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
