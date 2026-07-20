import io
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import Response, HTMLResponse
from PIL import Image
from google import genai
import edge_tts
import os

app = FastAPI()

# Az API kulcsot a Render Environment változóiból olvassa
api_key = os.environ.get("GOOGLE_API_KEY")
client = genai.Client(api_key=api_key)

@app.get("/", response_class=HTMLResponse)
async def fooldal():
    return """
    <html>
        <body>
            <button onclick="document.getElementById('file').click()" style="padding:20px; font-size:20px;">FOTÓZÁS</button>
            <input type="file" id="file" accept="image/*" capture="environment" style="display:none" onchange="upload(this)">
            <script>
                async function upload(i) {
                    const fd = new FormData(); 
                    fd.append('file', i.files[0]);
                    try {
                        const r = await fetch('/api/meselj', {method: 'POST', body: fd});
                        if(r.ok) { 
                            const b = await r.blob(); 
                            new Audio(URL.createObjectURL(b)).play(); 
                        } else { 
                            const err = await r.text();
                            alert('Hiba történt: ' + err); 
                        }
                    } catch(e) { alert('Hálózati hiba: ' + e); }
                }
            </script>
        </body>
    </html>
    """

@app.post("/api/meselj")
async def meselj(file: UploadFile = File(...)):
    try:
        print("--- Fájl fogadva ---")
        contents = await file.read()
        img = Image.open(io.BytesIO(contents)).convert("RGB")
        print("--- Kép feldolgozva, Gemini hívása ---")
        
        # Gemini hívás
        res = client.models.generate_content(
            model='gemini-1.5-flash', 
            contents=[img, "Mondj egy rövid mondatot a képről."]
        )
        print(f"--- Gemini válasz: {res.text} ---")
        
        # TTS generálás
        communicate = edge_tts.Communicate(res.text, "hu-HU-TamasNeural")
        audio_io = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio": audio_io.write(chunk["data"])
        
        print("--- Hang sikeresen generálva ---")
        return Response(audio_io.getvalue(), media_type="audio/mpeg")
    
    except Exception as e:
        print(f"!!! HIBA TÖRTÉNT: {str(e)} !!!")
        return Response(str(e), status_code=500)
