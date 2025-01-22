# 從官方 Python slim 映像檔開始
FROM python:3.10-slim-bullseye

# 安裝 ffmpeg 以及其他你需要的套件
RUN apt-get update && apt-get install -y ffmpeg

# 建立工作目錄
WORKDIR /app

# 複製專案檔案到容器內
COPY . .

# 安裝 Python 套件
RUN pip install --no-cache-dir -r requirements.txt

# 你的啟動指令
CMD ["python", "bot.py"]
