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
import pandas as pd
from pathlib import Path
import random
import time

# Load environment variables from .env file
load_dotenv()

app = FastAPI()
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Import and include routers
from .routes.quiz import quiz_bp
from .routes.verb_quiz import router as verb_quiz_router
from .routes.dictionary import router as dictionary_router
from .database import init_db

# Initialize database
init_db()

app.include_router(quiz_bp)
app.include_router(verb_quiz_router)
app.include_router(dictionary_router)

PONS_API_KEY = os.getenv("PONS_API_KEY")

# Load quiz sentences
def load_quiz_sentences():
    try:
        data_path = Path("resource/learn_vocab.xlsx")
        if not data_path.exists():
            return []
        
        # Read Excel file with explicit string handling
        df = pd.read_excel(data_path, sheet_name="Sentences", dtype=str)
        sentences = []
        
        for _, row in df.iterrows():
            # Convert values to strings and handle NaN/None values
            german = str(row["German"]).strip() if pd.notna(row["German"]) else ""
            english = str(row["English"]).strip() if pd.notna(row["English"]) else ""
            
            # Ensure proper encoding of umlauts
            german = german.encode('utf-8').decode('utf-8')
            english = english.encode('utf-8').decode('utf-8')
            
            # Only add sentences where both German and English are non-empty
            if german and english:
                sentences.append({
                    "german": german,
                    "english": english
                })
        
        return sentences
    except Exception as e:
        print(f"Error loading quiz sentences: {e}")
        return []

# Store base sentences in memory
BASE_SENTENCES = load_quiz_sentences()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/quiz", response_class=HTMLResponse)
async def quiz(request: Request):
    return templates.TemplateResponse("quiz.html", {"request": request})

@app.get("/api/quiz/sentences")
async def get_quiz_sentences():
    try:
        # Create a new shuffled copy for each request
        sentences = BASE_SENTENCES.copy()
        random.shuffle(sentences)
        return JSONResponse(
            content=sentences,
            media_type="application/json; charset=utf-8"
        )
    except Exception as e:
        print(f"Error serving quiz sentences: {e}")
        return JSONResponse(content=[], status_code=500)

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
    verb_conjugations = {
        "präsens": [],
        "präteritum": [],
        "imperativ": [],
        "konjunktiv_i": [],
        "konjunktiv_ii": [],
        "infinitiv": [],
        "partizip": []
    }

    if translation_span:
        # Extract the text, removing any HTML tags within the span
        translation_text = translation_span.get_text(separator=", ")
        translation_text = translation_text.strip()
        translation_text = ", ".join(filter(None, translation_text.split(", ")))
    
        # Find verb conjugations from tables
        conjugation_tables = soup.find_all("div", class_="vTbl")
        for table_div in conjugation_tables:
            heading = table_div.find("h2", class_="wG")
            if heading:
                tense = heading.get_text(strip=True).lower()
                # Map the tense to our standardized keys
                tense_key = None
                if "präsens" in tense:
                    tense_key = "präsens"
                elif "präteritum" in tense:
                    tense_key = "präteritum"
                elif "partizip" in tense:
                    tense_key = "partizip"
                
                if tense_key:
                    # Get the table
                    table = table_div.find("table")
                    if table:
                        conjugations = []
                        rows = table.find_all("tr")
                        for row in rows:
                            cells = row.find_all("td")
                            if len(cells) >= 2:
                                pronoun = cells[0].get_text(strip=True)
                                verb = cells[1].get_text(strip=True)
                                conjugations.append(f"{pronoun} {verb}")
                            elif len(cells) == 1:
                                verb = cells[0].get_text(strip=True)
                                conjugations.append(verb)
                        
                        if conjugations:
                            verb_conjugations[tense_key] = conjugations
                            print(f"Found {tense_key} conjugations: {conjugations}")  # Debug print

        print(verb_conjugations)
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

    # Verify if the image exists
    try:
        response = requests.head(dynamic_image_url)
        if response.status_code != 200:
            dynamic_image_url = None
            print(f"Image not found at URL: {dynamic_image_url}")
    except Exception as e:
        dynamic_image_url = None
        print(f"Error checking image URL: {e}")

    # Search for MP3 sound URL - look for any MP3 file containing the word
    sound_match = re.search(f'https://www\.verbformen\.de/deklination/substantive/grundform/[^"]+\.mp3', html)
    word_sound = sound_match.group(0) if sound_match else None
    print(word_sound)
    return JSONResponse(content={
        "word": encoded_word,
        "pons": {},
        "verbformen_html": f'<a href="{verbformen_url}">{verbformen_url}</a>',
        "verb_image_url": dynamic_image_url,
        "translation": translation_text,
        "beispiele_list": beispiele_list,
        "article": article,
        "word_sound": word_sound,
        "verb_conjugations": verb_conjugations
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