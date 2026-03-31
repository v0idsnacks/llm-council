"""Multi-Agent Debate System orchestration.

Maps onto the existing LLM Council architecture:
  - Pro Agent   → affirmative arguments (uses PRO_MODEL)
  - Against Agent → counterarguments (uses AGAINST_MODEL)
  - Judge Agent   → verdict + confidence score (uses JUDGE_MODEL)

Debate flow:
  Stage 1 – Opening Arguments  (Pro + Against, parallel)
  Stage 2 – Rebuttal Round     (Pro + Against, parallel, context-aware)
  Stage 3 – Final Statements   (Pro + Against, parallel, closing remarks)
  Stage 4 – Judge Evaluation   (verdict, confidence score, pros/cons summary)
"""

import asyncio
import re
from typing import Dict, Any, Tuple

from .openrouter import query_model
from .config import PRO_MODEL, AGAINST_MODEL, JUDGE_MODEL


# ---------------------------------------------------------------------------
# Stage 1 – Opening Arguments
# ---------------------------------------------------------------------------

async def stage1_opening_arguments(topic: str) -> Dict[str, Any]:
    """
    Stage 1: Pro and Against agents present their opening arguments.

    Args:
        topic: The debate topic

    Returns:
        Dict with 'pro' and 'against' keys, each containing agent info and argument
    """
    pro_prompt = (
        f"You are the PRO agent in a structured debate. Your role is to argue "
        f"IN FAVOR of the following topic.\n\n"
        f"Topic: {topic}\n\n"
        f"Present a strong, well-reasoned opening argument supporting this topic. Include:\n"
        f"1. Your main thesis statement\n"
        f"2. 3-4 key supporting arguments with evidence/reasoning\n"
        f"3. Pre-emptively address the strongest potential weaknesses\n\n"
        f"Be persuasive, logical, and comprehensive."
    )

    against_prompt = (
        f"You are the AGAINST agent in a structured debate. Your role is to argue "
        f"AGAINST the following topic.\n\n"
        f"Topic: {topic}\n\n"
        f"Present a strong, well-reasoned opening argument opposing this topic. Include:\n"
        f"1. Your main thesis statement (opposing the topic)\n"
        f"2. 3-4 key counterarguments with evidence/reasoning\n"
        f"3. Pre-emptively address the strongest potential weaknesses of your position\n\n"
        f"Be persuasive, logical, and comprehensive."
    )

    pro_response, against_response = await asyncio.gather(
        query_model(PRO_MODEL, [{"role": "user", "content": pro_prompt}]),
        query_model(AGAINST_MODEL, [{"role": "user", "content": against_prompt}]),
    )

    return {
        "pro": {
            "agent": "Pro Agent",
            "model": PRO_MODEL,
            "argument": pro_response.get("content", "") if pro_response else "",
        },
        "against": {
            "agent": "Against Agent",
            "model": AGAINST_MODEL,
            "argument": against_response.get("content", "") if against_response else "",
        },
    }


# ---------------------------------------------------------------------------
# Stage 2 – Rebuttal Round
# ---------------------------------------------------------------------------

