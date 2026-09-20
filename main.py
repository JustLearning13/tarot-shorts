import os
import argparse
from datetime import datetime

from deck import load_deck, pick_card, DECK_DIR
from ai_text import generate_tarot_reading, translate_text, build_narration_script
from voice import text_to_speech, transcribe_audio
from video import create_video
from question_agent import decide_question

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--question", required=False, help="Your tarot question (omit to let the agent decide)")
    parser.add_argument("--card", required=False, help="Specific card name (optional; random if omitted)")
    parser.add_argument("--language", default="en", choices=["en", "uk", "es"], help="Reading language")
    args = parser.parse_args()

    if args.question:
        question = args.question
        viewer_intro = f"Your question: {question}."
    else:
        result = decide_question()
        question = result["question"]
        viewer_intro = result["viewer_intro"]

    deck = load_deck()
    card = pick_card(deck, args.card)
    card_image = os.path.join(DECK_DIR, "images", card["image_file"])

    print(f"Question: {question}")
    print(f"Card drawn: {card['name']}")

    reading = generate_tarot_reading(question, card)
    print(f"Reading (EN): {reading}")

    narration_en = build_narration_script(question, viewer_intro, card, reading)
    narration = translate_text(narration_en, args.language)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    card_slug = card["image_file"].replace(".png", "")

    audio_file = f"output/{timestamp}_{card_slug}.wav"
    video_file = f"output/{timestamp}_{card_slug}.mp4"

    os.makedirs("output", exist_ok=True)

    text_to_speech(narration, audio_file)

    words = transcribe_audio(audio_file)
    create_video(card_image, words, audio_file, video_file)