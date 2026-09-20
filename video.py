from moviepy import ImageClip, AudioFileClip, TextClip, CompositeVideoClip, ColorClip, CompositeAudioClip
from moviepy.audio.fx import AudioLoop, MultiplyVolume, AudioFadeIn, AudioFadeOut

def group_words(words, chunk_size=3):
    """Groups the word list into small phrases with combined start/end times."""
    chunks = []
    for i in range(0, len(words), chunk_size):
        group = words[i:i + chunk_size]
        text = " ".join(w["word"] for w in group)
        start = group[0]["start"]
        end = group[-1]["end"]
        chunks.append({"text": text, "start": start, "end": end})
    return chunks

def create_video(card_image_path, words, audio_file, output_file, music_file=None, chunk_size=3):
    audio = AudioFileClip(audio_file)
    duration = audio.duration

    if music_file:
        music = AudioFileClip(music_file)
        music = music.with_effects([
                AudioLoop(duration=duration),
                MultiplyVolume(0.12),
                AudioFadeIn(1.0),
                AudioFadeOut(1.5)
        ])
        final_audio = CompositeAudioClip([audio, music])
    else:
        final_audio = audio

    image_clip = ImageClip(card_image_path).with_duration(duration)
    image_clip = image_clip.resized(height=1920)
    image_clip = image_clip.with_position(("center", "center"))

    chunks = group_words(words, chunk_size)

    bottom_margin = 100
    box_height = 220  # was 160 — bigger to fit larger font + descenders

    box_y = 1920 - bottom_margin - box_height

    bg_box = ColorClip(size=(1080, box_height), color=(0, 0, 0))
    bg_box = bg_box.with_opacity(0.55).with_duration(duration)
    bg_box = bg_box.with_position(("center", box_y))

    caption_clips = []
    for chunk in chunks:
        clip_duration = max(chunk["end"] - chunk["start"], 0.1)

        text_clip = TextClip(
            text=chunk["text"],
            font_size=58,                 # was 44
            color="white",
            size=(1000, box_height - 20), # was (1000, None) — fixed height, not auto-cropped
            method="caption",
            font="C:/Windows/Fonts/arial.ttf",
            stroke_color="black",
            stroke_width=1
        )
        text_clip = text_clip.with_start(chunk["start"]).with_duration(clip_duration)
        text_clip = text_clip.with_position(("center", box_y + (box_height - text_clip.h) // 2))
        caption_clips.append(text_clip)

    video = CompositeVideoClip([image_clip, bg_box, *caption_clips], size=(1080, 1920))
    video = video.with_audio(final_audio)   # was: video.with_audio(audio)

    video.write_videofile(output_file, fps=24, logger="bar")
    print(f"Video saved to {output_file}")