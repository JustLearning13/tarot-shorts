import os
import json
import random

DECK_DIR = "decks/ukrainian-collage"

def load_deck():
    with open(os.path.join(DECK_DIR, "cards.json"), "r", encoding="utf-8") as f:
        return json.load(f)

def pick_card(deck, card_name=None):
    if card_name:
        normalized = card_name.lower().replace("-", " ").replace("_", " ")
        for card in deck:
            if card["name"].lower() == normalized:
                return card
        raise ValueError(f"Card '{card_name}' not found in deck. Check spelling (e.g. 'The Fool', 'Three of Cups').")
    return random.choice(deck)