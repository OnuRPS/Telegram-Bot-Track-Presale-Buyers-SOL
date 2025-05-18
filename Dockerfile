FROM python:3.10-slim

WORKDIR /app

COPY . .

# Instalează pip și pachetele în ordine strictă
RUN pip install --upgrade pip \
 && pip install solders==0.23.0 solana==0.36.0 \
 && pip install -r requirements.txt

CMD ["python", "bot_controller.py"]
