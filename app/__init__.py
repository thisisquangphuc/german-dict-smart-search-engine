from fastapi import FastAPI

app = FastAPI()

# Import and include routers
from .routes.quiz import quiz_bp
app.include_router(quiz_bp) 