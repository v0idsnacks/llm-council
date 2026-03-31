"""Shared title generation for debate sessions."""

from .openrouter import query_model


async def generate_debate_title(topic: str) -> str:
    """
    Generate a short title for a debate based on the topic.

    Args:
        topic: The debate proposition/topic

    Returns:
        A short title (3-5 words)
    """
    title_prompt = f"""Generate a very short title (3-5 words maximum) that summarizes the following debate topic.
The title should be concise and descriptive. Do not use quotes or punctuation in the title.

Topic: {topic}

Title:"""

    messages = [{"role": "user", "content": title_prompt}]

    # Use gemini-2.5-flash for title generation (fast and cheap)
    response = await query_model("google/gemini-2.5-flash", messages, timeout=30.0)

    if response is None:
        # Fallback to a generic title
        return "New Debate"

    title = response.get("content", "New Debate").strip()

    # Clean up the title - remove quotes, limit length
    title = title.strip("\"'")

    # Truncate if too long
    if len(title) > 50:
        title = title[:47] + "..."

    return title
