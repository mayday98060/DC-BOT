# 使用 Python 3.10 作為基礎環境
FROM python:3.10-slim-bullseye

# 安裝 ffmpeg 和 opus
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libopus0 \
    python3 \
    python3-pip \
    && apt-get clean

# 設定工作目錄
WORKDIR /app

# 複製專案檔案
COPY . .

# 安裝 Python 依賴
RUN pip3 install --no-cache-dir -r requirements.txt

# 指定 Python 3 執行 bot.py
CMD ["python3", "bot.py"]
