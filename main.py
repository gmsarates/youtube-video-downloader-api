from flask import Flask, request, jsonify, send_from_directory
from pytubefix import YouTube
import re
import os
import unicodedata

app = Flask(__name__)

DOWNLOAD_ROOT = "./downloads"


def slugify(text):
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    text = re.sub(r'[^a-zA-Z0-9\- ]+', '', text).lower().strip()
    return text.replace(" ", "-") or "video"


def download_video(url, resolution):
    try:
        yt = YouTube(
            url,
            use_oauth=True,
            allow_oauth_cache=True
        )

        stream = yt.streams.filter(progressive=True, file_extension='mp4', resolution=resolution).first()

        video_id = url.split("v=")[1].split("&")[0]
        out_dir = os.path.join(DOWNLOAD_ROOT, video_id)
        os.makedirs(out_dir, exist_ok=True)

        # Baixa o arquivo
        file_path = stream.download(output_path=out_dir)

        # Slug pelo título
        slug_name = slugify(yt.title) + ".mp4"
        new_path = os.path.join(out_dir, slug_name)

        # Renomeia
        os.rename(file_path, new_path)

        return True, new_path, slug_name, video_id

    except Exception as e:
        return False, None, None, None

def get_video_info(url):
    try:
        yt = YouTube(
            url,
            use_oauth=True,
            allow_oauth_cache=True
        )
        
        stream = yt.streams.first()
        video_info = {
            "title": yt.title,
            "author": yt.author,
            "length": yt.length,
            "views": yt.views,
            "description": yt.description,
            "publish_date": yt.publish_date,
        }
        return video_info, None
    except Exception as e:
        return None, str(e)


def is_valid_youtube_url(url):
    pattern = r"^(https?://)?(www\.)?youtube\.com/watch\?v=[\w-]+(&\S*)?$"
    return re.match(pattern, url) is not None


# 🔥 ROTA PARA DOWNLOAD
@app.route("/files/<video_id>/<filename>")
def serve_file(video_id, filename):
    folder = os.path.join(DOWNLOAD_ROOT, video_id)
    return send_from_directory(folder, filename, as_attachment=True)


# 🔥 ROTA QUE FAZ O DOWNLOAD E RETORNA A URL
@app.route('/download/<resolution>', methods=['POST'])
def download_by_resolution(resolution):
    data = request.get_json()
    url = data.get('url')

    if not url:
        return jsonify({"error": "Missing 'url' parameter."}), 400

    if not is_valid_youtube_url(url):
        return jsonify({"error": "Invalid YouTube URL."}), 400

    success, path, filename, video_id = download_video(url, resolution)

    if not success:
        return jsonify({"error": "Could not download video"}), 500

    # URL completa do download
    download_url = f"{request.host_url}files/{video_id}/{filename}"

    return jsonify({
        "message": "Video downloaded successfully.",
        "file": filename,
        "download_url": download_url
    }), 200


@app.route('/video_info', methods=['POST'])
def video_info():
    data = request.get_json()
    url = data.get('url')
    
    if not url:
        return jsonify({"error": "Missing 'url' parameter in the request body."}), 400

    if not is_valid_youtube_url(url):
        return jsonify({"error": "Invalid YouTube URL."}), 400
    
    video_info, error_message = get_video_info(url)
    
    if video_info:
        return jsonify(video_info), 200
    else:
        return jsonify({"error": error_message}), 500


@app.route('/available_resolutions', methods=['POST'])
def available_resolutions():
    data = request.get_json()
    url = data.get('url')
    
    if not url:
        return jsonify({"error": "Missing 'url' parameter in the request body."}), 400

    if not is_valid_youtube_url(url):
        return jsonify({"error": "Invalid YouTube URL."}), 400
    
    try:
        yt = YouTube(url)
        progressive_resolutions = list(set([
            stream.resolution 
            for stream in yt.streams.filter(progressive=True, file_extension='mp4')
            if stream.resolution
        ]))
        all_resolutions = list(set([
            stream.resolution 
            for stream in yt.streams.filter(file_extension='mp4')
            if stream.resolution
        ]))
        return jsonify({
            "progressive": sorted(progressive_resolutions),
            "all": sorted(all_resolutions)
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
