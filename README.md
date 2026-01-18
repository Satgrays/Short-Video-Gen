```markdown
# Brainrot Generator

Automated short-form vertical video generator with AI-powered script generation, text-to-speech, and synchronized subtitles.

## Features

- AI script generation using Groq API (Llama 3.3 70B)
- Text-to-speech with Edge TTS (free, unlimited) or ElevenLabs
- Automatic transcription with word-level timestamps using Groq Whisper
- Animated subtitle generation with bounce effects
- Vertical video format (1080x1920) optimized for TikTok/YouTube Shorts
- Customizable fonts, colors, and styling

## Requirements

- Python 3.11+
- ffmpeg
- ffprobe

### Python Dependencies

```bash
pip install moviepy groq edge-tts python-dotenv requests numpy Pillow
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/brainrot-generator.git
cd brainrot-generator
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your API keys:
```bash
GROQ_API_KEY=your_groq_api_key_here
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here  # Optional
```

4. Set up your configuration in `config/config.json`

5. Add background videos to the `videos/` directory

6. Add fonts to the `fonts/` directory (default: PassionOne-Bold.ttf)

## Project Structure

```
brainrot-generator/
├── config/
│   ├── config.py
│   └── config.json
├── controllers/
│   ├── script_controller.py
│   └── creation_controller.py
├── fonts/
│   └── PassionOne-Bold.ttf
├── videos/                    # Background videos
├── content/                   # Generated videos
├── main.py
├── fix_videos.py
└── .env
```

## Usage

### Generate a video from scratch

```bash
python main.py generate \
  --video_title "My Video Title" \
  --user_input "Topic or prompt for the video"
```

Optional: Provide a custom system prompt:
```bash
python main.py generate \
  --video_title "My Video Title" \
  --system_input "You are a motivational speaker..." \
  --user_input "Give me 3 productivity tips"
```

### Generate video from existing audio

```bash
python main.py transcript \
  --video_title "My Video" \
  --audio_path "path/to/audio.mp3"
```

### Workflow

1. Script is generated using Groq AI
2. User reviews and edits the script (press ENTER when ready)
3. Audio is generated from the script using Edge TTS
4. Transcript with word-level timestamps is generated using Groq Whisper
5. Video is assembled with background footage, subtitles, and title

## Configuration

Edit `config/config.json` to customize:

### Video Settings
- `width`: Video width (default: 1080)
- `height`: Video height (default: 1920)
- `title_duration`: Duration of title display in seconds
- `title_fontsize`: Font size for title
- `title_position`: Position of title [x, y]

### Text Clip Settings
- `fontsize`: Subtitle font size
- `color`: Subtitle color
- `font`: Path to font file
- `stroke_color`: Subtitle outline color
- `stroke_width`: Subtitle outline width
- `crossfade_duration`: Fade-in duration for subtitles

### Audio Settings

Edge TTS (free, unlimited):
```json
"edge": {
  "voice": "en-US-GuyNeural",
  "rate": "+0%",
  "pitch": "+0Hz"
}
```

Available voices:
- `en-US-GuyNeural` - Male US
- `en-US-JennyNeural` - Female US
- `en-US-AriaNeural` - Female US (energetic)
- `en-GB-RyanNeural` - Male UK
- `en-AU-WilliamNeural` - Male Australian

ElevenLabs (requires API key and credits):
```json
"elevenlabs": {
  "model_id": "pNInz6obpgDQGcFmaJgB",
  "model": "eleven_monolingual_v1",
  "voice_settings": {
    "stability": 0.5,
    "similarity_boost": 0.5
  }
}
```

### Script Settings
- `model`: Groq model to use (default: llama-3.3-70b-versatile)

## Video Metadata Fix Utility

If your videos have incorrect rotation metadata, use the included fix utility:

### Check video metadata
```bash
python fix_videos.py check videos/my_video.mp4
python fix_videos.py check videos/
```

### Fix video metadata
```bash
python fix_videos.py fix videos/
python fix_videos.py fix videos/ videos_fixed/
```

This will:
- Detect rotation metadata issues
- Apply physical rotation if needed
- Output corrected videos

## Output

Generated videos are saved in:
```
content/
└── Video_Title/
    ├── script.txt
    ├── audio.mp3
    ├── transcript.json
    ├── details.json
    └── final_video.mp4
```

## Troubleshooting

### Videos are stretched or rotated incorrectly

1. Check your video dimensions:
```bash
python fix_videos.py check videos/your_video.mp4
```

2. If dimensions are inverted (e.g., 1596x720 instead of 720x1596), the script will automatically correct them during processing.

3. Alternatively, use the fix utility to pre-process all videos:
```bash
python fix_videos.py fix videos/
```

### Edge TTS not pronouncing contractions correctly

The script automatically normalizes apostrophes and quotes. If issues persist, edit the script manually after generation.

### No background videos found

Ensure you have .mp4 files in the `videos/` directory. Videos should be:
- Vertical format (or will be rotated automatically)
- Longer than your audio duration
- Preferably 1080x1920 or similar vertical resolution

### Subtitles appearing in wrong position

Adjust `subtitle_y_position` in `creation_controller.py`:
```python
subtitle_y_position = video_height - 900  # Increase to move up, decrease to move down
```

## API Keys

### Groq API (Required)
Get your free API key at: https://console.groq.com

Groq provides:
- Fast LLM inference (script generation)
- Whisper API (transcription)

### ElevenLabs API (Optional)
Get your API key at: https://elevenlabs.io

Free tier: 10,000 characters/month (resets monthly)

Note: Edge TTS is recommended as it's free and unlimited.

## License

MIT

## Contributing

Contributions are welcome. Please open an issue or submit a pull request.

## Credits

- Groq for AI inference and transcription
- Edge TTS for text-to-speech
- MoviePy for video processing
- ElevenLabs for premium TTS (optional)
```