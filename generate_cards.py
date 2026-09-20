import os
import json
import time
import argparse
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def generate_card_image(card, image_path, style_template):
    prompt = style_template.format(scene=card["scene"], title=card["name"].upper())

    response = client.models.generate_content(
        model="gemini-3-pro-image",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=['TEXT', 'IMAGE'],
            image_config=types.ImageConfig(aspect_ratio="3:4", image_size="2K"),
        )
    )

    for part in response.candidates[0].content.parts:
        if part.inline_data:
            with open(image_path, "wb") as f:
                f.write(part.inline_data.data)
            return True
    return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--deck", required=True)
    parser.add_argument("--dry-run", action="store_true", help="Show what would happen, without calling the API")
    args = parser.parse_args()

    deck_dir = os.path.join("decks", args.deck)
    cards_json_path = os.path.join(deck_dir, "cards.json")
    style_path = os.path.join(deck_dir, "style.txt")
    images_dir = os.path.join(deck_dir, "images")

    with open(cards_json_path, "r", encoding="utf-8") as f:
        deck = json.load(f)

    with open(style_path, "r", encoding="utf-8") as f:
        style_template = f.read().strip()

    os.makedirs(images_dir, exist_ok=True)

    to_generate = []
    for card in deck:
        image_path = os.path.join(images_dir, card["image_file"])
        exists = os.path.exists(image_path)
        status = "EXISTS" if exists else "MISSING"
        print(f"[{status}] {card['name']} -> {image_path}")
        if not exists:
            to_generate.append((card, image_path))

    print(f"\n{len(deck) - len(to_generate)} existing, {len(to_generate)} to generate")

    if args.dry_run:
        print("Dry run — no API calls made.")
        exit()

    for i, (card, image_path) in enumerate(to_generate, 1):
        print(f"[{i}/{len(to_generate)}] Generating {card['name']}...")
        try:
            success = generate_card_image(card, image_path, style_template)
            print(f"  {'Saved' if success else 'No image returned'}")
        except Exception as e:
            print(f"  ERROR: {e}")
        time.sleep(3)

    print("Done!")