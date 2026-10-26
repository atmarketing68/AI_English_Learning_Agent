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
    Generates a context for the roleplay (free-topic mode; curated scenarios in
    app/services/speaking_scenarios.py do not need this call).
    Returns: { "system_prompt": "...", "ai_first_message": "..." }
    """
    prompt = f"""You are an English teacher designing a roleplay for a Vietnamese CEFR {level} student.
The topic is: {topic}.

Create a scenario where the student talks to you. Give the AI character a name and a clear role.
Return ONLY JSON:
{{
    "system_prompt": "The system prompt that will instruct the AI on how to behave in this roleplay. E.g., 'You are Linh, a barista... The user is a customer... Keep responses under 2 sentences and end with a question.'",
    "ai_first_message": "The AI's opening line to start the conversation."
}}
"""
    raw = get_llm_response(prompt)
    return parse_and_validate(raw, RoleplayScenarioOutput)


def evaluate_speaking_turn(
    system_prompt: str,
    history: list[dict],
    user_message: str,
    level: str = "A2",
) -> dict:
    """
    Evaluates the user's latest message and generates the next AI reply.
    history format: [{"role": "ai", "content": "..."}, {"role": "user", "content": "..."}]

    Returns:
    {
        "ai_reply": "...",
        "feedback": "...",   # Vietnamese feedback on grammar/vocab (if any errors)
        "is_correct": bool,  # True if generally understandable and correct
        "score": float,      # 0-100 based on grammar and relevance
        "corrected": "...",  # natural version of the learner's sentence ("" if already fine)
        "hint_en": "..."     # one short thing the learner could say next
    }
    """
    history_text = ""
    for msg in history:
        role = "AI" if msg["role"] == "ai" else "Learner"
        history_text += f"{role}: {msg['content']}\n"
    history_text += f"Learner: {user_message}\n"

    prompt = f"""You are an AI English speaking coach running a roleplay with a Vietnamese CEFR {level} learner.
Roleplay Context (stay in this character for 'ai_reply'): {system_prompt}

Conversation so far:
{history_text}

The learner's message was transcribed from speech, so ignore punctuation and capitalisation.

Task:
1. As the character, write the next reply ('ai_reply'): natural, 1-2 short sentences, end with a question or prompt so the learner keeps talking. Match the learner's level ({level}).
2. Evaluate the learner's latest message ("{user_message}") for grammar, vocabulary and relevance.
3. 'feedback': Vietnamese, ONLY if there is an error or unnatural phrasing — name the mistake briefly and how to fix it. If it is fine, write "Rất tốt!".
4. 'corrected': the learner's sentence rewritten naturally and correctly. Empty string if it was already fine.
5. 'hint_en': one short, natural English sentence the learner could say next in this situation (max 12 words).
6. 'score': 0-100.

Output ONLY JSON:
{{
    "ai_reply": "Your next response as the character",
    "feedback": "Nhận xét ngắn bằng tiếng Việt (nếu có lỗi)",
    "is_correct": true,
    "score": 85,
    "corrected": "",
    "hint_en": "A short sentence the learner could say next"
}}
"""
    raw = get_llm_response(prompt)
    return parse_and_validate(raw, SpeakingTurnOutput)
