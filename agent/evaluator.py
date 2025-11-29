from typing import Dict

# Simple evaluator that scores responses on technical, communication and culture-fit
# In production this would call an LLM (Claude or GPT-4) with a scoring rubric.

def evaluate_response(question: Dict, answer: str, provider: str = "mock") -> Dict:
    # Basic heuristics: length and presence of keywords
    if not answer:
        return {"technical": 0.0, "communication": 0.0, "culture": 0.0, "notes": "No answer provided"}

    length = len(answer.split())
    technical = min(5, max(1, length / 30))  # scale approx 1..5
    communication = min(5, max(1, 1 + (length / 80)))
    culture = 3.0

    # Provider hooks: placeholder for LLM based evaluation.
    if provider in ("openai", "anthropic", "langchain"):
        # The real implementation would send a prompt to the LLM asking for numeric scores and justification.
        # We just return a simple mocked evaluation for now.
        technical = round(technical, 2)
        communication = round(communication, 2)

    return {"technical": technical, "communication": communication, "culture": culture, "notes": "heuristic evaluation"}
