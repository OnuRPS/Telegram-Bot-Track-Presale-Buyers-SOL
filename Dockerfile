# Imagine de bază cu Python 3.10
FROM python:3.10-slim

# Setează directorul de lucru
WORKDIR /app

# Copiază fișierele în container
COPY . .

# Instalează pip și dependențele (cu forțare solders)
RUN pip install --upgrade pip \
 && pip install solders==0.26.0 \
 && pip install -r requirements.txt

# Pornește scriptul
CMD ["python", "main.py"]
