# Base Image
FROM python:3.11-slim

# 환경 변수 설정
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    STREAMLIT_WATCHDOG_MODE=none \
    CHROME_BIN=/usr/bin/google-chrome

# 필요한 기본 도구 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget curl unzip gnupg \
    ca-certificates fonts-liberation \
    libnss3 libxss1 libasound2 libatk-bridge2.0-0 \
    libgtk-3-0 libdrm-dev libgbm-dev libxshmfence-dev \
    libu2f-udev \
    chromium \
    chromium-driver \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# 크롬 심볼릭 링크 (경우에 따라 필요)
RUN ln -s /usr/bin/chromium /usr/bin/google-chrome

# 작업 디렉토리
WORKDIR /app

# 종속성 파일 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 앱 복사
COPY . .

# Streamlit 포트 열기
EXPOSE 10000

# 실행 명령어 (Render용)
CMD ["streamlit", "run", "app.py", "--server.port=10000", "--server.address=0.0.0.0"]
