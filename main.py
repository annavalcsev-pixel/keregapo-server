import io
import os
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import Response, HTMLResponse
from PIL import Image
from google import genai
import edge_tts

app = FastAPI()

# API kulcs inicializálása
api_key = os.environ.get("GOOGLE_API_KEY")
client = genai.Client(api_key=api_key)

@app.get("/", response_class=HTMLResponse)
async def fooldal():
    return """
    <html>
        <body style="background:#2d1b0d; color:white; text-align:center; font-family:sans-serif;">
            <h1>Természetbúvár Manó</h1>
            <button onclick="document.getElementById('file').click()" style="padding:20px 40px; font-size:20px; border-radius:10px; cursor:pointer;">FOTÓZÁS</button>
            <input type="file" id="file" accept="image/*" capture="environment" style="display:none" onchange="upload(this)">
            <script>
                async function upload(i) {
                    const fd = new FormData(); 
                    fd.append('file', i.files[0]);
                    alert('Manó vizsgálja a kincset...');
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
        contents = await file.read()
        img = Image.open(io.BytesIO(contents)).convert("RGB")
        
        # Ha a gemini-1.5-flash nem működik, írd át a modell nevét a korábban működőre!
        res = client.models.generate_content(
            model='gemini-3.1-flash-lite', 
            contents=[img, "Légy egy természetvédő manó. Mondj egy rövid, 2 mondatos, érdekes tanítást a képen látható dologról, amivel a gyerekek tanulhatnak és tisztelhetik a természetet."]
        )
        
        communicate = edge_tts.Communicate(res.text, "hu-HU-TamasNeural")
        audio_io = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio": audio_io.write(chunk["data"])
        
        return Response(audio_io.getvalue(), media_type="audio/mpeg")
    
    except Exception as e:
        print(f"HIBA: {str(e)}")
        return Response(str(e), status_code=500)
