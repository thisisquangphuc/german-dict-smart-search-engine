from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import pandas as pd
from pathlib import Path
import random

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

def load_nouns():
    try:
        data_path = Path("resource/learn_vocab.xlsx")
        print(f"Loading nouns from: {data_path.absolute()}")
        if not data_path.exists():
            print(f"File does not exist at: {data_path.absolute()}")
            return []
        
        # Read Excel file with explicit string handling
        print("Reading Excel file...")
        df = pd.read_excel(data_path, sheet_name="Noun", dtype=str)
        print(f"Found {len(df)} rows in the Noun sheet")
        
        nouns = []
        for index, row in df.iterrows():
            try:
                # Clean column names by stripping extra spaces
                noun = {
                    "singular": str(row["Noun (singular)"]).strip() if pd.notna(row["Noun (singular)"]) else "",
                    "gender": str(row["Gender"]).strip() if pd.notna(row["Gender"]) else "",
                    "article": str(row["Article"]).strip() if pd.notna(row["Article"]) else "",
                    "full_word": str(row["Full word"]).strip() if pd.notna(row["Full word"]) else "",
                    "plural": str(row["Plural"]).strip() if pd.notna(row["Plural"]) else "N/A",
                    "meaning": str(row["Meanning  "]).strip() if pd.notna(row["Meanning  "]) else "",
                    "example": str(row["Example"]).strip() if pd.notna(row["Example"]) else "No example available"
                }
                
                # Skip non-nouns (adjectives, adverbs, etc.)
                if noun["gender"] == "-" or noun["article"] == "":
                    print(f"Skipping row {index} as it's not a noun: {noun['singular']}")
                    continue
                
                # Only require essential fields
                required_fields = ["singular", "gender", "article", "full_word", "meaning"]
                if all(noun[field] for field in required_fields):
                    nouns.append(noun)
                else:
                    print(f"Skipping row {index} due to missing required fields: {noun}")
            except Exception as e:
                print(f"Error processing row {index}: {e}")
        
        print(f"Successfully loaded {len(nouns)} valid nouns")
        return nouns
    except Exception as e:
        print(f"Error loading nouns: {e}")
        return []

# Store nouns in memory
NOUNS = load_nouns()
print(f"Initialized with {len(NOUNS)} nouns")

@router.get("/noun-quiz", response_class=HTMLResponse)
async def noun_quiz(request: Request):
    return templates.TemplateResponse("noun_quiz.html", {"request": request})

@router.get("/api/noun-quiz/nouns")
async def get_nouns():
    try:
        # Create a new shuffled copy for each request
        nouns = NOUNS.copy()
        random.shuffle(nouns)
        return nouns
    except Exception as e:
        print(f"Error serving nouns: {e}")
        return [] 