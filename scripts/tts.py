import argparse
import soundfile as sf
from kokoro import KPipeline
import os

def generate_tts(text, output_file, voice="af_heart", lang_code="a"):
    """
    Generate TTS using Kokoro-82M.
    lang_code 'a' for American English, 'b' for British English.
    Voices: af_heart, af_bella, af_nicole, af_sky, am_adam, am_michael,
            bf_isabelle, bf_alice, bm_george, bm_lewis, etc.
    """
    # Initialize pipeline
    pipeline = KPipeline(lang_code=lang_code)
    
    # Generate audio
    generator = pipeline(text, voice=voice, speed=1, split_pattern=r'\n+')
    
    # Collect all audio chunks
    all_audio = []
    for gs, ps, audio in generator:
        all_audio.append(audio)
    
    if not all_audio:
        raise ValueError("No audio was generated.")
    
    # Concatenate audio chunks
    import numpy as np
    final_audio = np.concatenate(all_audio)
    
    # Save to file (24kHz is Kokoro's native rate)
    sf.write(output_file, final_audio, 24000)
    print(f"Audio saved to {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate TTS using Kokoro-82M")
    parser.add_argument("text", help="Text to convert to speech")
    parser.add_argument("output_file", help="Path to the output audio file")
    parser.add_argument("--voice", default="af_heart", help="Voice to use (default: af_heart)")
    parser.add_argument("--lang", default="a", help="Language code (a=US, b=UK)")
    args = parser.parse_args()

    # Ensure output directory exists
    os.makedirs(os.path.dirname(os.path.abspath(args.output_file)), exist_ok=True)
    
    generate_tts(args.text, args.output_file, args.voice, args.lang)
