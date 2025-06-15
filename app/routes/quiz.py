import os
import json
from datetime import datetime
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path

quiz_bp = APIRouter(prefix="/api/quiz", tags=["quiz"])

def get_progress_file_path():
    # Use environment variable for Docker volume path, fallback to local path
    base_path = os.getenv('QUIZ_DATA_PATH', os.path.join(os.path.dirname(__file__), '..', 'data'))
    return os.path.join(base_path, 'quiz_progress.json')

def ensure_progress_file():
    progress_file = get_progress_file_path()
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(progress_file), exist_ok=True)
        
        # Create file with empty JSON object if it doesn't exist
        if not os.path.exists(progress_file):
            with open(progress_file, 'w') as f:
                json.dump({}, f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error ensuring progress file: {str(e)}")

def load_progress():
    progress_file = get_progress_file_path()
    try:
        ensure_progress_file()
        with open(progress_file, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading progress: {str(e)}")

def save_progress(progress):
    progress_file = get_progress_file_path()
    try:
        ensure_progress_file()
        with open(progress_file, 'w') as f:
            json.dump(progress, f, indent=2)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving progress: {str(e)}")

@quiz_bp.get("/progress")
async def get_progress():
    try:
        progress = load_progress()
        return progress
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@quiz_bp.post("/progress")
async def update_progress(data: dict):
    if not data or 'date' not in data or 'correct' not in data or 'total' not in data:
        raise HTTPException(status_code=400, detail="Invalid data")

    try:
        progress = load_progress()
        progress[data['date']] = {
            'correct': data['correct'],
            'total': data['total']
        }
        save_progress(progress)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ... existing code ... 