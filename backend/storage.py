"""JSON-based storage for debates."""

import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
import re
from .config import DEBATES_DIR


_SAFE_ID_RE = re.compile(r'^[a-zA-Z0-9\-]+$')


def _validate_id(resource_id: str) -> str:
    """
    Validate that a resource ID contains only safe characters (alphanumeric + hyphens).
    Raises ValueError for IDs that could enable path traversal.

    Args:
        resource_id: The ID to validate

    Returns:
        The validated ID if safe

    Raises:
        ValueError: If the ID contains unsafe characters
    """
    if not _SAFE_ID_RE.match(resource_id):
        raise ValueError(f"Invalid resource ID: {resource_id!r}")
    return resource_id


def ensure_debates_dir():
    """Ensure the debates data directory exists."""
    Path(DEBATES_DIR).mkdir(parents=True, exist_ok=True)


def get_debate_path(debate_id: str) -> str:
    """Get the file path for a debate, with path-traversal prevention."""
    _validate_id(debate_id)
    debates_abs = os.path.realpath(DEBATES_DIR)
    path = os.path.realpath(os.path.join(debates_abs, f"{debate_id}.json"))
    if not path.startswith(debates_abs + os.sep):
        raise ValueError(f"Invalid debate ID: {debate_id!r}")
    return path


def create_debate(debate_id: str) -> Dict[str, Any]:
    """
    Create a new debate record.

    Args:
        debate_id: Unique identifier for the debate

    Returns:
        New debate dict
    """
    ensure_debates_dir()

    debate = {
        "id": debate_id,
        "created_at": datetime.utcnow().isoformat(),
        "title": "New Debate",
        "topic": None,
        "messages": [],
    }

    path = get_debate_path(debate_id)
    with open(path, "w") as f:
        json.dump(debate, f, indent=2)

    return debate


def get_debate(debate_id: str) -> Optional[Dict[str, Any]]:
    """
    Load a debate from storage.

    Args:
        debate_id: Unique identifier for the debate

    Returns:
        Debate dict or None if not found
    """
    path = get_debate_path(debate_id)

    if not os.path.exists(path):
        return None

    with open(path, "r") as f:
        return json.load(f)


def save_debate(debate: Dict[str, Any]):
    """
    Save a debate to storage.

    Args:
        debate: Debate dict to save
    """
    ensure_debates_dir()

    path = get_debate_path(debate["id"])
    with open(path, "w") as f:
        json.dump(debate, f, indent=2)


def list_debates() -> List[Dict[str, Any]]:
    """
    List all debates (metadata only).

    Returns:
        List of debate metadata dicts
    """
    ensure_debates_dir()

    debates = []
    for filename in os.listdir(DEBATES_DIR):
        if filename.endswith(".json"):
            path = os.path.join(DEBATES_DIR, filename)
            with open(path, "r") as f:
                data = json.load(f)
                debates.append({
                    "id": data["id"],
                    "created_at": data["created_at"],
                    "title": data.get("title", "New Debate"),
                    "topic": data.get("topic"),
                    "message_count": len(data["messages"]),
                })

    debates.sort(key=lambda x: x["created_at"], reverse=True)
    return debates


def add_debate_topic(debate_id: str, topic: str):
    """
    Store the debate topic and add the user message.

    Args:
        debate_id: Debate identifier
        topic: The debate proposition
    """
    debate = get_debate(debate_id)
    if debate is None:
        raise ValueError(f"Debate {debate_id} not found")

    debate["topic"] = topic
    debate["messages"].append({"role": "user", "content": topic})
    save_debate(debate)


def add_debate_result_message(
    debate_id: str,
    stage1: Dict[str, Any],
    stage2: Dict[str, Any],
    stage3: Dict[str, Any],
    stage4: Dict[str, Any],
):
    """
    Add the completed debate result as an assistant message.

    Args:
        debate_id: Debate identifier
        stage1: Opening arguments
        stage2: Rebuttal round
        stage3: Final statements
        stage4: Judge evaluation
    """
    debate = get_debate(debate_id)
    if debate is None:
        raise ValueError(f"Debate {debate_id} not found")

    debate["messages"].append({
        "role": "debate",
        "stage1": stage1,
        "stage2": stage2,
        "stage3": stage3,
        "stage4": stage4,
    })
    save_debate(debate)


def update_debate_title(debate_id: str, title: str):
    """
    Update the title of a debate.

    Args:
        debate_id: Debate identifier
        title: New title
    """
    debate = get_debate(debate_id)
    if debate is None:
        raise ValueError(f"Debate {debate_id} not found")

    debate["title"] = title
    save_debate(debate)
