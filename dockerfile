FROM python:3.12

WORKDIR /app
COPY . /app

RUN pip install -r requirements.txt

CMD ["python", "bot.py"]

RUN apt-get update && apt-get install -y \
    python3-dev python3-pip python3-venv \
    build-essential libffi-dev libssl-dev \
    libnacl-dev libjpeg-dev libxslt1-dev zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*
