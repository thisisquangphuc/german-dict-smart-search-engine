# German Dictionary Service with Caching

A FastAPI-based German dictionary service that uses the PONS API with local caching to minimize API calls.

## Features

- German-English dictionary lookup using PONS API
- Local SQLite caching to minimize API calls
- Case-sensitive word handling
- Automatic cache updates and access tracking
- Fallback to cached results when API quota is reached

## Setup

1. Clone the repository
2. Create a `.env` file in the root directory with your PONS API key:
   ```
   PONS_API_KEY=your_api_key_here
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the application:
   ```bash
   uvicorn app.main:app --reload
   ```

## API Usage

### Dictionary Lookup

```
GET /api/dict/pons?word=Haus
```

Response:
```json
{
    "word": "Haus",
    "result": "...",
    "is_cached": false
}
```

## Docker Support

To run with Docker:

1. Build the image:
   ```bash
   docker build -t german-dict .
   ```

2. Run the container:
   ```bash
   docker run -p 8000:8000 -e PONS_API_KEY=your_api_key_here german-dict
   ```

## Notes

- The service maintains a SQLite database in `app/data/pons_cache.db`
- Cache entries include word, result, creation time, search count, and last access time
- Case sensitivity is preserved (e.g., "Haus" and "haus" are treated as different words)
