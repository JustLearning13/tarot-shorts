import os
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()
client = Anthropic()

tools = [{
    "name": "critique_reading",
    "description": "Critique a tarot video script for tone, pacing, and coherence before posting.",
    "input_schema": {
        "type": "object",
        "properties": {
            "verdict": {
                "type": "string",
                "enum": ["good_to_post", "minor_tweaks_suggested", "needs_rework"]
            },
            "critique": {
                "type": "string",
                "description": "2-4 sentences: does the viewer_intro tone match the reading? Does the reading actually answer the question? Any awkward phrasing or pacing concerns given the duration?"
            },
            "suggested_fix": {
                "type": "string",
                "description": "If verdict is not 'good_to_post', a concrete suggested rewrite or fix. Empty string if good_to_post."
            }
        },
        "required": ["verdict", "critique", "suggested_fix"]
    }
}]

def critique_video_script(question, viewer_intro, card, reading, narration_duration):
    word_count = len(f"{viewer_intro} {reading}".split())
    words_per_second = word_count / narration_duration if narration_duration else 0

    message = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=600,
        tools=tools,
        tool_choice={"type": "tool", "name": "critique_reading"},
        messages=[{
            "role": "user",
            "content": (
                f"Review this tarot short's script before it gets posted.\n\n"
                f"Question: {question}\n"
                f"Card: {card['name']}\n"
                f"Viewer intro (spoken first): {viewer_intro}\n"
                f"Reading (spoken after): {reading}\n"
                f"Narration duration: {narration_duration:.1f} seconds "
                f"({word_count} words, ~{words_per_second:.1f} words/sec).\n\n"
                f"Check: does the intro's tone match the reading? Does the reading actually "
                f"answer the question using the card meaning? Is the pacing likely too "
                f"slow/fast for the word count vs. duration? (Ideal is roughly 2.3-2.6 words/sec "
                f"for a calm but not sluggish narration.)"
            )
        }]
    )
    tool_call = next(b for b in message.content if b.type == "tool_use")
    return tool_call.input


if __name__ == "__main__":
    # Standalone test with fake data — replace with a real recent run's values
    result = critique_video_script(
        question="What am I ready to release from my life right now?",
        viewer_intro="Take a breath with me, love — somewhere inside you already know what's grown too heavy to carry.",
        card={"name": "The Tower"},
        reading="The Tower signals sudden upheaval, but also liberation from what no longer serves you.",
        narration_duration=14.0
    )
    print(f"Verdict: {result['verdict']}")
    print(f"Critique: {result['critique']}")
    print(f"Suggested fix: {result['suggested_fix']}")