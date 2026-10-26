"""
AGEN — Speaking Agent
Handles dynamic roleplay generation and conversational evaluation.
"""
from app.services.llm_client import get_llm_response, parse_and_validate
from app.agents.contracts import RoleplayScenarioOutput, SpeakingTurnOutput
from app.services.llm_cache import ai_cache


@ai_cache()
def generate_roleplay_scenario(level: str, topic: str) -> dict:
    """
    Generates a context for the roleplay.
    Returns: { "system_prompt": "...", "ai_first_message": "..." }
    """
    prompt = f"""You are an English teacher designing a roleplay for a CEFR {level} student.
The topic is: {topic}.

Create a scenario where the student talks to you.
Return ONLY JSON:
{{
    "system_prompt": "The system prompt that will instruct the AI on how to behave in this roleplay. E.g., 'You are a barista... The user is a customer... Keep responses under 2 sentences.'",
    "ai_first_message": "The AI's opening line to start the conversation."
}}
"""
    raw = get_llm_response(prompt)
    return parse_and_validate(raw, RoleplayScenarioOutput)


def evaluate_speaking_turn(system_prompt: str, history: list[dict], user_message: str) -> dict:
    """
    Evaluates the user's latest message and generates the next AI reply.
    history format: [{"role": "ai", "content": "..."}, {"role": "user", "content": "..."}]
    
    Returns: 
    {
        "ai_reply": "...",
        "feedback": "...", # Vietnamese feedback on grammar/vocab (if any errors)
        "is_correct": bool, # True if generally understandable and correct
        "score": float # 0-100 based on grammar and relevance
    }
    """
    # Format history for the prompt
    history_text = ""
    for msg in history:
        role = "AI" if msg["role"] == "ai" else "Learner"
        history_text += f"{role}: {msg['content']}\n"
        
    history_text += f"Learner: {user_message}\n"

    prompt = f"""You are an AI English Tutor evaluating a roleplay conversation.
Roleplay Context: {system_prompt}

Conversation so far:
{history_text}

Task:
1. Act as the AI character and generate the next reply ('ai_reply') to continue the conversation naturally. Keep it short (1-2 sentences).
2. Evaluate the Learner's latest message ("{user_message}") for grammar, vocabulary, and relevance.
3. Provide feedback in Vietnamese ('feedback') ONLY IF there are errors or major unnatural phrasing. If perfect, leave it empty or say 'Rất tốt!'.
4. Give a score from 0-100.

Output ONLY JSON:
{{
    "ai_reply": "Your next response as the character",
    "feedback": "Nhận xét lỗi ngữ pháp bằng tiếng Việt (nếu có)",
    "is_correct": true/false,
    "score": 85
}}
"""
    raw = get_llm_response(prompt)
    return parse_and_validate(raw, SpeakingTurnOutput)
