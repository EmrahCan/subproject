from flask import Flask, render_template, request, send_file
from flask_sqlalchemy import SQLAlchemy
from googletrans import Translator
import os
from datetime import datetime

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads/"
app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///translations.db'  # SQLite veritabanı
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
translator = Translator()
db = SQLAlchemy(app)

# Çeviri geçmişi ve sayaç için model tanımlıyoruz
class Translation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original_filename = db.Column(db.String(120), nullable=False)
    source_language = db.Column(db.String(20), nullable=False)
    target_language = db.Column(db.String(20), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Veritabanını ilk kez oluşturma
with app.app_context():
    db.create_all()

# Çeviri işlemi ve sayacı güncelleme
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files["file"]
        target_language = request.form.get("language")
        
        # Dosya türü kontrolü
        if file and allowed_file(file.filename):
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
            file.save(filepath)

            # Çeviri işlemi
            translated_text = translate_srt(filepath, target_language)
            output_path = os.path.join(app.config["UPLOAD_FOLDER"], "translated_" + file.filename)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(translated_text)
            
            # Çeviri geçmişine kaydetme
            translation = Translation(
                original_filename=file.filename,
                source_language="auto",
                target_language=target_language
            )
            db.session.add(translation)
            db.session.commit()
            
            return send_file(output_path, as_attachment=True)
    
    # Çeviri geçmişini ana sayfada gösterebilmek için tüm çeviri kayıtlarını yüklüyoruz
    translation_history = Translation.query.order_by(Translation.timestamp.desc()).all()
    return render_template("index.html", translation_history=translation_history)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'srt'

def translate_srt(filepath, target_language):
    translated_text = ""
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip().isdigit() or "-->" in line:
                translated_text += line
            else:
                try:
                    translation = translator.translate(line, src="auto", dest=target_language)
                    translated = translation.text if translation and translation.text else ""
                    translated_text += translated + "\n"
                except TypeError:
                    translated_text += "\n"
    return translated_text

if __name__ == "__main__":
    os.makedirs("uploads", exist_ok=True)
    app.run(debug=True)
