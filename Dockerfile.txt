# Base com Python + Tesseract
FROM python:3.10-slim

# Instala o Tesseract e dependências
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    poppler-utils \
    tesseract-ocr-por \
    && apt-get clean

# Cria diretório da aplicação
WORKDIR /app

# Copia tudo da pasta local
COPY ./app /app

# Instala dependências do Python
RUN pip install --no-cache-dir -r requirements.txt

# Porta para o Render (importante!)
ENV PORT=10000

# Executa a API
CMD ["python", "main.py"]
