# Folosește Python 3.10 slim pentru compatibilitate cu solders
FROM python:3.10-slim

# Setează directorul de lucru
WORKDIR /app

# Copiază tot codul în container
COPY . .

# Instalează dependențele cu versiuni compatibile
RUN pip install --upgrade pip \
 && pip install solders==0.22.0 solana==0.30.1 \
 && pip install -r requirements.txt

# Rulează scriptul principal
CMD ["python", "main.py"]
