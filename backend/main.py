from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Duolingo Clone Backend is running"}

@app.get("/health")
def health_check():
    return {"status": "ok"}