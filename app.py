from flask import Flask, render_template, request, send_file
from flask_socketio import SocketIO, emit
from googletrans import Translator
import os

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads/"
translator = Translator()

# async_mode'u "eventlet" olarak belirleyin
socketio = SocketIO(app, async_mode="eventlet")

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files["file"]
        target_language = request.form.get("language")
        
        if file.filename.endswith(".srt"):
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
            file.save(filepath)

            # Çeviri işlemi
            translated_text = translate_srt(filepath, target_language)
            output_path = os.path.join(app.config["UPLOAD_FOLDER"], "translated_" + file.filename)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(translated_text)
            
            return send_file(output_path, as_attachment=True)
    
    return render_template("index.html")

def translate_srt(filepath, target_language):
    translated_text = ""
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()
        total_lines = len(lines)
        
        for i, line in enumerate(lines):
            # Zaman kodları ve numaraları olduğu gibi bırak
            if line.strip().isdigit() or "-->" in line:
                translated_text += line
            else:
                try:
                    translation = translator.translate(line, src="auto", dest=target_language)
                    translated = translation.text if translation and translation.text else ""
                    translated_text += translated + "\n"
                except Exception as e:
                    translated_text += "\n"
            
            # İlerleme yüzdesini hesapla ve istemciye gönder
            progress = int((i + 1) / total_lines * 100)
            socketio.emit('progress', {'progress': progress})

    return translated_text

if __name__ == "__main__":
    os.makedirs("uploads", exist_ok=True)
    socketio.run(app, debug=True)
