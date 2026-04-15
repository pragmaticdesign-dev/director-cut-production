import argparse
import json
import subprocess
from pathlib import Path
from faster_whisper import WhisperModel

# --- Configuration defaults ---
DEFAULT_COLOR = "black"
DEFAULT_FONTSIZE = 52
DEFAULT_FONT = "Helvetica-Bold"
DEFAULT_Y_EXPR = "h-450"
MAX_WORDS_PER_CHUNK = 3


def get_audio_duration(audio_path: str) -> float:
    """Get exact audio duration using ffprobe."""
    result = subprocess.run(
        [
            "ffprobe", "-v", "quiet",
            "-show_entries", "format=duration",
            "-of", "csv=p=0",
            str(audio_path),
        ],
        capture_output=True, text=True, check=True,
    )
    return float(result.stdout.strip())


def transcribe_video(video_path):
    """Transcribe a single video/audio file using faster-whisper."""
    model = WhisperModel("base", device="cpu", compute_type="int8")
    segments, _ = model.transcribe(str(video_path), word_timestamps=True)
    return list(segments)


def transcribe_per_slide(slideshow_json_path):
    """Transcribe each audio file from slideshow.json individually.

    This avoids drift: each audio is transcribed independently and its
    timestamps are shifted by the cumulative offset of all prior audio
    durations. The result is a flat list of chunks whose timestamps are
    correct relative to the final concatenated video timeline.
    """
    data = json.loads(Path(slideshow_json_path).read_text())
    base_dir = Path(slideshow_json_path).parent

    model = WhisperModel("base", device="cpu", compute_type="int8")

    all_chunks = []
    cumulative_offset = 0.0

    for slide in data["slides"]:
        audio_path = str((base_dir / slide["audio"]).resolve())
        duration = get_audio_duration(audio_path)

        segments, _ = model.transcribe(audio_path, word_timestamps=True)

        for seg in segments:
            words = seg.words if hasattr(seg, "words") and seg.words else []

            if words:
                for i in range(0, len(words), MAX_WORDS_PER_CHUNK):
                    group = words[i : i + MAX_WORDS_PER_CHUNK]
                    text = " ".join(w.word.strip() for w in group)
                    t_start = cumulative_offset + group[0].start
                    t_end = cumulative_offset + group[-1].end
                    all_chunks.append({
                        "text": text,
                        "start": t_start,
                        "end": t_end,
                    })
            else:
                # Fallback: no word-level timestamps
                raw = seg.text.strip().split()
                total_words = len(raw)
                if total_words == 0:
                    continue
                seg_duration = seg.end - seg.start
                words_so_far = 0
                for j in range(0, total_words, MAX_WORDS_PER_CHUNK):
                    group = raw[j : j + MAX_WORDS_PER_CHUNK]
                    t_start = (cumulative_offset + seg.start
                               + (words_so_far / total_words) * seg_duration)
                    words_so_far += len(group)
                    t_end = (cumulative_offset + seg.start
                             + (words_so_far / total_words) * seg_duration)
                    all_chunks.append({
                        "text": " ".join(group),
                        "start": t_start,
                        "end": t_end,
                    })

        # Advance offset by exact audio duration (not transcription end)
        cumulative_offset += duration

    return all_chunks


def _escape_drawtext(text: str) -> str:
    """Escape text for FFmpeg drawtext filter."""
    text = text.replace("\\", "\\\\")
    text = text.replace(":", "\\:")
    text = text.replace("'", "’")
    text = text.replace(";", "\\;")
    text = text.replace("%", "%%")
    return text


def chunk_words(segment, max_words=MAX_WORDS_PER_CHUNK):
    """Split a transcription segment into smaller word-groups."""
    words = segment.words if hasattr(segment, "words") and segment.words else []

    if not words:
        raw = segment.text.strip().split()
        chunks = []
        total_words = len(raw)
        if total_words == 0:
            return []
        duration = segment.end - segment.start
        words_so_far = 0
        for i in range(0, total_words, max_words):
            group = raw[i : i + max_words]
            t_start = segment.start + (words_so_far / total_words) * duration
            words_so_far += len(group)
            t_end = segment.start + (words_so_far / total_words) * duration
            chunks.append({
                "text": " ".join(group),
                "start": t_start,
                "end": t_end,
            })
        return chunks

    chunks = []
    for i in range(0, len(words), max_words):
        group = words[i : i + max_words]
        text = " ".join(w.word.strip() for w in group)
        t_start = group[0].start
        t_end = group[-1].end
        chunks.append({"text": text, "start": t_start, "end": t_end})
    return chunks


