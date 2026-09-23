import os
import wave
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def text_to_speech(text, output_file, language="en"):
    style = (
        "Say this like you're talking to a close friend, not reading a script — "
        "warm, a little informal, with natural pauses and thoughtful hesitations "
        "where a real person would pause mid-sentence, not perfectly smooth. "
        "Mystical and calming, but conversational, not stiff or overly formal."
    )
    if language == "uk":
        style += (
            " Speak with a Western Ukrainian accent, closer to Galician or "
            "Carpathian regional pronunciation rather than standard Kyiv "
            "broadcast Ukrainian, if that distinction is achievable."
        )

    response = gemini_client.models.generate_content(
        model="gemini-3.1-flash-tts-preview",
        contents=f"{style} {text}",
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Kore")
                )
            ),
        )
    )

    audio_data = response.candidates[0].content.parts[0].inline_data.data

    with wave.open(output_file, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(24000)
        wf.writeframes(audio_data)

    print(f"Audio saved to {output_file}")

def transcribe_audio(audio_path):
    """Returns a list of {'word': str, 'start': float, 'end': float}."""
    audio_file = gemini_client.files.upload(file=audio_path)

    response = gemini_client.models.generate_content(
        model="gemini-3.5-transcribe",
        contents=[audio_file],
        config=types.GenerateContentConfig(
            audio_transcription_config=types.AudioTranscriptionConfig(
                word_timestamp=True,
            )
        ),
    )

    words = response.candidates[0].content.parts[0].audio_transcription.words

    return [
        {
            "word": w.word,
            "start": float(w.start_offset.rstrip("s")),
            "end": float(w.end_offset.rstrip("s")),
        }
        for w in words
    ]