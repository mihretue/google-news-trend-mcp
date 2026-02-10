#!/usr/bin/env python3

from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/test")
def test():
    return {"status": "working"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)