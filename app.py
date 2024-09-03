from flask import Flask, request, send_file, after_this_request, render_template
import instaloader
import re
import os
import shutil
import threading
import time

app = Flask(__name__)

def get_shortcode_from_url(url):
    match = re.search(r'instagram\.com/(p|reel)/([^/?#&]+)', url)
    if match:
        return match.group(2)
    else:
        raise ValueError("Geçersiz Instagram URL'si")

def delete_unwanted_files(directory, extensions):
    for filename in os.listdir(directory):
        if any(filename.endswith(ext) for ext in extensions):
            os.remove(os.path.join(directory, filename))

def download_instagram_video(url):
    L = instaloader.Instaloader()
    shortcode = get_shortcode_from_url(url)
    post = instaloader.Post.from_shortcode(L.context, shortcode)
    target_directory = f"{post.owner_username}_{shortcode}"
    L.download_post(post, target=target_directory)
    delete_unwanted_files(target_directory, ['.jpg', '.json', '.txt'])
    return target_directory

def remove_directory(directory):
    try:
        time.sleep(1)  # Biraz bekle, dosyanın serbest bırakılması için
        shutil.rmtree(directory)
    except Exception as e:
        app.logger.error(f'Error removing directory: {e}')

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        video_url = request.form['url']
        try:
            directory = download_instagram_video(video_url)
            video_file = next(f for f in os.listdir(directory) if f.endswith('.mp4'))
            video_path = os.path.join(directory, video_file)

            @after_this_request
            def remove_file(response):
                try:
                    # Dosya gönderildikten sonra dizini ve içindeki dosyaları sil
                    threading.Thread(target=lambda: (time.sleep(2), remove_directory(directory))).start()
                except Exception as e:
                    app.logger.error(f'Error removing or closing downloaded file handle: {e}')
                return response

            return send_file(video_path, as_attachment=True)
        except Exception as e:
            return str(e), 500
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=80)