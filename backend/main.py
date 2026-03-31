"""FastAPI backend for the Debate system."""

import asyncio
import json
import uuid
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from . import storage
from .debate import (
    run_full_debate,
    stage1_opening_arguments,
    stage2_rebuttal_round,
    stage3_final_statements,
    stage4_judge_evaluation,
)
from .title import generate_debate_title

app = FastAPI(title="Debate API")

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class StartDebateRequest(BaseModel):
    """Request to start a debate with a topic."""

    topic: str


class DebateMetadata(BaseModel):
    """Debate metadata for list view."""

    id: str
    created_at: str
    title: str
    topic: Optional[str]
    message_count: int


class Debate(BaseModel):
    """Full debate with all messages."""

    id: str
    created_at: str
    title: str
    topic: Optional[str]
    messages: List[Dict[str, Any]]


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "Debate API"}


@app.get("/api/debates", response_model=List[DebateMetadata])
async def list_debates():
    """List all debates (metadata only)."""
    return storage.list_debates()


@app.post("/api/debates", response_model=Debate)
async def create_debate():
    """Create a new empty debate session."""
    debate_id = str(uuid.uuid4())
    debate = storage.create_debate(debate_id)
    return debate


@app.get("/api/debates/{debate_id}", response_model=Debate)
async def get_debate(debate_id: str):
    """Get a specific debate with all its messages."""
    debate = storage.get_debate(debate_id)
    if debate is None:
        raise HTTPException(status_code=404, detail="Debate not found")
    return debate


@app.post("/api/debates/{debate_id}/start")
async def start_debate(debate_id: str, request: StartDebateRequest):
    """
    Start a debate with the given topic and run the full 4-stage debate process.
    Returns the complete debate result.
    """
    debate = storage.get_debate(debate_id)
    if debate is None:
        raise HTTPException(status_code=404, detail="Debate not found")

    # Store topic
    storage.add_debate_topic(debate_id, request.topic)

    # Generate title in parallel
    title_task = asyncio.create_task(generate_debate_title(request.topic))

    # Run the full debate
    stage1, stage2, stage3, stage4 = await run_full_debate(request.topic)

    # Save results
    storage.add_debate_result_message(debate_id, stage1, stage2, stage3, stage4)

    # Update title
    title_base = await title_task
    title = f"Debate: {title_base}"
    storage.update_debate_title(debate_id, title)

    return {
        "stage1": stage1,
        "stage2": stage2,
        "stage3": stage3,
        "stage4": stage4,
        "title": title,
    }


@app.post("/api/debates/{debate_id}/start/stream")
async def start_debate_stream(debate_id: str, request: StartDebateRequest):
    """
    Start a debate and stream results as each stage completes (Server-Sent Events).
    """
    debate = storage.get_debate(debate_id)
    if debate is None:
        raise HTTPException(status_code=404, detail="Debate not found")

    async def event_generator():
        try:
            # Store topic
            storage.add_debate_topic(debate_id, request.topic)

            # Start title generation in parallel
            title_task = asyncio.create_task(generate_debate_title(request.topic))

            # Stage 1 – Opening Arguments
            yield f"data: {json.dumps({'type': 'stage1_start'})}\n\n"
            stage1 = await stage1_opening_arguments(request.topic)
            yield f"data: {json.dumps({'type': 'stage1_complete', 'data': stage1})}\n\n"

            # Stage 2 – Rebuttal Round
            yield f"data: {json.dumps({'type': 'stage2_start'})}\n\n"
            stage2 = await stage2_rebuttal_round(request.topic, stage1)
            yield f"data: {json.dumps({'type': 'stage2_complete', 'data': stage2})}\n\n"

            # Stage 3 – Final Statements
            yield f"data: {json.dumps({'type': 'stage3_start'})}\n\n"
            stage3 = await stage3_final_statements(request.topic, stage1, stage2)
            yield f"data: {json.dumps({'type': 'stage3_complete', 'data': stage3})}\n\n"

            # Stage 4 – Judge Evaluation
            yield f"data: {json.dumps({'type': 'stage4_start'})}\n\n"
            stage4 = await stage4_judge_evaluation(request.topic, stage1, stage2, stage3)
            yield f"data: {json.dumps({'type': 'stage4_complete', 'data': stage4})}\n\n"

            # Save complete result
            storage.add_debate_result_message(debate_id, stage1, stage2, stage3, stage4)

            # Title
            title_base = await title_task
            title = f"Debate: {title_base}"
            storage.update_debate_title(debate_id, title)
            yield f"data: {json.dumps({'type': 'title_complete', 'data': {'title': title}})}\n\n"

            yield f"data: {json.dumps({'type': 'complete'})}\n\n"

        except Exception as e:
            print(f"Debate stream error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': 'An internal error occurred during the debate.'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
