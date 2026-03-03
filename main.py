from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Welcome to Ginja Claims"}

@app.post("/claims")
async def submit_claim():
    return {"message": "Claim created"}

@app.get("/claims/{id}")
async def get_claim(id: int):
    """Retrieve claim status"""
    return {"id": id}