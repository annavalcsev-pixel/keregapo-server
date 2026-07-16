# We will create a Python Flet script. Flet allows us to build cross-platform mobile apps using Python.
# Since we need to deliver a complete code file to the user, let's write a beautifully designed Python Flet code that builds this mobile app interface.
# The user wants to see Kéregapó, a thick book, an forest background, a magnifying glass icon, and have it connect to their Render API.
# Let's generate a highly detailed and commented Python file that they can run and package.
# We will save this as `app.py`.

app_code = """# -*- coding: utf-8 -*-
import flet as ft
import requests
import base64
import io

# A Render szerverünk címe (Ezt írd át a saját Render címedre, pl: 'https://keregapo-szerver.onrender.com')
RENDER_API_URL = "https://keregapo-server.onrender.com/" # Lokális teszthez, vagy a Renderes HTTPS címed

def main(page: ft.Page):
    page.title = "Kéregapó és a Varázskönyv"
    # Mobil képernyő méretre tervezünk
    page.window_width = 390
    page.window_height = 844
    page.padding = 0
    page.spacing = 0
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.START

    # Háttérképek és grafikai elemek URL-jei (behelyettesíthető helyi fájlokkal is)
    # Most gyönyörű, hangulatos illusztrációkat adunk meg alapértelmezettként
    FOREST_BG = "https://images.unsplash.com/photo-1448375240586-882707db888b?auto=format&fit=crop&q=80&w=1000"
    
    # Kéregapó békésen pihen a könyve felett (AI generált jellegű kép)
    KEREGAPO_RESTING = "https://images.unsplash.com/photo-1518156677180-95a2893f3e9f?auto=format&fit=crop&q=80&w=400"
    # Kéregapó lázgasan lapozza a könyvet keresés közben
    KEREGAPO_SEARCHING = "https://images.unsplash.com/photo-1457369804613-52c61a468e7d?auto=format&fit=crop&q=80&w=400"

    # Audio lejátszó a hang megszólaltatásához
    audio_player = ft.Audio(
        autoplay=True,
        volume=1.0,
    )
    page.overlay.append(audio_player)

    # 1. Háttér és felület struktúrája
    # Kéregapó képe
    keregapo_img = ft.Image(
        src=KEREGAPO_RESTING,
        width=180,
        height=180,
        fit=ft.ImageFit.CONTAIN,
        border_radius=ft.border_radius.all(90),
    )

    # A varázskönyv szöveges része
    story_text = ft.Text(
        value="Üdvözöllek, kis barátom! Koppints a lenti nagyítóra, fotózz le egy szép növényt, én pedig kikeresem neked a titkos könyvemből, és elmesélem a történetét!",
        size=15,
        color=ft.colors.BROWN_900,
        italic=True,
        text_align=ft.TextAlign.CENTER,
    )

    # Kényelmes könyv-szerű kártya a szövegnek
    book_card = ft.Container(
        content=ft.Column(
            [
                ft.Text("✨ KÉREGAPÓ VARÁZSKÖNYVE ✨", size=14, weight=ft.FontWeight.BOLD, color=ft.colors.GREEN_800),
                ft.Divider(color=ft.colors.BROWN_300, height=10),
                ft.Container(content=story_text, padding=10),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        bgcolor=ft.colors.with_opacity(0.9, ft.colors.AMBER_50), # Sárgás, pergamen-szerű szín
        padding=20,
        border_radius=15,
        border=ft.border.all(2, ft.colors.BROWN_400),
        width=320,
        height=260,
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=15,
            color=ft.colors.with_opacity(0.4, ft.colors.BLACK),
            offset=ft.Offset(0, 5),
        ),
    )

    # Töltőcsík / státusz jelző
    status_indicator = ft.ProgressRing(visible=False, color=ft.colors.GREEN_700, width=40, height=40)
    status_text = ft.Text(value="", size=14, color=ft.colors.WHITE, weight=ft.FontWeight.BOLD)

    # API hívás feldolgozása a fotó után
    def on_file_selected(e: ft.FilePickerResultEvent):
        if not e.files:
            return
        
        # UI átállítása: Kéregapó lapozni kezd!
        keregapo_img.src = KEREGAPO_SEARCHING
        status_indicator.visible = True
        status_text.value = "Kéregapó épp lapozza a vaskos könyvet..."
        story_text.value = "Lássuk csak... melyik növény is lehet ez? Az öreg lapok suttognak..."
        page.update()

        try:
            # Kiválasztott kép beolvasása
            selected_file = e.files[0]
            with open(selected_file.path, "rb") as image_file:
                image_bytes = image_file.read()

            # Küldés a FastAPI szervernek
            files = {"file": (selected_file.name, image_bytes, "image/jpeg")}
            response = requests.post(RENDER_API_URL, files=files)

            if response.status_code == 200:
                # Mivel HTML-t ad vissza a szerverünk, de mi JSON-t vagy sima szöveget szeretnénk a mobilon:
                # (A korábbi verziókban visszakapott mese és hang a legjobb)
                # Ahhoz, hogy az app tökéletesen játssza le, a szervernek vissza kellene adnia a hangfájl URL-jét vagy Base64-ét.
                # Ebben az appban a letöltési végpontunkat (/api/keregapo/hang.mp3) fogjuk meghívni az audio lejátszóval!
                
                # HTML válaszból kiszedjük a mese szövegét a bemutató kedvéért, de a legegyszerűbb, ha az app
                # közvetlenül a szerver hang-végpontját indítja el:
                audio_player.src = f"{RENDER_API_URL.replace('/api/keregapo', '')}/api/keregapo/hang.mp3"
                
                # Frissítsük Kéregapó szövegét (Itt most egy mintaszöveggel helyettesítjük, amit a szerver küldött)
                # Ha a szerver HTML-t ad vissza, kiszedhetjük a <p> tagek közül a mesét:
                html_resp = response.text
                import re
                p_content = re.findall(r'<p[^>]*>(.*?)</p>', html_resp, re.DOTALL)
                if p_content:
                    story_text.value = p_content[0].replace("<br>", "\\n").strip()
                else:
                    story_text.value = "Kikeresem neked a könyvemből, figyelj csak!"

                # Hang lejátszás indítása
                audio_player.play()

            else:
                story_text.value = f"Ejha, pici porszem került a gépezetbe! (Kód: {response.status_code})"

        except Exception as ex:
            story_text.value = f"Kéregapó eltévedt az erdőben: {str(ex)}"
        
        # UI visszaállítása: Kéregapó megnyugszik, elmeséli a talált történetet
        keregapo_img.src = KEREGAPO_RESTING
        status_indicator.visible = False
        status_text.value = ""
        page.update()

    # File picker (Fényképező/Galéria megnyitója)
    file_picker = ft.FilePicker(on_result=on_file_selected)
    page.overlay.append(file_picker)

    # Nagyító Gomb (Fotó készítése)
    magnifier_button = ft.Container(
        content=ft.IconButton(
            icon=ft.icons.SEARCH_SHARP,
            icon_color=ft.colors.WHITE,
            icon_size=40,
            tooltip="Fényképező megnyitása",
            on_click=lambda _: file_picker.pick_files(allow_multiple=False, file_type=ft.FilePickerFileType.IMAGE),
        ),
        width=80,
        height=80,
        border_radius=40,
        bgcolor=ft.colors.GREEN_700,
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=10,
            color=ft.colors.with_opacity(0.5, ft.colors.BLACK),
            offset=ft.Offset(0, 4),
        ),
    )

    # Fő elrendezés összerakása egy gyönyörű erdei háttérkonténerben
    main_layout = ft.Container(
        content=ft.Column(
            [
                ft.Container(height=40), # Felső margó
                # Kéregapó portréja
                keregapo_img,
                ft.Container(height=15),
                # Varázskönyv kártya
                book_card,
                ft.Container(height=20),
                # Betöltés jelzők
                status_indicator,
                status_text,
                ft.Container(height=10),
                # Nagyító gomb felirata
                ft.Text("Koppints a nagyítóra a vizsgálathoz!", color=ft.colors.WHITE, size=14, weight=ft.FontWeight.BOLD),
                ft.Container(height=5),
                # Nagyító gomb
                magnifier_button,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
        ),
        width=390,
        height=844,
        image_src=FOREST_BG,
        image_fit=ft.ImageFit.COVER,
        padding=20,
    )

    page.add(main_layout)

# Indítás
if __name__ == "__main__":
    ft.app(target=main)
"""

with open("app.py", "w", encoding="utf-8") as f:
    f.write(app_code)

print("Generated app.py successfully!")