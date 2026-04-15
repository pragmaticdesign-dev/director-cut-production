import argparse, json, subprocess, sys
from pathlib import Path


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


def normalize_ratio(value: str) -> tuple[int, int]:
    val = value.lower()
    if val == "youtube":
        return (1920, 1080)
    if val in ("shorts", "portrait"):
        return (1080, 1920)
    return (1080, 1920)


def render_video_ffmpeg(job_path: str, output_path: str) -> None:
    data = json.loads(Path(job_path).read_text())
    base_dir = Path(job_path).parent
    width, height = normalize_ratio(data.get("ratio", "shorts"))

    segments: list[Path] = []

    for i, slide in enumerate(data["slides"]):
        img = (base_dir / slide["image"]).resolve()
        aud = (base_dir / slide["audio"]).resolve()
        seg_path = base_dir / f"seg_{i:02d}.ts"

        # Get the EXACT audio duration first
        duration = get_audio_duration(str(aud))

        # Build per-segment video using -t for precise duration control.
        # Key fixes vs old version:
        #   1. Use -t <duration> instead of -shortest (which is unreliable with -loop 1)
        #   2. Set explicit framerate with -r to avoid variable frame timing
        #   3. Output to MPEG-TS (.ts) for frame-accurate concat later
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-framerate", "30", "-i", str(img),
            "-i", str(aud),
            "-t", f"{duration:.6f}",
            "-c:v", "libx264", "-tune", "stillimage",
            "-r", "30",
            "-pix_fmt", "yuv420p",
            "-vf", (
                f"scale={width}:{height}"
                f":force_original_aspect_ratio=increase,"
                f"crop={width}:{height},setsar=1"
            ),
            "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart",
            str(seg_path),
        ]
        print(f"  🎬 Rendering segment {i+1}/{len(data['slides'])} "
              f"({duration:.3f}s) …")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"  ❌ Segment {i} failed:\n{result.stderr[-1500:]}")
            sys.exit(1)

        # Verify segment duration matches audio
        seg_dur = get_audio_duration(str(seg_path))
        drift = abs(seg_dur - duration)
        if drift > 0.1:
            print(f"  ⚠️  Segment {i} drift: {drift:.3f}s "
                  f"(expected {duration:.3f}s, got {seg_dur:.3f}s)")

        segments.append(seg_path)

    # Concatenate using concat demuxer with re-encode for consistent timestamps
    list_path = base_dir / "concat_list.txt"
    with open(list_path, "w") as f:
        for seg in segments:
            f.write(f"file '{seg}'\n")

    print(f"  🔗 Concatenating {len(segments)} segments …")
    cmd_concat = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(list_path),
        "-c:v", "libx264", "-preset", "fast",
        "-r", "30",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        str(output_path),
    ]
    result = subprocess.run(cmd_concat, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ❌ Concat failed:\n{result.stderr[-1500:]}")
        sys.exit(1)

    # Cleanup temp files
    list_path.unlink(missing_ok=True)
    for seg in segments:
        seg.unlink(missing_ok=True)

    # Final verification
    final_dur = get_audio_duration(str(output_path))
    expected = sum(
        get_audio_duration(str((base_dir / s["audio"]).resolve()))
        for s in data["slides"]
    )
    print(f"  ✅ Output: {output_path}")
    print(f"     Duration: {final_dur:.3f}s (expected {expected:.3f}s, "
          f"drift {abs(final_dur - expected):.3f}s)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Render a slideshow video from slideshow.json with "
                    "frame-accurate audio sync."
    )
    parser.add_argument("job_path", help="Path to slideshow.json")
    parser.add_argument("output_path", help="Path for output .mp4")
    args = parser.parse_args()
    render_video_ffmpeg(args.job_path, args.output_path)
