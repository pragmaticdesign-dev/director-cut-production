import argparse, json, subprocess, os
from pathlib import Path

def normalize_ratio(value):
    val = value.lower()
    if val == "youtube": return (1920, 1080)
    if val in ["shorts", "portrait"]: return (1080, 1920)
    return (1080, 1920)

def render_video_ffmpeg(job_path, output_path):
    data = json.loads(Path(job_path).read_text())
    base_dir = Path(job_path).parent
    width, height = normalize_ratio(data.get('ratio', 'shorts'))
    
    segments = []
    for i, slide in enumerate(data['slides']):
        img = (base_dir / slide['image']).resolve()
        aud = (base_dir / slide['audio']).resolve()
        seg_path = base_dir / f"seg_{i:02d}.mp4"
        
        # Exact segment matching audio duration
        cmd = [
            "ffmpeg", "-y", "-loop", "1", "-i", str(img), "-i", str(aud),
            "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p",
            "-vf", f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},setsar=1",
            "-c:a", "aac", "-shortest",
            str(seg_path)
        ]
        subprocess.run(cmd, check=True)
        segments.append(seg_path)
    
    # Concat
    list_path = base_dir / "concat_list.txt"
    with open(list_path, "w") as f:
        for seg in segments:
            f.write(f"file '{seg.name}'\n")
            
    cmd_concat = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_path),
        "-c", "copy", str(output_path)
    ]
    subprocess.run(cmd_concat, check=True)
    
    # Clean
    list_path.unlink()
    for seg in segments: seg.unlink()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("job_path"); parser.add_argument("output_path")
    args = parser.parse_args()
    render_video_ffmpeg(args.job_path, args.output_path)
