# Director Cut Video Project Workflow (Pro v4 - Synced Paper Edition)

A high-fidelity production workflow for turning complex topics into "Cartoon Style Paper" educational videos (9:16 vertical) with perfect audio-video synchronization.

## 🛠 Tech Stack
- **Design**: `spawn_coder` for HTML/CSS using the "Cartoon Paper" theme.
- **Image**: Playwright rendering at 1080x1920 PNG (`render_code_image.py`).
- **Audio**: Kokoro-82M TTS (`tts.py`).
- **Composition**: MoviePy segment-matching engine (`slideshow_composer.py`).
- **Subtitles**: Faster-Whisper + FFmpeg (`burn_subtitles.py`).

## 🎨 Mandatory Theme: "Cartoon Style Paper"
- **Background**: `#f5f0e8` (Beige paper texture feel).
- **Borders**: Thick (5px+), hand-drawn dark borders (`#3b3b3b`).
- **Accents**: Soft pastels (Green, Peach, Blue, Pink).
- **Typography**: 'Quicksand' (Rounded, friendly).
- **Style**: Everything should look like a structured card on a paper background with "Pill" labels.

## 🚀 Correct Workflow
1. **Topic & Storyboard**: Collect topic and draft a 12-scene narration.
2. **Design (Coder Agent)**: Spawn a coder to build all HTML/CSS scenes. **CRITICAL**: The coder must follow the "Cartoon Paper" theme.
3. **Asset Generation**:
   - Generate TTS for all narration first.
   - Render all HTML scenes to PNG.
   - **Verify**: Ensure 12 PNGs and 12 MP3s exist.
4. **Synced Composition**:
   - Run `slideshow_composer.py`. It matches each image clip exactly to the length of its audio clip.
5. **Subtitles**:
   - Burn subtitles at `y=h-450` (safe zone) in black text.
6. **Delivery**: Upload and notify via Telegram.
