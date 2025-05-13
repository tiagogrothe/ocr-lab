from flask import Flask, request, jsonify
from pdf2image import convert_from_bytes
from PIL import Image
import pytesseract
import re
import io
import openai
import os

app = Flask(__name__)
openai.api_key = os.getenv("OPENAI_API_KEY", "SUA_CHAVE_AQUI")

@app.route("/ocr", methods=["POST"])
def ocr():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "Arquivo não enviado com key 'file'"}), 400

        file = request.files['file']
        file_bytes = file.read()

        try:
            images = convert_from_bytes(file_bytes, first_page=1, last_page=1)
        except:
            image = Image.open(io.BytesIO(file_bytes))
            images = [image]

        text = ''
        for img in images:
            text += pytesseract.image_to_string(img, lang='por') + '\n'

        return jsonify({"raw_text": text.strip()}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/clean", methods=["POST"])
def clean_text():
    try:
        data = request.get_json()
        raw_text = data.get("text", "")

        text = re.sub(r'[\\\"\']', '', raw_text)
        text = re.sub(r"\s{2,}", " ", text)
        text = re.sub(r"\n+", "\n", text)

        prompt = f"Extraia apenas os nomes dos exames listados neste texto médico:\n\n{text}"
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        exames = response['choices'][0]['message']['content']

        return jsonify({"exames": exames.strip()}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/", methods=["GET"])
def home():
    return "Backend OCR + GPT ativo", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

