import os
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()
client = Anthropic()

def generate_tarot_reading(question, card):
    message = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=500,
        messages=[
            {
                "role": "user",
                "content": (
                    f"I drew the {card['name']} tarot card in response to this question: "
                    f"'{question}'. Its traditional upright meaning is: {card['upright_meaning']}. "
                    f"Give me a short, mystical tarot reading (2-3 sentences) in English "
                    f"that interprets this card for my question, grounded in that meaning."
                )
            }
        ]
    )
    for block in message.content:
        if block.type == "text":
            return block.text

def translate_text(text, language):
    if language == "en":
        return text

    lang_name = "Ukrainian" if language == "uk" else "Spanish"
    message = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=800,
        messages=[
            {
                "role": "user",
                "content": f"Translate this to {lang_name}, keeping the same mystical tone. Output only the translation, nothing else:\n\n{text}"
            }
        ]
    )
    for block in message.content:
        if block.type == "text":
            return block.text.strip()

def build_narration_script(question, viewer_intro, closing_echo, card, reading):
    intro = f"{viewer_intro} Your question: {question}. The card drawn is: {card['name']}."
    outro = f"{closing_echo} Put your question in the comments, and we'll see what card will answer it."
    return f"{intro} {reading} {outro}"

def generate_metadata(question, card, reading, language="en"):
    message = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=400,
        tools=[{
            "name": "video_metadata",
            "description": "Generate YouTube Shorts metadata for a tarot reading video.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Under 60 chars, intriguing, not clickbait — must honestly reflect the video."},
                    "description": {"type": "string", "description": "1-2 sentences plus a call to comment their own question."},
                    "hashtags": {"type": "string", "description": "5-8 relevant hashtags, space-separated, starting with #tarot #tarotshorts"}
                },
                "required": ["title", "description", "hashtags"]
            }
        }],
        tool_choice={"type": "tool", "name": "video_metadata"},
        messages=[{
            "role": "user",
            "content": f"Question: {question}\nCard: {card['name']}\nReading: {reading}\nLanguage: {language}\n\nGenerate YouTube Shorts metadata for this."
        }]
    )
    tool_call = next(b for b in message.content if b.type == "tool_use")
    return tool_call.input