# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A pipeline that produces vertical (1080x1920) tarot YouTube Shorts: pick a question and a card, generate a reading with Claude, narrate it with Gemini TTS, transcribe for word timings, and render a captioned video with MoviePy. There are no tests, no linter config and no README.

## Commands

Windows project; use the existing `venv/`.

```
venv\Scripts\activate
python main.py [--question "..."] [--card "The Fool"] [--language en|uk|es]   # CLI, one video
streamlit run app.py                                                          # interactive UI with review steps
python question_agent.py                                                      # try the question agent alone
python generate_cards.py --deck <name> [--dry-run]                            # generate deck card images (Gemini image model)
```

- Needs `ANTHROPIC_API_KEY` and `GEMINI_API_KEY` in `.env` (loaded via python-dotenv).
- Output goes to `output/<timestamp>_<card-slug>.{wav,mp4}`. Every run leaves a `.wav`, even if video rendering fails.
- Run everything from the repo root: paths like `decks/...`, `output/`, `assets/music/` and `question_history.json` are relative to the cwd.

## Architecture

Two entry points share the same modules: `main.py` (one-shot CLI) and `app.py` (Streamlit, staged: question -> card -> reading -> critique -> audio -> video, with state in `st.session_state`). `app.py` duplicates the orchestration in `main.py`, so a pipeline change usually has to be made in both.

Data flow: `question_agent.decide_question` -> `deck.pick_card` -> `ai_text.generate_tarot_reading` -> `ai_text.build_narration_script` -> `ai_text.translate_text` -> `voice.text_to_speech` -> `voice.transcribe_audio` (word timings) -> `video.create_video`.

- **Two AI providers.** Anthropic (`claude-sonnet-5`) does the text: `ai_text.py`, `question_agent.py`, `critique_agent.py`. Gemini does audio and images: TTS and transcription in `voice.py`, card art in `generate_cards.py`. Model IDs are hardcoded in each call.
- **Agents use forced tool calls** (`tool_choice` on `propose_question` / `critique_reading`) to get structured output. `critique_agent` is used only by `app.py`, not `main.py`.
- **`question_agent` keeps state** in `question_history.json` (last 20 questions) and passes it to the model to avoid repeats. It is gitignored but still tracked, which is why it shows as modified.
- **Decks** live in `decks/<name>/` with `cards.json` (`name`, `upright_meaning`, `image_file`, `scene`) and `images/`. The active deck is the hardcoded `DECK_DIR` in `deck.py` (`ukrainian-collage`); `ukrainian_modern` is not selectable without editing it.
- **Captions** come from Gemini word timestamps; `video.group_words` chunks them (3 words by default) into timed `TextClip`s over the card image. Background music is optional and picked from `assets/music/` (gitignored). `main.py` doesn't pass music; only the Streamlit UI does.

## Gotchas

- `video.py` hardcodes the font path `C:/Windows/Fonts/arial.ttf`, so video rendering is Windows-only as written.
- `requirements.txt` is UTF-16 encoded (a PowerShell `pip freeze >` artifact) and does not list `streamlit`, although `app.py` imports it. Note that `pip install -r` on the UTF-16 file may need re-encoding first.
- `voice.py` has a debug `print("FINISH REASON: ...")` left in `text_to_speech`.
- The Gemini TTS/image model names (`gemini-3.1-flash-tts-preview`, `gemini-3-pro-image`) are preview names and may change.
