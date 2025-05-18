FROM python:3.10-slim

WORKDIR /app

COPY . .

RUN pip install --upgrade pip \
 && pip install solders==0.17.0 solana==0.30.1 \
 && pip install -r requirements.txt

CMD ["python", "main.py"]
