import os
import json
import uuid
import subprocess
import sys
import logging
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, send_file, jsonify
from flask_cors import CORS
from yt_dlp import YoutubeDL
from threading import Thread

# Monkey patch for yt-dlp compatibility issue
try:
    from yt_dlp.utils import _urllib_error_to_compat_http_error
except ImportError:
    pass

# Suppress BrokenPipeError
def ignore_broken_pipe(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except BrokenPipeError:
            pass
    return wrapper

# Suppress warnings from werkzeug about broken pipe
logging.getLogger('werkzeug').setLevel(logging.ERROR)

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
DOWNLOADS_DIR = Path("downloads")
TEMP_DIR = Path("temp")
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'ogg', 'm4a'}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

# Create folders if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
DOWNLOADS_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Store download status for YouTube downloads
downloads_status = {}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_audio_duration(file_path):
    """Get audio file duration in seconds using FFprobe"""
    try:
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            file_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            duration = float(result.stdout.strip())
            return duration
        return None
    except Exception as e:
        print(f"Error getting duration: {str(e)}")
        return None


def check_ffmpeg():
    """Check if ffmpeg is installed"""
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def download_and_convert(url, download_id):
    """Download video and convert to MP3"""
    try:
        downloads_status[download_id] = {
            "status": "downloading",
            "progress": 0,
            "message": "Starting download...",
        }

        temp_file = TEMP_DIR / f"{download_id}.%(ext)s"

        # Define progress hook function first
        def progress_hook(d):
            if d["status"] == "downloading":
                percent = d.get("_percent_str", "0%").strip().replace("%", "")
                try:
                    downloads_status[download_id]["progress"] = float(percent)
                except:
                    pass
                downloads_status[download_id]["message"] = f"Downloading... {d.get('_percent_str', '0%')}"
            elif d["status"] == "processing":
                downloads_status[download_id]["message"] = "Processing audio..."
                downloads_status[download_id]["progress"] = 95

        # Configure yt-dlp
        ydl_opts = {
            "format": "bestaudio/best",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
            "outtmpl": str(temp_file),
            "quiet": False,
            "no_warnings": False,
            "progress_hooks": [progress_hook],
            "socket_timeout": 30,
            "ignoreerrors": False,
            "no_color": True,
            "noplaylist": True,
        }

        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get("title", "audio")
        except AttributeError as ae:
            # Handle yt-dlp version compatibility issues
            if "_http_error" in str(ae):
                raise Exception(f"HTTP error during download. Please try again in a moment. (Error: {str(ae)[:100]})")
            raise

        # Find the converted MP3 file
        mp3_file = TEMP_DIR / f"{download_id}.mp3"

        if mp3_file.exists():
            # Move to downloads folder with sanitized name
            safe_title = "".join(c for c in title if c.isalnum() or c in (" ", "-", "_")).rstrip()
            output_file = DOWNLOADS_DIR / f"{safe_title}.mp3"

            # Handle duplicate filenames
            counter = 1
            while output_file.exists():
                output_file = DOWNLOADS_DIR / f"{safe_title}_{counter}.mp3"
                counter += 1

            mp3_file.rename(output_file)

            downloads_status[download_id] = {
                "status": "completed",
                "progress": 100,
                "message": "Download complete!",
                "file": output_file.name,
                "title": title,
            }
        else:
            raise Exception("MP3 file not created")

    except Exception as e:
        downloads_status[download_id] = {
            "status": "error",
            "progress": 0,
            "message": str(e),
        }
    finally:
        # Cleanup temp files
        for f in TEMP_DIR.glob(f"{download_id}*"):
            try:
                f.unlink()
            except:
                pass


# ==================== Routes ====================

@app.route('/')
def index():
    return render_template('index.html')


# ==================== YouTube Download Routes ====================

@app.route("/api/health", methods=["GET"])
def health():
    """Health check endpoint"""
    ffmpeg_installed = check_ffmpeg()
    return jsonify({
        "status": "ok",
        "ffmpeg_installed": ffmpeg_installed,
    })


@app.route("/api/youtube/download", methods=["POST"])
def youtube_download():
    """Start a YouTube download"""
    data = request.json
    url = data.get("url", "").strip()

    if not url:
        return jsonify({"error": "No URL provided"}), 400

    if not check_ffmpeg():
        return jsonify({"error": "FFmpeg not installed. Please install FFmpeg to use this service."}), 500

    download_id = str(uuid.uuid4())
    downloads_status[download_id] = {
        "status": "queued",
        "progress": 0,
        "message": "Queued for download...",
    }

    # Start download in background thread
    thread = Thread(target=download_and_convert, args=(url, download_id))
    thread.daemon = True
    thread.start()

    return jsonify({"download_id": download_id})


@app.route("/api/youtube/status/<download_id>", methods=["GET"])
def youtube_status(download_id):
    """Get YouTube download status"""
    if download_id not in downloads_status:
        return jsonify({"error": "Download not found"}), 404

    return jsonify(downloads_status[download_id])


@app.route("/api/youtube/download/<filename>", methods=["GET"])
def youtube_download_file(filename):
    """Download the YouTube MP3 file"""
    file_path = DOWNLOADS_DIR / filename

    if not file_path.exists():
        return jsonify({"error": "File not found"}), 404

    return send_file(file_path, as_attachment=True)


# ==================== Clip Routes ====================

