from fastapi import FastAPI
import app.core.db.registry

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}
