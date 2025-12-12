import os
import sys
import logging
import uuid
import shutil
import socket
import yt_dlp
from glob import glob
from flask import (
    Flask, request, send_file, flash, redirect, url_for, render_template
)

# Increase socket timeout globally for downloads
socket.setdefaulttimeout(300)

app = Flask(__name__)
# Use environment variable for secret in production; fallback for local testing
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "change_this_for_production")

# Folder where downloads are saved
DOWNLOAD_FOLDER = os.environ.get("DOWNLOAD_FOLDER", "downloads")
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)

# QUALITY MAP for front-end values: a,b,c,d,e and 'audio'
QUALITY_MAP = {
    "a": "bestvideo[height=2160]+bestaudio/best",   # 4K
    "b": "bestvideo[height=1440]+bestaudio/best",   # 2K
    "c": "bestvideo[height=1080]+bestaudio/best",   # 1080p
    "d": "bestvideo[height=720]+bestaudio/best",    # 720p
    "e": "bestvideo[height=480]+bestaudio/best",    # 480p
}

AUDIO_FORMAT = "bestaudio/best"


# -----------------------------
# Utility functions
# -----------------------------

def safe_basename(prefix: str) -> str:
    """Return a safe unique basename prefix for output files."""
    return f"{prefix}_{uuid.uuid4().hex}"


def find_file_with_prefix(prefix: str):
    """Find a file in DOWNLOAD_FOLDER that starts with prefix and return full path."""
    pattern = os.path.join(DOWNLOAD_FOLDER, f"{prefix}*")
    matches = sorted(glob(pattern))
    return matches[0] if matches else None


# -----------------------------
# Home page
# -----------------------------
@app.route("/", methods=["GET"])
def index():
    # serve the index.html in templates
    return render_template("index.html")


# -----------------------------
# MAIN DOWNLOAD ROUTE
# -----------------------------
@app.route("/download", methods=["POST"])
def download():
    try:
        # read from form (because the HTML uses method="post")
        mode = (request.form.get("mode") or "video").lower()
        url = (request.form.get("url") or "").strip()
        quality = request.form.get("quality", "e")

        if not url:
            flash("No URL provided!", "error")
            return redirect(url_for("index"))

        # Check for cookies.txt in app root
        cookie_file = os.path.join(app.root_path, "cookies.txt")
        ignore_cookies = not os.path.exists(cookie_file)
        if not ignore_cookies:
            app.logger.info("Found cookies.txt, using it for authentication.")
        else:
            app.logger.warning("cookies.txt not found. YouTube may block requests.")

        # AUDIO (MP3)
        if mode in ("mp3", "audio"):
            prefix = safe_basename("audio")
            outtmpl = os.path.join(DOWNLOAD_FOLDER, f"{prefix}.%(ext)s")

            ydl_opts = {
                "format": AUDIO_FORMAT,
                "outtmpl": outtmpl,
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
                "noplaylist": True,
                # yt-dlp verbosity: set to False to let Flask logs be clearer
                "quiet": False,
                # Timeout settings for slow networks (Render, etc.)
                "socket_timeout": 300,
                "http_chunk_size": 10485760,  # 10MB chunks
                "retries": 10,
                "fragment_retries": 10,
                "file_access_retries": 10,
                "skip_unavailable_fragments": True,
            }

            if not ignore_cookies:
                ydl_opts["cookiefile"] = cookie_file

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            found = find_file_with_prefix(prefix)
            if not found:
                flash("Audio conversion failed or file not found.", "error")
                return redirect(url_for("index"))

            return send_file(found, as_attachment=True)

        # VIDEO (single)
        elif mode == "video":
            fmt = QUALITY_MAP.get(quality, QUALITY_MAP["e"])
            prefix = safe_basename("video")
            outtmpl = os.path.join(DOWNLOAD_FOLDER, f"{prefix}.%(ext)s")

            ydl_opts = {
                "format": fmt,
                "outtmpl": outtmpl,
                "merge_output_format": "mp4",
                "noplaylist": True,
                "quiet": False,
                # Timeout settings for slow networks (Render, etc.)
                "socket_timeout": 300,
                "http_chunk_size": 10485760,  # 10MB chunks
                "retries": 10,
                "fragment_retries": 10,
                "file_access_retries": 10,
                "skip_unavailable_fragments": True,
            }

            if not ignore_cookies:
                ydl_opts["cookiefile"] = cookie_file

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            found = find_file_with_prefix(prefix)
            if not found:
                flash("Video download failed or file not found.", "error")
                return redirect(url_for("index"))

            return send_file(found, as_attachment=True)

        # PLAYLIST
        elif mode == "playlist":
            fmt = QUALITY_MAP.get(quality, QUALITY_MAP["e"])
            playlist_id = uuid.uuid4().hex
            playlist_folder = os.path.join(DOWNLOAD_FOLDER, f"pl_{playlist_id}")
            os.makedirs(playlist_folder, exist_ok=True)

            ydl_opts = {
                "format": fmt,
                "outtmpl": os.path.join(playlist_folder, "%(playlist_index)s - %(title)s.%(ext)s"),
                "merge_output_format": "mp4",
                "ignoreerrors": True,
                "quiet": False,
                # Timeout settings for slow networks (Render, etc.)
                "socket_timeout": 300,
                "http_chunk_size": 10485760,  # 10MB chunks
                "retries": 10,
                "fragment_retries": 10,
                "file_access_retries": 10,
                "skip_unavailable_fragments": True,
            }

            if not ignore_cookies:
                ydl_opts["cookiefile"] = cookie_file

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            # ZIP the playlist folder
            zip_base = os.path.join(DOWNLOAD_FOLDER, f"playlist_{playlist_id}")
            shutil.make_archive(zip_base, "zip", playlist_folder)
            zip_path = f"{zip_base}.zip"

            if not os.path.exists(zip_path):
                flash("Playlist zip creation failed.", "error")
                return redirect(url_for("index"))

            return send_file(zip_path, as_attachment=True)

        else:
            flash("Invalid download mode!", "error")
            return redirect(url_for("index"))

    except Exception as e:
        # Log the full error to stderr so it shows up in Render/Docker logs
        logging.exception("ERROR downloading")
        app.logger.error(f"Download invalid: {e}")

        # show error and go back to UI
        flash(f"Error: {str(e)}", "error")
        return redirect(url_for("index"))


# -----------------------------
# RUN APP (local testing)
# -----------------------------
if __name__ == "__main__":
    # ensure templates folder is used; run debug locally only
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