@app.route('/api/clip/upload', methods=['POST'])
def clip_upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Unsupported file format'}), 400
        
        # Save uploaded file
        file_id = str(uuid.uuid4())
        file_extension = file.filename.rsplit('.', 1)[1].lower()
        temp_filename = f"{file_id}.{file_extension}"
        temp_path = os.path.join(UPLOAD_FOLDER, temp_filename)
        file.save(temp_path)
        
        # Get audio duration
        duration = get_audio_duration(temp_path)
        
        if duration is None:
            os.remove(temp_path)
            return jsonify({'error': 'Could not read audio file duration'}), 400
        
        return jsonify({
            'success': True,
            'file_id': file_id,
            'filename': file.filename,
            'duration': duration,
            'extension': file_extension
        }), 200
    
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@app.route('/api/clip/clip', methods=['POST'])
def clip_audio():
    try:
        data = request.get_json()
        
        file_id = data.get('file_id')
        start_time = float(data.get('start_time', 0))
        end_time = float(data.get('end_time', 0))
        extension = data.get('extension', 'mp3')
        
        if not file_id:
            return jsonify({'error': 'File ID is required'}), 400
        
        if start_time < 0 or end_time <= start_time:
            return jsonify({'error': 'Invalid time range'}), 400
        
        # Find the uploaded file
        input_filename = f"{file_id}.{extension}"
        input_path = os.path.join(UPLOAD_FOLDER, input_filename)
        
        if not os.path.exists(input_path):
            return jsonify({'error': 'File not found'}), 404
        
        # Generate output filename
        output_filename = f"clipped_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
        
        # Calculate duration
        duration = end_time - start_time
        
        # Use FFmpeg to clip the audio
        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-ss', str(start_time),
            '-t', str(duration),
            '-c:a', 'libmp3lame',
            '-b:a', '192k',
            '-y',
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            error_msg = result.stderr if result.stderr else "FFmpeg error"
            return jsonify({'error': f'Clipping failed: {error_msg}'}), 400
        
        return jsonify({
            'success': True,
            'message': 'Audio clipped successfully',
            'filename': output_filename
        }), 200
    
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@app.route('/api/clip/cleanup/<file_id>/<extension>', methods=['POST'])
def clip_cleanup_upload(file_id, extension):
    """Clean up uploaded file"""
    try:
        filename = f"{file_id}.{extension}"
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        
        if os.path.exists(file_path):
            os.remove(file_path)
            return jsonify({'success': True}), 200
        
        return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== Merge Routes ====================

@app.route('/api/merge/merge', methods=['POST'])
def merge_songs():
    try:
        # Check if files are in request
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided'}), 400
        
        files = request.files.getlist('files')
        
        if not files or len(files) < 2:
            return jsonify({'error': 'Please upload at least 2 files'}), 400
        
        # Validate files
        audio_files = []
        temp_files = []
        
        for file in files:
            if file.filename == '':
                continue
            
            if not allowed_file(file.filename):
                return jsonify({'error': f'File {file.filename} has unsupported format'}), 400
            
            # Save temporary file
            temp_filename = f"{uuid.uuid4()}_{file.filename}"
            temp_path = os.path.join(UPLOAD_FOLDER, temp_filename)
            file.save(temp_path)
            temp_files.append(temp_path)
            audio_files.append(temp_path)
        
        if len(audio_files) < 2:
            return jsonify({'error': 'Please upload at least 2 files'}), 400
        
        # Generate output filename
        output_filename = f"merged_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
        
        # Create concat file for ffmpeg
        concat_filename = f"concat_{uuid.uuid4()}.txt"
        concat_path = os.path.join(UPLOAD_FOLDER, concat_filename)
        
        try:
            with open(concat_path, 'w') as f:
                for audio_file in audio_files:
                    # Use absolute paths to avoid path resolution issues
                    abs_path = os.path.abspath(audio_file)
                    # Escape single quotes in filenames
                    escaped_path = abs_path.replace("'", "'\\''")
                    f.write(f"file '{escaped_path}'\n")
            
            # Use FFmpeg to merge files
            cmd = [
                'ffmpeg',
                '-f', 'concat',
                '-safe', '0',
                '-i', concat_path,
                '-c:a', 'libmp3lame',
                '-b:a', '192k',
                '-y',
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                error_msg = result.stderr if result.stderr else "FFmpeg error"
                return jsonify({'error': f'Merge failed: {error_msg}'}), 400
            
            # Clean up temporary files
            for temp_file in temp_files:
                try:
                    os.remove(temp_file)
                except:
                    pass
            
            try:
                os.remove(concat_path)
            except:
                pass
            
            return jsonify({
                'success': True,
                'message': 'Files merged successfully',
                'filename': output_filename
            }), 200
        
        except Exception as e:
            return jsonify({'error': f'Error merging files: {str(e)}'}), 400
    
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return jsonify({'error': f'Server error: {str(e)}'}), 500


# ==================== Common Download Routes ====================

@app.route('/api/download/<filename>')
def download_file(filename):
    try:
        file_path = os.path.join(OUTPUT_FOLDER, filename)
        abs_file_path = os.path.abspath(file_path)
        abs_output_folder = os.path.abspath(OUTPUT_FOLDER)
        
        # Security check - ensure file is in output folder
        if not abs_file_path.startswith(abs_output_folder):
            return jsonify({'error': 'Invalid file path'}), 403
        
        # Check if file exists
        if not os.path.exists(abs_file_path):
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(
            abs_file_path,
            mimetype='audio/mpeg',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        print(f"Download error: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@app.route('/api/cleanup-output/<filename>', methods=['POST'])
def cleanup_output(filename):
    """Clean up output file"""
    try:
        file_path = os.path.join(OUTPUT_FOLDER, filename)
        
        if os.path.exists(file_path):
            os.remove(file_path)
            return jsonify({'success': True}), 200
        
        return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # Use port 5001 to avoid conflicts with macOS AirPlay Receiver on port 5000
    app.run(debug=True, host='127.0.0.1', port=5001)

