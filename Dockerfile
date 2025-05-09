FROM python:3.10-slim

# 필수 패키지 설치
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    wget \
    curl \
    unzip \
    gnupg \
    ca-certificates \
    jq \
    libglib2.0-0 \
    libnss3 \
    libgconf-2-4 \
    libfontconfig1 \
    libxss1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    fonts-liberation \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 최신 Chrome 설치
RUN wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb -O /tmp/chrome.deb && \
    apt-get update && \
    apt-get install -y --no-install-recommends /tmp/chrome.deb && \
    rm /tmp/chrome.deb && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Chrome 버전 확인 및 일치하는 ChromeDriver 설치
RUN set -ex && \
    CHROME_VERSION=$(google-chrome --version | grep -oP '\d+\.\d+\.\d+\.\d+') && \
    echo "Detected Chrome version: $CHROME_VERSION" && \
    CHROMEDRIVER_URL=$( \
      curl -s https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json | \
      jq -r --arg ver "$CHROME_VERSION" '.versions[] | select(.version==$ver) | .downloads.chromedriver[] | select(.platform=="linux64") | .url' \
    ) && \
    if [ -z "$CHROMEDRIVER_URL" ]; then \
      echo "ChromeDriver URL not found for version $CHROME_VERSION" >&2; exit 1; \
    fi && \
    echo "Downloading ChromeDriver from $CHROMEDRIVER_URL" && \
    wget -q -O /tmp/chromedriver.zip "$CHROMEDRIVER_URL" && \
    unzip -o /tmp/chromedriver.zip -d /tmp/ && \
    mv /tmp/chromedriver-linux64/chromedriver /usr/bin/chromedriver && \
    chmod +x /usr/bin/chromedriver && \
    chromedriver --version

# 파이썬 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 앱 복사
COPY app.py .

# 포트 열기 및 실행
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