async def stage2_rebuttal_round(
    topic: str,
    stage1_results: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Stage 2: Each agent rebuts the other's opening argument.

    Args:
        topic: The debate topic
        stage1_results: Opening arguments from Stage 1

    Returns:
        Dict with 'pro' and 'against' rebuttal entries
    """
    pro_opening = stage1_results["pro"]["argument"]
    against_opening = stage1_results["against"]["argument"]

    pro_rebuttal_prompt = (
        f"You are the PRO agent in a structured debate about: {topic}\n\n"
        f"Your opening argument was:\n{pro_opening}\n\n"
        f"The AGAINST agent made the following opposing argument:\n{against_opening}\n\n"
        f"Now provide your rebuttal. Directly address the Against agent's specific points, "
        f"refute their arguments with evidence, and reinforce your own position. "
        f"Be precise and persuasive."
    )

    against_rebuttal_prompt = (
        f"You are the AGAINST agent in a structured debate about: {topic}\n\n"
        f"Your opening argument was:\n{against_opening}\n\n"
        f"The PRO agent made the following argument:\n{pro_opening}\n\n"
        f"Now provide your rebuttal. Directly address the Pro agent's specific points, "
        f"refute their arguments with evidence, and reinforce your own position. "
        f"Be precise and persuasive."
    )

    pro_rebuttal, against_rebuttal = await asyncio.gather(
        query_model(PRO_MODEL, [{"role": "user", "content": pro_rebuttal_prompt}]),
        query_model(AGAINST_MODEL, [{"role": "user", "content": against_rebuttal_prompt}]),
    )

    return {
        "pro": {
            "agent": "Pro Agent",
            "model": PRO_MODEL,
            "rebuttal": pro_rebuttal.get("content", "") if pro_rebuttal else "",
        },
        "against": {
            "agent": "Against Agent",
            "model": AGAINST_MODEL,
            "rebuttal": against_rebuttal.get("content", "") if against_rebuttal else "",
        },
    }


# ---------------------------------------------------------------------------
# Stage 3 – Final Statements
# ---------------------------------------------------------------------------

async def stage3_final_statements(
    topic: str,
    stage1_results: Dict[str, Any],
    stage2_results: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Stage 3: Each agent delivers a short closing/final statement.

    Args:
        topic: The debate topic
        stage1_results: Opening arguments from Stage 1
        stage2_results: Rebuttals from Stage 2

    Returns:
        Dict with 'pro' and 'against' final statement entries
    """
    pro_opening = stage1_results["pro"]["argument"]
    against_opening = stage1_results["against"]["argument"]
    pro_rebuttal = stage2_results["pro"]["rebuttal"]
    against_rebuttal = stage2_results["against"]["rebuttal"]

    pro_final_prompt = (
        f"You are the PRO agent in a structured debate about: {topic}\n\n"
        f"The debate so far:\n"
        f"Your opening: {pro_opening}\n\n"
        f"Against opening: {against_opening}\n\n"
        f"Your rebuttal: {pro_rebuttal}\n\n"
        f"Against rebuttal: {against_rebuttal}\n\n"
        f"Deliver a concise, powerful FINAL STATEMENT (2-3 paragraphs) that summarises "
        f"why your side has won the debate. Highlight the strongest points in your favour "
        f"and the key weaknesses in the opposing case."
    )

    against_final_prompt = (
        f"You are the AGAINST agent in a structured debate about: {topic}\n\n"
        f"The debate so far:\n"
        f"Pro opening: {pro_opening}\n\n"
        f"Your opening: {against_opening}\n\n"
        f"Pro rebuttal: {pro_rebuttal}\n\n"
        f"Your rebuttal: {against_rebuttal}\n\n"
        f"Deliver a concise, powerful FINAL STATEMENT (2-3 paragraphs) that summarises "
        f"why your side has won the debate. Highlight the strongest points in your favour "
        f"and the key weaknesses in the opposing case."
    )

    pro_final, against_final = await asyncio.gather(
        query_model(PRO_MODEL, [{"role": "user", "content": pro_final_prompt}]),
        query_model(AGAINST_MODEL, [{"role": "user", "content": against_final_prompt}]),
    )

    return {
        "pro": {
            "agent": "Pro Agent",
            "model": PRO_MODEL,
            "final_statement": pro_final.get("content", "") if pro_final else "",
        },
        "against": {
            "agent": "Against Agent",
            "model": AGAINST_MODEL,
            "final_statement": against_final.get("content", "") if against_final else "",
        },
    }


# ---------------------------------------------------------------------------
# Stage 4 – Judge Evaluation
# ---------------------------------------------------------------------------

async def stage4_judge_evaluation(
    topic: str,
    stage1_results: Dict[str, Any],
    stage2_results: Dict[str, Any],
    stage3_results: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Stage 4: The Judge evaluates both sides and delivers a verdict.

    Args:
        topic: The debate topic
        stage1_results: Opening arguments
        stage2_results: Rebuttals
        stage3_results: Final statements

    Returns:
        Dict with evaluation text, parsed verdict, and confidence score
    """
    judge_prompt = (
        f"You are an impartial Judge evaluating a structured debate on the topic:\n"
        f"**{topic}**\n\n"
        f"---\n"
        f"PRO AGENT – Opening Argument:\n{stage1_results['pro']['argument']}\n\n"
        f"AGAINST AGENT – Opening Argument:\n{stage1_results['against']['argument']}\n\n"
        f"PRO AGENT – Rebuttal:\n{stage2_results['pro']['rebuttal']}\n\n"
        f"AGAINST AGENT – Rebuttal:\n{stage2_results['against']['rebuttal']}\n\n"
        f"PRO AGENT – Final Statement:\n{stage3_results['pro']['final_statement']}\n\n"
        f"AGAINST AGENT – Final Statement:\n{stage3_results['against']['final_statement']}\n\n"
        f"---\n"
        f"Provide your evaluation using EXACTLY this format:\n\n"
        f"## Summary of Arguments\n\n"
        f"### Pro Arguments\n"
        f"[Concise summary of the key points made by the Pro agent]\n\n"
        f"### Against Arguments\n"
        f"[Concise summary of the key points made by the Against agent]\n\n"
        f"## Pros and Cons Analysis\n\n"
        f"### Pros (strongest points FOR the topic)\n"
        f"- [Point 1]\n"
        f"- [Point 2]\n"
        f"- [Point 3]\n\n"
        f"### Cons (strongest points AGAINST the topic)\n"
        f"- [Point 1]\n"
        f"- [Point 2]\n"
        f"- [Point 3]\n\n"
        f"## Judge's Verdict\n\n"
        f"[Your verdict: which side presented the stronger case and why. Be specific.]\n\n"
        f"## Confidence Score\n\n"
        f"VERDICT: [PRO/AGAINST/TIE]\n"
        f"CONFIDENCE: [0-100]%\n"
        f"REASONING: [Brief explanation of the confidence level]"
    )

    judge_response = await query_model(
        JUDGE_MODEL, [{"role": "user", "content": judge_prompt}]
    )

    evaluation_text = (
        judge_response.get("content", "") if judge_response else ""
    )

    return {
        "agent": "Judge",
        "model": JUDGE_MODEL,
        "evaluation": evaluation_text,
        "verdict": _parse_verdict(evaluation_text),
        "confidence": _parse_confidence(evaluation_text),
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_verdict(text: str) -> str:
    """Extract VERDICT value (PRO / AGAINST / TIE) from judge evaluation."""
    match = re.search(r"VERDICT\s*:\s*(PRO|AGAINST|TIE)", text, re.IGNORECASE)
    if match:
        return match.group(1).upper()
    return "UNKNOWN"


def _parse_confidence(text: str) -> int:
    """Extract CONFIDENCE percentage (0-100) from judge evaluation."""
    match = re.search(r"CONFIDENCE\s*:\s*(\d+)\s*%", text, re.IGNORECASE)
    if match:
        value = int(match.group(1))
        return max(0, min(100, value))
    return 0


# ---------------------------------------------------------------------------
# Full pipeline
# ---------------------------------------------------------------------------

async def run_full_debate(
    topic: str,
) -> Tuple[Dict, Dict, Dict, Dict]:
    """
    Run the complete 4-stage debate process.

    Args:
        topic: The debate topic / proposition

    Returns:
        Tuple of (stage1_results, stage2_results, stage3_results, stage4_results)
    """
    stage1 = await stage1_opening_arguments(topic)

    stage2 = await stage2_rebuttal_round(topic, stage1)

    stage3 = await stage3_final_statements(topic, stage1, stage2)

    stage4 = await stage4_judge_evaluation(topic, stage1, stage2, stage3)

    return stage1, stage2, stage3, stage4
