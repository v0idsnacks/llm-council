"""FastAPI backend for LLM Council."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any
import uuid
import json
import asyncio

from . import storage
from .council import run_full_council, generate_conversation_title, stage1_collect_responses, stage2_collect_rankings, stage3_synthesize_final, calculate_aggregate_rankings
from .debate import (
    run_full_debate,
    stage1_opening_arguments,
    stage2_rebuttal_round,
    stage3_final_statements,
    stage4_judge_evaluation,
)

app = FastAPI(title="LLM Council API")

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CreateConversationRequest(BaseModel):
    """Request to create a new conversation."""
    pass


class SendMessageRequest(BaseModel):
    """Request to send a message in a conversation."""
    content: str


class ConversationMetadata(BaseModel):
    """Conversation metadata for list view."""
    id: str
    created_at: str
    title: str
    message_count: int


class Conversation(BaseModel):
    """Full conversation with all messages."""
    id: str
    created_at: str
    title: str
    messages: List[Dict[str, Any]]


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "LLM Council API"}


@app.get("/api/conversations", response_model=List[ConversationMetadata])
async def list_conversations():
    """List all conversations (metadata only)."""
    return storage.list_conversations()


@app.post("/api/conversations", response_model=Conversation)
async def create_conversation(request: CreateConversationRequest):
    """Create a new conversation."""
    conversation_id = str(uuid.uuid4())
    conversation = storage.create_conversation(conversation_id)
    return conversation


@app.get("/api/conversations/{conversation_id}", response_model=Conversation)
async def get_conversation(conversation_id: str):
    """Get a specific conversation with all its messages."""
    conversation = storage.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@app.post("/api/conversations/{conversation_id}/message")
async def send_message(conversation_id: str, request: SendMessageRequest):
    """
    Send a message and run the 3-stage council process.
    Returns the complete response with all stages.
    """
    # Check if conversation exists
    conversation = storage.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Check if this is the first message
    is_first_message = len(conversation["messages"]) == 0

    # Add user message
    storage.add_user_message(conversation_id, request.content)

    # If this is the first message, generate a title
    if is_first_message:
        title = await generate_conversation_title(request.content)
        storage.update_conversation_title(conversation_id, title)

    # Run the 3-stage council process
    stage1_results, stage2_results, stage3_result, metadata = await run_full_council(
        request.content
    )

    # Add assistant message with all stages
    storage.add_assistant_message(
        conversation_id,
        stage1_results,
        stage2_results,
        stage3_result
    )

    # Return the complete response with metadata
    return {
        "stage1": stage1_results,
        "stage2": stage2_results,
        "stage3": stage3_result,
        "metadata": metadata
    }


@app.post("/api/conversations/{conversation_id}/message/stream")
async def send_message_stream(conversation_id: str, request: SendMessageRequest):
    """
    Send a message and stream the 3-stage council process.
    Returns Server-Sent Events as each stage completes.
    """
    # Check if conversation exists
    conversation = storage.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Check if this is the first message
    is_first_message = len(conversation["messages"]) == 0

    async def event_generator():
        try:
            # Add user message
            storage.add_user_message(conversation_id, request.content)

            # Start title generation in parallel (don't await yet)
            title_task = None
            if is_first_message:
                title_task = asyncio.create_task(generate_conversation_title(request.content))

            # Stage 1: Collect responses
            yield f"data: {json.dumps({'type': 'stage1_start'})}\n\n"
            stage1_results = await stage1_collect_responses(request.content)
            yield f"data: {json.dumps({'type': 'stage1_complete', 'data': stage1_results})}\n\n"

            # Stage 2: Collect rankings
            yield f"data: {json.dumps({'type': 'stage2_start'})}\n\n"
            stage2_results, label_to_model = await stage2_collect_rankings(request.content, stage1_results)
            aggregate_rankings = calculate_aggregate_rankings(stage2_results, label_to_model)
            yield f"data: {json.dumps({'type': 'stage2_complete', 'data': stage2_results, 'metadata': {'label_to_model': label_to_model, 'aggregate_rankings': aggregate_rankings}})}\n\n"

            # Stage 3: Synthesize final answer
            yield f"data: {json.dumps({'type': 'stage3_start'})}\n\n"
            stage3_result = await stage3_synthesize_final(request.content, stage1_results, stage2_results)
            yield f"data: {json.dumps({'type': 'stage3_complete', 'data': stage3_result})}\n\n"

            # Wait for title generation if it was started
            if title_task:
                title = await title_task
                storage.update_conversation_title(conversation_id, title)
                yield f"data: {json.dumps({'type': 'title_complete', 'data': {'title': title}})}\n\n"

            # Save complete assistant message
            storage.add_assistant_message(
                conversation_id,
                stage1_results,
                stage2_results,
                stage3_result
            )

            # Send completion event
            yield f"data: {json.dumps({'type': 'complete'})}\n\n"

        except Exception as e:
            # Send error event
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


# ---------------------------------------------------------------------------
# Debate endpoints
# ---------------------------------------------------------------------------

class StartDebateRequest(BaseModel):
    """Request to start a debate with a topic."""
    topic: str


class DebateMetadata(BaseModel):
    """Debate metadata for list view."""
    id: str
    created_at: str
    title: str
    topic: str | None
    message_count: int


class Debate(BaseModel):
    """Full debate with all messages."""
    id: str
    created_at: str
    title: str
    topic: str | None
    messages: List[Dict[str, Any]]


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
    title_task = asyncio.create_task(generate_conversation_title(request.topic))

    # Run the full debate
    stage1, stage2, stage3, stage4 = await run_full_debate(request.topic)

    # Save results
    storage.add_debate_result_message(debate_id, stage1, stage2, stage3, stage4)

    # Update title
    title = await title_task
    title = f"Debate: {title}"
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
            title_task = asyncio.create_task(
                generate_conversation_title(request.topic)
            )

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
            stage4 = await stage4_judge_evaluation(
                request.topic, stage1, stage2, stage3
            )
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

