from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
from threading import Thread

app = FastAPI()

@app.get("/health")
async def health_check():
    return JSONResponse({"status": "healthy"})

def run_health_server():
    """Run the health check server"""
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="error")
