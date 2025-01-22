FROM python:3.11

# 安裝 ffmpeg
RUN apt update && apt install -y ffmpeg

# 設定工作目錄
WORKDIR /app

# 安裝 Python 依賴
COPY requirements.txt .
RUN pip install -r requirements.txt

# 複製 bot.py
COPY bot.py .

# 執行機器人
CMD ["python", "bot.py"]