def build_drawtext_filters(chunks, color, fontsize, font, y_expr):
    """Build FFmpeg drawtext filter strings from word chunks."""
    filters = []
    for c in chunks:
        escaped = _escape_drawtext(c["text"])
        f = (
            f"drawtext=text='{escaped}'"
            f":fontcolor={color}"
            f":fontsize={fontsize}"
            f":fontfile=''"
            f":font={font}"
            f":x=(w-text_w)/2"
            f":y={y_expr}"
            f":enable='between(t,{c['start']:.3f},{c['end']:.3f})'"
        )
        filters.append(f)
    return filters


def burn_subtitles(
    video_path,
    chunks,
    output_path,
    color=DEFAULT_COLOR,
    fontsize=DEFAULT_FONTSIZE,
    font=DEFAULT_FONT,
    y_expr=DEFAULT_Y_EXPR,
):
    """Burn pre-computed subtitle chunks into video_path."""
    if not chunks:
        print("\u26a0  No subtitle chunks produced — copying video unchanged.")
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(video_path), "-c", "copy",
             str(output_path)],
            capture_output=True,
        )
        return

    filters = build_drawtext_filters(chunks, color, fontsize, font, y_expr)
    vf = ",".join(filters)

    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-vf", vf,
        "-c:v", "libx264",
        "-preset", "fast",
        "-c:a", "copy",
        str(output_path),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"\u26a0  FFmpeg failed (exit {result.returncode}):")
        print(result.stderr[-2000:] if result.stderr else "(no stderr)")
    else:
        print(f"\u2705 Subtitled video saved → {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Burn word-chunked subtitles onto a video."
    )
    parser.add_argument("video_path", help="Path to input video")
    parser.add_argument(
        "--slideshow-json", default=None,
        help="Path to slideshow.json for per-slide transcription "
             "(recommended for sync accuracy). If omitted, transcribes "
             "the video directly.",
    )
    parser.add_argument(
        "--color", default=DEFAULT_COLOR,
        help=f"Font colour (default: {DEFAULT_COLOR})",
    )
    parser.add_argument(
        "--fontsize", type=int, default=DEFAULT_FONTSIZE,
        help=f"Font size in pixels (default: {DEFAULT_FONTSIZE})",
    )
    parser.add_argument(
        "--font", default=DEFAULT_FONT,
        help=f"Font family name (default: {DEFAULT_FONT})",
    )
    parser.add_argument(
        "--y-expr", default=DEFAULT_Y_EXPR,
        help=f"FFmpeg Y position expression (default: {DEFAULT_Y_EXPR})",
    )
    parser.add_argument(
        "--max-words", type=int, default=MAX_WORDS_PER_CHUNK,
        help=f"Max words per subtitle line (default: {MAX_WORDS_PER_CHUNK})",
    )

    args = parser.parse_args()
    vp = Path(args.video_path)
    out = vp.with_name(f"{vp.stem}_subtitled.mp4")

    if args.slideshow_json:
        # Per-slide transcription: timestamps anchored to audio durations
        print("📝 Transcribing per-slide for drift-free subtitles …")
        chunks = transcribe_per_slide(args.slideshow_json)
    else:
        # Fallback: transcribe the video directly
        print("📝 Transcribing video directly …")
        segs = transcribe_video(vp)
        chunks = []
        for seg in segs:
            chunks.extend(chunk_words(seg, max_words=args.max_words))

    burn_subtitles(
        vp, chunks, out,
        color=args.color,
        fontsize=args.fontsize,
        font=args.font,
        y_expr=args.y_expr,
    )
    print(out)
