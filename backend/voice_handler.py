import whisper
from gtts import gTTS
import os

# Load Whisper model once (base model — fast and accurate)
print("🎙️ Loading Whisper model...")
whisper_model = whisper.load_model("base")
print("✅ Whisper model loaded!")

def speech_to_text(audio_file_path: str) -> str:
    """Convert audio file to text"""
    print(f"🎙️ Transcribing: {audio_file_path}")
    result = whisper_model.transcribe(audio_file_path)
    text = result["text"].strip()
    print(f"📝 Transcribed: {text}")
    return text

def text_to_speech(text: str, language: str = "hindi") -> str:
    """Convert text to speech and save as mp3"""
    lang_code = "hi"
    if language == "marathi":
        lang_code = "mr"
    elif language == "english":
        lang_code = "en"

    print(f"🔊 Converting to speech ({lang_code})...")
    output_path = "voice_output.mp3"
    tts = gTTS(text=text, lang=lang_code, slow=False)
    tts.save(output_path)
    print(f"✅ Audio saved: {output_path}")
    return output_path