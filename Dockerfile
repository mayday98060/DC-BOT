FROM debian:bullseye

# 安裝必需的套件
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libopus0 \
    python3 \
    python3-pip \
    && apt-get clean

# 設定工作目錄
WORKDIR /app

# 複製專案程式碼
COPY . .

# 安裝 Python 依賴
RUN pip3 install --no-cache-dir -r requirements.txt

# 啟動 Bot
CMD ["python3", "bot.py"]
