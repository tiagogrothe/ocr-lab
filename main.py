from flask import Flask, request, jsonify
from pdf2image import convert_from_bytes
from PIL import Image
import pytesseract
import re
import io
import openai
import os
import sys

app = Flask(__name__)

# Chave da OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY", "SUA_CHAVE_AQUI")

@app.route("/ocr", methods=["POST"])
def ocr():
    try:
        if 'file' not in request.files:
            print("❌ Nenhum arquivo com key 'file' foi enviado!", file=sys.stderr, flush=True)
            return jsonify({"error": "Arquivo não enviado com key 'file'"}), 400

        file = request.files['file']
        print("📂 Arquivo recebido:", file.filename, file=sys.stderr, flush=True)

        file_bytes = file.read()

        try:
            images = convert_from_bytes(file_bytes, first_page=1, last_page=1)
        except Exception as conv_error:
            print("⚠️ Falha ao converter PDF para imagem. Tentando como imagem direta...", file=sys.stderr, flush=True)
            image = Image.open(io.BytesIO(file_bytes))
            images = [image]

        text = ''
        for img in images:
            text += pytesseract.image_to_string(img, lang='por') + '\n'

        print("✅ OCR executado com sucesso.", file=sys.stderr, flush=True)
        return jsonify({"raw_text": text.strip()}), 200

    except Exception as e:
        print("❌ Erro no OCR:", str(e), file=sys.stderr, flush=True)
        return jsonify({"error": str(e)}), 500

@app.route("/clean", methods=["POST"])
def clean_text():
    try:
        data = request.get_json()
        raw_text = data.get("text", "")

        print("🧹 Texto recebido para limpeza:", raw_text[:100], file=sys.stderr, flush=True)

        # Limpeza básica
        text = re.sub(r'[\\\"\']', '', raw_text)
        text = re.sub(r"\s{2,}", " ", text)
        text = re.sub(r"\n+", "\n", text)

        prompt = f"Extraia apenas os nomes dos exames listados neste texto médico:\n\n{text}"

        print("📤 Enviando prompt para o GPT...", file=sys.stderr, flush=True)
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )

        exames_extraidos = response['choices'][0]['message']['content']

        print("📥 Resposta do GPT recebida com sucesso.", file=sys.stderr, flush=True)
        return jsonify({"exames": exames_extraidos.strip()}), 200

    except Exception as e:
        print("❌ Erro na limpeza ou GPT:", str(e), file=sys.stderr, flush=True)
        return jsonify({"error": str(e)}), 500

@app.route("/", methods=["GET"])
def home():
    return "Backend OCR + GPT ativo", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)


