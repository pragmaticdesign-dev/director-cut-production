# Director Cut: Automated Video Production Pipeline 🎬✨

A high-fidelity production workflow for turning complex topics into visually stunning educational or explainer videos (optimized for YouTube Shorts). 

This system uses code-driven visuals (HTML/CSS) and AI-powered narration to produce polished, platform-ready content with frame-perfect synchronization.

## 🛠 Tech Stack & Tools
- **UI/UX Design**: Specialized **Coding Agents** to generate high-quality HTML/CSS scenes.
- **Image Generation**: Playwright rendering at 1080x1920 PNG (`render_code_image.py`).
- **TTS**: **Kokoro-82M** for high-quality, natural local voice generation (`tts.py`).
- **Composition**: Custom **Segment-Matching Engine** using MoviePy/FFmpeg for zero audio-video lag (`slideshow_composer.py`).
- **Subtitles**: **Faster-Whisper** + FFmpeg for drift-free, safe-zone subtitle burning (`burn_subtitles.py`).
- **Verification**: Built-in asset count and integrity checks via `ffprobe`.

## 📂 Project Structure
- `scripts/`: Core Python production scripts.
- `skills/`: Standardized production workflows and SOPs (`SKILL.md`).
- `YoutubeScripts/`: Project folders containing source code, assets, and metadata.

## 🚀 How to Create a Video

### 1. Define the Topic & Storyboard
Draft a 12-scene narration script. The rule of thumb: **2 words of TTS = ~1 second of video.**

### 2. Design the Visuals
Use a Coding Agent to build 12 HTML/CSS scenes based on the **"Cartoon Style Paper"** theme:
- Background: `#f5f0e8` (Beige paper).
- Borders: Thick (5px+), hand-drawn dark borders.
- Font: **Quicksand** (Rounded/Friendly).

### 3. Generate Assets
Run the TTS and Image rendering scripts to produce 12 synchronized pairs of audio and PNGs.

### 4. Verified Assembly
Use the `slideshow_composer.py` to merge assets. The system verifies the existence of all scenes and checks the final video integrity before proceeding.

### 5. Final Subtitles
Burn subtitles at `y=h-450` using bold black text to clear the YouTube Shorts UI.

---
Built by **Youtube Creater** 🚀🎯
