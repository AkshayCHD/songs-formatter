# Songs Formatter

A unified web application that combines three powerful audio tools:
- **YouTube Downloader**: Download YouTube videos as MP3 files
- **Audio Clipper**: Clip and extract segments from audio files
- **Audio Merger**: Merge multiple audio files into one

## Features

### 🎵 YouTube Downloader
- Download YouTube videos as high-quality MP3 files
- Real-time download progress tracking
- Automatic audio conversion using FFmpeg

![YouTube Downloader](screenshots/youtube-downloader.png)

### ✂️ Audio Clipper
- Upload audio files (MP3, WAV, OGG, M4A)
- Visual timeline with start/end time sliders
- Preview audio before clipping
- Extract specific segments from audio files

![Audio Clipper](screenshots/audio-clipper.png)

### 🔀 Audio Merger
- Merge multiple audio files into one
- Support for MP3, WAV, OGG, M4A formats
- Drag and drop file selection
- Maintains audio quality during merge

![Audio Merger](screenshots/audio-merger.png)

## Requirements

- Internet connection (for YouTube downloads)
- **That's it!** The setup script will automatically install everything else.

## Quick Start (For Everyone!)

**🚀 One-Command Setup - No Technical Knowledge Required!**

1. **Download or clone this project to your computer**

2. **Open Terminal/Command Prompt and navigate to the project folder:**
   ```bash
   cd songs-formatter
   ```

3. **Run the setup script:**
   ```bash
   ./run.sh
   ```
   
   **That's it!** The script will automatically:
   - ✅ Detect your operating system (macOS, Linux, Windows)
   - ✅ Install Python 3.7+ if not already installed
   - ✅ Install FFmpeg for audio processing
   - ✅ Create a virtual environment
   - ✅ Install all required dependencies
   - ✅ Start the application
   
   **No manual installation needed!**

4. **Open your browser:**
   Navigate to `http://127.0.0.1:5001`

## What the Setup Script Does

The comprehensive `run.sh` script handles everything automatically:

### 🔍 **System Detection**
- Automatically detects your operating system
- Supports macOS, Ubuntu/Debian, CentOS, Arch Linux
- Provides clear instructions for Windows users

### 🐍 **Python Installation**
- Checks if Python 3.7+ is installed
- Automatically installs Python if missing
- Uses system package managers (brew, apt, yum, pacman)

### 🎵 **FFmpeg Installation**
- Checks if FFmpeg is available
- Automatically installs FFmpeg using system package managers
- Provides manual installation instructions when needed

### 📦 **Dependency Management**
- Creates isolated Python virtual environment
- Installs all required Python packages
- Upgrades pip to latest version

### 🎯 **Smart Error Handling**
- Colored output for easy reading
- Clear error messages and solutions
- Graceful handling of interruptions
- Verification of all installations

## Manual Installation (Advanced Users)

If you prefer to install dependencies manually:

1. **Install Python 3.7+**
2. **Install FFmpeg**
3. **Make the script executable:**
   ```bash
   chmod +x run.sh
   ```
4. **Run the application:**
   ```bash
   ./run.sh
   ```

## Usage

### YouTube Downloader
1. Click on the "YouTube Download" tab
2. Paste a YouTube URL
3. Click "Download"
4. Wait for the download to complete
5. Click "Download MP3" to save the file

### Audio Clipper
1. Click on the "Clip Audio" tab
2. Upload an audio file (drag & drop or click to browse)
3. Use the sliders to set start and end times
4. Preview the audio using the player
5. Click "Clip Audio" to process
6. Download the clipped file

### Audio Merger
1. Click on the "Merge Files" tab
2. Upload multiple audio files (at least 2)
3. Remove files if needed using the "Remove" button
4. Click "Merge Files" to combine them
5. Download the merged file

## Project Structure

```
songs-formatter/
├── app.py                 # Flask backend application
├── templates/
│   └── index.html        # Frontend HTML with all three tools
├── requirements.txt      # Python dependencies
├── run.sh                # Startup script
├── README.md             # This file
├── uploads/              # Temporary upload directory (auto-created)
├── outputs/              # Output files directory (auto-created)
├── downloads/            # YouTube downloads directory (auto-created)
└── temp/                 # Temporary files directory (auto-created)
```

## API Endpoints

### YouTube Download
- `POST /api/youtube/download` - Start YouTube download
- `GET /api/youtube/status/<download_id>` - Get download status
- `GET /api/youtube/download/<filename>` - Download MP3 file

### Audio Clipping
- `POST /api/clip/upload` - Upload audio file for clipping
- `POST /api/clip/clip` - Clip audio file
- `POST /api/clip/cleanup/<file_id>/<extension>` - Clean up uploaded file

### Audio Merging
- `POST /api/merge/merge` - Merge multiple audio files

### Common
- `GET /api/download/<filename>` - Download output file
- `POST /api/cleanup-output/<filename>` - Clean up output file
- `GET /api/health` - Health check

## Technical Details

- **Backend**: Flask (Python)
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **Audio Processing**: FFmpeg
- **YouTube Download**: yt-dlp
- **CORS**: Enabled for cross-origin requests
- **Default Port**: 5001 (changed from 5000 to avoid macOS AirPlay Receiver conflicts)

## Notes

- Maximum file size: 100MB per upload
- Supported audio formats: MP3, WAV, OGG, M4A
- Output format: MP3 (192kbps)
- Files are automatically cleaned up after processing
- The application runs on `http://127.0.0.1:5001` by default (port 5001 to avoid conflicts with macOS AirPlay Receiver)

## Troubleshooting

### Setup Script Issues

**"Permission denied" error:**
```bash
chmod +x run.sh
./run.sh
```

**Script stops with "command not found":**
- On macOS: Install Homebrew first: https://brew.sh/
- On Linux: Make sure you have sudo privileges
- On Windows: Use Git Bash or WSL

**Python installation fails:**
- On macOS: Install Xcode command line tools: `xcode-select --install`
- On Linux: Update package manager: `sudo apt update` or `sudo yum update`
- Manual installation: Download from https://python.org

**FFmpeg installation fails:**
- On macOS: Install Homebrew first
- On Linux: Try updating package lists first
- Manual installation: https://ffmpeg.org/download.html

### Application Issues

**FFmpeg not found after installation:**
- Restart your terminal/command prompt
- Check installation with: `ffmpeg -version`
- On Windows: Make sure FFmpeg is in your PATH

**YouTube download fails:**
- Check your internet connection
- Verify the YouTube URL is valid
- Some videos may be restricted or unavailable
- Try updating yt-dlp: `pip install --upgrade yt-dlp`

**File upload fails:**
- Check file size (max 100MB)
- Verify file format is supported (MP3, WAV, OGG, M4A)
- Ensure sufficient disk space

**Virtual environment issues:**
- Delete the `venv` folder and run `./run.sh` again
- Make sure you have write permissions in the project directory

**Port already in use:**
- The app uses port 5001 by default to avoid macOS AirPlay Receiver conflicts
- If port 5001 is in use, kill the process: `lsof -ti:5001 | xargs kill -9` (macOS/Linux)
- Or change the port in `app.py` (line 516)

## License

This project is open source and available for personal use.

