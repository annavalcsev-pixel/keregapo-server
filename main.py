import io
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import Response, HTMLResponse
from PIL import Image
from google import genai
import edge_tts

app = FastAPI()
client = genai.Client()

@app.get("/", response_class=HTMLResponse)
async def fooldal():
    return """
    <html><body>
        <button onclick="document.getElementById('file').click()">FOTÓZÁS</button>
        <input type="file" id="file" accept="image/*" capture="environment" style="display:none" onchange="upload(this)">
        <script>
            async function upload(i) {
                const fd = new FormData(); fd.append('file', i.files[0]);
                const r = await fetch('/api/meselj', {method: 'POST', body: fd});
                if(r.ok) { 
                    const b = await r.blob(); 
                    new Audio(URL.createObjectURL(b)).play(); 
                } else { alert('Hiba!'); }
            }
        </script>
    </body></html>
    """

@app.post("/api/meselj")
async def meselj(file: UploadFile = File(...)):
    img = Image.open(io.BytesIO(await file.read())).convert("RGB")
    res = client.models.generate_content(model='gemini-1.5-flash', contents=[img, "Mondj egy mondatot a képről."])
    
    communicate = edge_tts.Communicate(res.text, "hu-HU-TamasNeural")
    audio_io = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio": audio_io.write(chunk["data"])
    return Response(audio_io.getvalue(), media_type="audio/mpeg")
