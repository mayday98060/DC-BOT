FROM python:3.10-slim-bullseye  # 確保安裝 Python

# 安裝 ffmpeg 和 opus
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    ffmpeg \
    libopus0

WORKDIR /app
COPY . .

# 確保使用 Python 3
RUN pip3 install --no-cache-dir -r requirements.txt

CMD ["python3", "bot.py"]  # 確保這裡使用 python3
