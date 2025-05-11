import re
import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import requests
import httpx
import json
from urllib.parse import quote
from bs4 import BeautifulSoup
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam

# Load environment variables from .env file
load_dotenv()

app = FastAPI()
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

PONS_API_KEY = os.getenv("PONS_API_KEY")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/lookup")
async def lookup(word: str):
    encoded_word = quote(word)
    verbformen_url = f"https://www.verbformen.de/?w={encoded_word}"
    html = requests.get(verbformen_url).text

    # Parse HTML with BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')

    # Extract grammatical article from Nominativ row
    article = ""
    nominativ_row = soup.find("th", title="Nominativ")
    if nominativ_row:
        parent_row = nominativ_row.find_parent("tr")
        if parent_row:
            cells = parent_row.find_all("td")
            if len(cells) >= 2:
                article = cells[0].get_text(strip=True)

    # Find the span with lang="en" tag containing the translation
    translation_span = soup.find('span', lang='en')
    
    translation_text = ""
    beispiele_list = []

    if translation_span:
        # Extract the text, removing any HTML tags within the span
        translation_text = translation_span.get_text(separator=", ")

        # Clean up extra spaces and unwanted symbols (if necessary)
        translation_text = translation_text.strip()
        
        # Remove empty strings
        translation_text = ", ".join(filter(None, translation_text.split(", ")))
    
        heading = soup.find("h2", string="Beispiele")

        if heading:
            beispiele_section = heading.find_next("ul")

            if beispiele_section:
                list_items = beispiele_section.find_all("li")
                for li in list_items:
                    # Extract only the German text before the <br> tag
                    german_html = ""
                    for content in li.contents:
                        if content.name == 'br':
                            break
                        if isinstance(content, str):
                            german_html += content
                        else:
                            german_html += str(content)
                    german_text = german_html.strip()

                    # Extract the English translation from the img title or the span after <br>
                    translation_span = li.find("br")
                    english_translation = ""
                    if translation_span and translation_span.next_sibling:
                        following_span = translation_span.find_next("span")
                        if following_span:
                            english_translation = following_span.get_text(strip=True)

                    beispiele_list.append({
                        "de": german_text,
                        "en": english_translation
                    })

            else:
                print("No <ul> with examples found.")
        else:
            print("No 'Beispiele' section found.")
        
    
    # Simple image URL logic based on known pattern
    base_image_url = f"https://www.verbformen.de/deklination/substantive/{encoded_word}.png"

    # Try to find the actual image URL in the HTML using the requested pattern
    match = re.search(r'https://www\.verbformen\.de/deklination/substantive/[^"]+\.png', html)
    dynamic_image_url = match.group(0) if match else base_image_url

    return JSONResponse(content={
        "word": encoded_word,
        "pons": {},
        "verbformen_html": f'<a href="{verbformen_url}">{verbformen_url}</a>',
        "verb_image_url": dynamic_image_url,
        "translation": translation_text,
        "beispiele_list": beispiele_list,
        "article": article,
    })

@app.get("/api/dict/pons")
async def lookup(word: str):
    encoded_word = quote(word)
    
    # PONS API endpoint
    pons_url = f"https://api.pons.com/v1/dictionary?q={encoded_word}&l=deen&language=en&in=de"

    headers = {
        "X-Secret": PONS_API_KEY  # API key for authentication
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(pons_url, headers=headers)

    if response.status_code == 200:
        data = response.json()

        if isinstance(data, list) and len(data) > 0:
            hits = data[0].get("hits", [])
        else:
            hits = []

        all_translations = []

        for hit in hits:
            # Check if roms exists
            roms = hit.get("roms", [])
            if roms:
                for rom in hit.get("roms", []):
                    for arab in rom.get("arabs", []):
                        for translation in arab.get("translations", []):
                            source = translation.get("source", "")
                            target = translation.get("target", "")
                            all_translations.append({"source": source, "target": target})
            else:
                # get direct source and target from hits
                source = hit.get("source", "")
                target = hit.get("target", "")
                all_translations.append({"source": source, "target": target})
                            
        result = {
            "word": encoded_word,
            "translations": all_translations,
            "verb_image_url": f"https://www.verbformen.de/deklination/substantive/{encoded_word.capitalize()}.png"
        }

        return JSONResponse(content=result)
    else:
        return JSONResponse(content={"error": "Failed to fetch data from PONS API"}, status_code=500)
    

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
@app.get("/api/genai/examples")
@app.get("/api/genai/examples")
async def generate_examples(word: str):
    prompt = (
        f"Give me 5 short daily-use example sentences in German using the word '{word}'. "
        "Each sentence should be followed by its English translation. "
        "Return the result as a JSON array like: "
        "[{\"de\": \"German sentence\", \"en\": \"English translation\"}]"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )

        # Extract and parse content
        content = response.choices[0].message.content
        import json
        examples = json.loads(content)

        return {"examples": examples}

    except Exception as e:
        return {"error": str(e)}