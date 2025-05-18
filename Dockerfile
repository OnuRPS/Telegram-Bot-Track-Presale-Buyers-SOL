# Imagine de bază cu Python 3.10
FROM python:3.10-slim

# Setează directorul de lucru
WORKDIR /app

# Copiază tot proiectul în container
COPY . .

# Instalează dependențele
RUN pip install --upgrade pip \
 && pip install solders==0.26.0 solana==0.36.0 \
 && pip install -r requirements.txt

# Setează comanda implicită
CMD ["python", "bot_controller.py"]
