import argparse
from moviepy import AudioClip
from pathlib import Path

def make_silence(duration, output_path):
    clip = AudioClip(lambda t: [0], duration=duration)
    clip.write_audiofile(str(output_path), fps=44100, logger=None)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("duration", type=float)
    parser.add_argument("output_path")
    args = parser.parse_args()
    make_silence(args.duration, Path(args.output_path))
