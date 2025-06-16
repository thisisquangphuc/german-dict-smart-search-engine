from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import pandas as pd
from pathlib import Path
import random

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

def find_verb_form_in_sentence(sentence, verb_forms):
    """Find which verb form appears in the sentence and return it along with the sentence with the blank."""
    # Check both German and German example 2 columns
    german_texts = []
    if "German" in sentence and sentence["German"]:
        german_texts.append(sentence["German"].lower())
    if "German example 2" in sentence and sentence["German example 2"]:
        german_texts.append(sentence["German example 2"].lower())
    
    # Sort verb forms by length (longest first) to match longer forms before shorter ones
    sorted_forms = sorted([f for f in verb_forms if f], key=len, reverse=True)
    
    # Try each verb form
    for form in sorted_forms:
        form_lower = form.lower()
        
        # Check each German text
        for german_text in german_texts:
            if form_lower in german_text:
                # Create the blanked sentence by replacing the form with ____
                blanked_sentence = german_text.replace(form_lower, "____")
                return {
                    "form": form,
                    "blanked_sentence": blanked_sentence,
                    "original_sentence": german_text
                }
    
    return None

def find_matching_sentences(verb_forms, sentences):
    """Find all sentences that contain any of the verb forms."""
    matching_sentences = []
    print(f"\nVerb forms to search: {[f for f in verb_forms if f]}")
    
    for i, sentence in enumerate(sentences):
        blank_info = find_verb_form_in_sentence(sentence, verb_forms)
        if blank_info:
            matching_sentences.append({
                "sentence": sentence,
                "blank_info": blank_info,
                "sentence_index": i
            })
    
    print(f"Found {len(matching_sentences)} matching sentences")
    return matching_sentences

def load_verb_data():
    try:
        data_path = Path("resource/learn_vocab.xlsx")
        if not data_path.exists():
            print(f"Excel file not found at: {data_path.absolute()}")
            return [], []
        
        # Read Verb sheet (title in row 1, data in row 2)
        print("Reading Verb sheet...")
        verbs_df = pd.read_excel(data_path, sheet_name="Verb", skiprows=1)
        print(f"Verb sheet columns: {verbs_df.columns.tolist()}")
        
        verbs = []
        for _, row in verbs_df.iterrows():
            try:
                # Check if PP form is "Verb not found"
                pp_value = str(row.get("PP", "")).strip()
                has_perfect_form = pp_value and pp_value.lower() != "verb not found"
                
                verb = {
                    "meaning": str(row.get("Meaning", "")).strip() if pd.notna(row.get("Meaning")) else "",
                    "infinitive": str(row.get("Infinity", "")).strip() if pd.notna(row.get("Infinity")) else "",
                    "perfect": pp_value if has_perfect_form else "",
                    "ich": str(row.get("ich", "")).strip() if pd.notna(row.get("ich")) else "",
                    "du": str(row.get("du", "")).strip() if pd.notna(row.get("du")) else "",
                    "er": str(row.get("er", "")).strip() if pd.notna(row.get("er")) else "",
                    "sie": str(row.get("sie", "")).strip() if pd.notna(row.get("sie")) else "",
                    "es": str(row.get("es", "")).strip() if pd.notna(row.get("es")) else "",
                    "wir_sie": str(row.get("wir/Sie", "")).strip() if pd.notna(row.get("wir/Sie")) else "",
                    "ihr": str(row.get("ihr", "")).strip() if pd.notna(row.get("ihr")) else ""
                }
                # Only add verbs that have at least a meaning and infinitive form
                if verb["meaning"] and verb["infinitive"]:
                    verbs.append(verb)
            except Exception as e:
                print(f"Error processing verb row: {e}")
                continue
        
        # Read Sentences sheet (title in row 1, data in row 1)
        print("Reading Sentences sheet...")
        sentences_df = pd.read_excel(data_path, sheet_name="Sentences")
        print(f"Sentences sheet columns: {sentences_df.columns.tolist()}")
        # print(f"First row of Sentences sheet: {sentences_df.iloc[0].to_dict()}")
        
        sentences = []
        for _, row in sentences_df.iterrows():
            try:
                sentence = {
                    "English": str(row.get("English", "")).strip() if pd.notna(row.get("English")) else "",
                    "German": str(row.get("German", "")).strip() if pd.notna(row.get("German")) else "",
                    "German example 2": str(row.get("German example 2", "")).strip() if pd.notna(row.get("German example 2")) else ""
                }
                # Only add sentences that have at least one German text
                if sentence["German"] or sentence["German example 2"]:
                    sentences.append(sentence)
            except Exception as e:
                print(f"Error processing sentence row: {e}")
                continue
        
        print(f"Loaded {len(verbs)} verbs and {len(sentences)} sentences")
        # print("First few sentences:")
        # for i, sentence in enumerate(sentences[:3]):
        #     print(f"Sentence {i}:")
        #     print(f"  English: {sentence['English']}")
        #     print(f"  German: {sentence['German']}")
        #     print(f"  German example 2: {sentence['German example 2']}")
        return verbs, sentences
    except Exception as e:
        print(f"Error loading verb data: {e}")
        import traceback
        traceback.print_exc()
        return [], []

# Store data in memory
VERBS, SENTENCES = load_verb_data()

@router.get("/verb-quiz", response_class=HTMLResponse)
async def verb_quiz(request: Request):
    return templates.TemplateResponse("verb_quiz.html", {"request": request})

@router.get("/api/verb-quiz/next")
async def get_next_verb():
    if not VERBS:
        return {"error": "No verbs available"}
    
    # Select a random verb
    verb = random.choice(VERBS)
    print(f"\nSelected verb: {verb['meaning']} ({verb['infinitive']})")
    
    # Get all verb forms
    verb_forms = [
        verb["infinitive"],
        verb["perfect"],
        verb["ich"],
        verb["du"],
        verb["er"],
        verb["sie"],
        verb["es"],
        verb["wir_sie"],
        verb["ihr"]
    ]
    
    # Find matching sentences
    matching_sentences = find_matching_sentences(verb_forms, SENTENCES)
    
    # Select a random matching sentence if available
    selected_sentence = None
    if matching_sentences:
        selected = random.choice(matching_sentences)
        selected_sentence = {
            "english": selected["sentence"]["English"],
            "german": selected["sentence"]["German"],
            "blanked_sentence": selected["blank_info"]["blanked_sentence"],
            "correct_form": selected["blank_info"]["form"],
            "sentence_index": selected["sentence_index"]
        }
    else:
        print("No matching sentences found for this verb")
    
    return {
        "verb": verb,
        "sentence": selected_sentence,
        "has_perfect_form": bool(verb["perfect"] and verb["perfect"].strip())
    } 