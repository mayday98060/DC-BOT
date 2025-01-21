# 安裝系統必要的 Linux 套件
RUN apt-get update && apt-get install -y \
    python3-dev \
    python3-pip \
    python3-setuptools \
    python3-wheel \
    gcc \
    build-essential \
    libffi-dev \
    libssl-dev \
    linux-headers-$(uname -r) \
    && rm -rf /var/lib/apt/lists/*
