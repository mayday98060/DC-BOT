FROM python:3.10-slim-bullseye

RUN apt-get update && apt-get install -y \
    ffmpeg \
    libopus0 \
    python3 \
    python3-pip \
    && apt-get clean

WORKDIR /app

COPY . .

RUN pip3 install --no-cache-dir -r requirements.txt

CMD ["python3", "bot.py"]
