import os
import argparse
from datetime import datetime

from deck import load_deck, pick_card, DECK_DIR
from ai_text import generate_tarot_reading, translate_text, build_narration_script, generate_metadata
from voice import text_to_speech, transcribe_audio
from video import create_video
from question_agent import decide_question
from critique_agent import critique_video_script


def get_question(args):
    if args.question:
        return args.question, f"Your question: {args.question}.", "So — was that what you needed to hear?"
    result = decide_question()
    return result["question"], result["viewer_intro"], result["closing_echo"]


def text_gate(deck, args):
    question, viewer_intro, closing_echo = get_question(args)
    card = pick_card(deck, args.card)
    reading = generate_tarot_reading(question, card)

    while True:
        est_words = len(f"{viewer_intro} {reading}".split())
        est_duration = est_words / 2.4

        print("\n--- TEXT REVIEW ---")
        print(f"Question: {question}")
        print(f"Card: {card['name']}")
        print(f"Viewer intro: {viewer_intro}")
        print(f"Closing echo: {closing_echo}")
        print(f"Reading: {reading}")

        critique = critique_video_script(question, viewer_intro, card, reading, est_duration)
        print(f"\n[Critique] Verdict: {critique['verdict']}")
        print(f"[Critique] {critique['critique']}")
        if critique["suggested_fix"]:
            print(f"[Suggested fix] {critique['suggested_fix']}")

        choice = input(
            "\n[A]ccept | [Q]redo question | [C]redo card | [R]edo reading | e[X]it: "
        ).strip().lower()

        if choice == "a":
            return question, viewer_intro, closing_echo, card, reading
        elif choice == "q":
            question, viewer_intro, closing_echo = get_question(args)
            reading = generate_tarot_reading(question, card)
        elif choice == "c":
            card = pick_card(deck, args.card)
            reading = generate_tarot_reading(question, card)
        elif choice == "r":
            reading = generate_tarot_reading(question, card)
        elif choice == "x":
            exit()
        else:
            print("Invalid choice.")


def audio_gate(narration, audio_file, language):
    while True:
        text_to_speech(narration, audio_file, language)
        print(f"\nAudio saved to {audio_file} — listen to it now.")
        choice = input("[A]ccept | [R]edo audio | e[X]it: ").strip().lower()
        if choice == "a":
            return
        elif choice == "x":
            exit()
        elif choice != "r":
            print("Invalid choice.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--question", required=False, help="Your tarot question (omit to let the agent decide)")
    parser.add_argument("--card", required=False, help="Specific card name (optional; random if omitted)")
    parser.add_argument("--language", default="en", choices=["en", "uk", "es"], help="Reading language")
    parser.add_argument("--music", required=False, help="Path to a background music file (optional)")
    args = parser.parse_args()

    deck = load_deck()

    question, viewer_intro, closing_echo, card, reading = text_gate(deck, args)
    card_image = os.path.join(DECK_DIR, "images", card["image_file"])

    narration_en = build_narration_script(question, viewer_intro, closing_echo, card, reading)
    narration = translate_text(narration_en, args.language)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    card_slug = card["image_file"].replace(".png", "")
    audio_file = f"output/{timestamp}_{card_slug}.wav"
    video_file = f"output/{timestamp}_{card_slug}.mp4"
    os.makedirs("output", exist_ok=True)

    audio_gate(narration, audio_file, args.language)

    words = transcribe_audio(audio_file)
    create_video(card_image, words, audio_file, video_file, music_file=args.music)

    metadata = generate_metadata(question, card, reading, args.language)
    metadata_file = video_file.replace(".mp4", "_metadata.txt")
    with open(metadata_file, "w", encoding="utf-8") as f:
        f.write(f"TITLE: {metadata['title']}\n\nDESCRIPTION:\n{metadata['description']}\n\nHASHTAGS:\n{metadata['hashtags']}")
    print(f"Metadata saved to {metadata_file}")