#!/usr/bin/env python3

from fastapi import FastAPI
import uvicorn

# Test imports one by one
try:
    from app.core.config import settings
    print("✅ Settings imported successfully")
except Exception as e:
    print(f"❌ Settings import failed: {e}")
    exit(1)

try:
    from app.routers import health
    print("✅ Health router imported successfully")
except Exception as e:
    print(f"❌ Health router import failed: {e}")
    exit(1)

try:
    from app.routers import auth
    print("✅ Auth router imported successfully")
except Exception as e:
    print(f"❌ Auth router import failed: {e}")
    exit(1)

try:
    from app.routers import chat
    print("✅ Chat router imported successfully")
except Exception as e:
    print(f"❌ Chat router import failed: {e}")
    exit(1)

app = FastAPI(title="Test App")

@app.get("/")
def read_root():
    return {"status": "working", "environment": settings.environment}

# Include routers
app.include_router(health.router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)