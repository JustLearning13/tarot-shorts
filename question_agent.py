import anthropic
from dotenv import load_dotenv
import os

load_dotenv()

import json

HISTORY_FILE = "question_history.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE) as f:
            return json.load(f)
    return []

def save_to_history(question):
    history = load_history()
    history.append(question)
    with open(HISTORY_FILE, "w") as f:
        json.dump(history[-20:], f)  # keep last 20, avoid unbounded growth

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

tools = [{
    "name": "propose_question",
    "description": "Propose one open-ended tarot question suitable for a short-form video.",
    "input_schema": {
        "type": "object",
        "properties": {
            "question": {"type": "string"},
            "viewer_intro": {...},  # existing
            "closing_echo": {
                "type": "string",
                "description": (
                    "A short closing line (under 12 words), spoken right before "
                    "the outro CTA, that directly answers or echoes the opening "
                    "viewer_intro line — creates a loop so the ending calls back "
                    "to the beginning."
                )
            },
            "reasoning": {
                "type": "string",
                "description": "Analytical explanation for the creator: why this question works (audience psychology, engagement, format fit)."
            },
            "viewer_intro": {
                "type": "string",
                "description": (
                    "The FIRST LINE spoken in the video — this is a scroll-stopping "
                    "hook, not a gentle intro. It must be under 8 words, create genuine "
                    "curiosity or tension in the first 2 seconds, and only then can the "
                    "mystical tone follow in what comes after. Bad: 'Take a breath with "
                    "me, love.' Good: 'You already know what you're avoiding.'"
                )
            }
        },
        "required": ["question", "viewer_intro", "closing_echo"]
    }
}]

def decide_question():
    history = load_history()
    avoid_list = "\n".join(f"- {q}" for q in history) if history else "None yet."

    message = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=800,
        tools=tools,
        tool_choice={"type": "tool", "name": "propose_question"},
        messages=[{
            "role": "user",
            "content": (
                "Goal: produce today's tarot YouTube short. "
                "Decide a good, broadly relatable question for Ukrainian audience "
                ", based on what people in Ukraine request the most — "
                "avoid repeating common ones like 'What do I need to hear right now?'. "
                f"Do NOT repeat or closely paraphrase any of these already-used questions:\n{avoid_list}"
            )
        }]
    )
    tool_call = next(b for b in message.content if b.type == "tool_use")
    print(f"[Agent reasoning]: {tool_call.input.get('reasoning', '')}")

    question = tool_call.input["question"]
    save_to_history(question)

    return {
        "question": question,
        "viewer_intro": tool_call.input["viewer_intro"],
        "reasoning": tool_call.input.get("reasoning", ""),
        "closing_echo": tool_call.input["closing_echo"]
    }   

if __name__ == "__main__":
    result = decide_question()
    print(f"\nQuestion: {result['question']}")
    print(f"Viewer intro: {result['viewer_intro']}")