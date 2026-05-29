"""
FastAPI server for exposing agent endpoints to the frontend
"""

import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

from agents.crewai_agents import analyze_region, answer_traveler_question

app = FastAPI(title="Airspace Copilot API")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TravelerQuery(BaseModel):
    identifier: str
    question: str

class RegionQuery(BaseModel):
    region: str = "region1"

@app.get("/")
def root():
    return {
        "service": "Airspace Copilot API",
        "endpoints": {
            "/ops/analyze": "POST - Analyze a region (body: {region: 'region1'})",
            "/traveler/query": "POST - Query about a flight (body: {identifier: 'THY4KZ', question: 'Where is my flight?'})",
            "/health": "GET - Health check"
        }
    }

@app.get("/health")
def health():
    return {"status": "ok", "service": "airspace-copilot-api"}

@app.post("/ops/analyze")
def ops_analyze(query: RegionQuery):
    """
    Analyze a region and return operations summary.
    """
    try:
        result = analyze_region(query.region)
        return {
            "success": True,
            "region": query.region,
            "summary": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/traveler/query")
def traveler_query(query: TravelerQuery):
    """
    Answer a traveler's question about their flight.
    """
    try:
        result = answer_traveler_question(query.identifier, query.question)
        return {
            "success": True,
            "identifier": query.identifier,
            "answer": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("API_PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)

