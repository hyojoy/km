FROM python:3.10-slim

# 필수 패키지 설치 (jq 추가 및 Chrome 의존성 명시)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    wget \
    curl \
    unzip \
    gnupg \
    # Chrome dependencies
    libglib2.0-0 \
    libnss3 \
    libgconf-2-4 \
    libfontconfig1 \
    libxss1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    fonts-liberation \
    # jq for parsing JSON
    jq \
    # HTTPS 통신을 위한 ca-certificates
    ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Chrome 설치 (최신 안정 버전)
RUN echo ">>> Docker build: Chrome 설치 시작..." && \
    wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb -O /tmp/google-chrome-stable_current_amd64.deb && \
    # 로컬 deb 설치 전 apt 데이터베이스 업데이트
    apt-get update && \
    apt-get install -y --no-install-recommends /tmp/google-chrome-stable_current_amd64.deb && \
    rm /tmp/google-chrome-stable_current_amd64.deb && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
RUN echo ">>> Docker build: 설치된 Chrome 버전 확인 중..." && \
    google-chrome --version

# ChromeDriver 설치
RUN echo ">>> Docker build: ChromeDriver 설치 버전 결정 시작..." && \
    # 기존 chromedriver가 있다면 명시적으로 삭제
    rm -f /usr/bin/chromedriver && \
    # 설치된 Chrome 버전 가져오기
    INSTALLED_CHROME_VERSION=$(google-chrome --version | awk '{print $3}') && \
    echo ">>> Docker build: 감지된 Chrome 버전: $INSTALLED_CHROME_VERSION" && \
    CHROME_MAJOR_VERSION=$(echo $INSTALLED_CHROME_VERSION | cut -d '.' -f1) && \
    echo ">>> Docker build: 감지된 Chrome 메이저 버전: $CHROME_MAJOR_VERSION" && \
    \
    # 시도 1: Chrome for Testing JSON API에서 전체 버전 번호로 ChromeDriver URL 가져오기
    echo ">>> Docker build: Chrome 버전 $INSTALLED_CHROME_VERSION 에 대한 정확한 ChromeDriver URL 검색 시도..." && \
    CHROMEDRIVER_URL=$(curl -s "https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json" | \
                       jq -r --argjson ver "$INSTALLED_CHROME_VERSION" '.versions[] | select(.version==$ver) | .downloads.chromedriver[] | select(.platform=="linux64") | .url' | head -n 1) && \
    \
    # 시도 2: 전체 버전이 없으면 MAJOR.MINOR.BUILD 형식(마지막 부분 제외)으로 시도
    if [ -z "$CHROMEDRIVER_URL" ]; then \
        TRUNCATED_CHROME_VERSION=$(echo $INSTALLED_CHROME_VERSION | sed 's/\.[^.]*$//') && \
        echo ">>> Docker build: 정확한 버전($INSTALLED_CHROME_VERSION)을 찾지 못했습니다. 축약 버전($TRUNCATED_CHROME_VERSION)으로 검색 시도..." && \
        CHROMEDRIVER_URL=$(curl -s "https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json" | \
                           jq -r --argjson ver "$TRUNCATED_CHROME_VERSION" '.versions[] | select(.version | startswith($ver)) | .downloads.chromedriver[] | select(.platform=="linux64") | .url' | head -n 1); \
    fi && \
    \
    # 시도 3: 그래도 없으면 MAJOR 버전에 대한 LATEST_RELEASE 사용 (가장 안정적인 방법)
    if [ -z "$CHROMEDRIVER_URL" ]; then \
        echo ">>> Docker build: 축약 버전을 찾지 못했습니다. 메이저 버전($CHROME_MAJOR_VERSION)에 대한 LATEST_RELEASE 로 검색 시도..." && \
        CHROMEDRIVER_VERSION_FOR_MAJOR=$(curl -s "https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_${CHROME_MAJOR_VERSION}") && \
        if [ -z "$CHROMEDRIVER_VERSION_FOR_MAJOR" ]; then \
            echo ">>> Docker build: ERROR: 메이저 버전 $CHROME_MAJOR_VERSION 에 대한 LATEST_RELEASE를 가져올 수 없습니다." >&2; exit 1; \
        fi && \
        echo ">>> Docker build: Chrome 메이저 버전 $CHROME_MAJOR_VERSION 에 대한 최신 ChromeDriver 버전: $CHROMEDRIVER_VERSION_FOR_MAJOR" && \
        CHROMEDRIVER_URL=$(curl -s "https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json" | \
                           jq -r --argjson ver "$CHROMEDRIVER_VERSION_FOR_MAJOR" '.versions[] | select(.version==$ver) | .downloads.chromedriver[] | select(.platform=="linux64") | .url' | head -n 1); \
    fi && \
    \
    # 최종 URL 확인
    if [ -z "$CHROMEDRIVER_URL" ]; then \
        echo ">>> Docker build: ERROR: Chrome 버전 $INSTALLED_CHROME_VERSION (메이저: $CHROME_MAJOR_VERSION)에 대한 ChromeDriver 다운로드 URL을 결정할 수 없습니다." >&2; exit 1; \
    fi && \
    echo ">>> Docker build: 사용할 ChromeDriver URL: $CHROMEDRIVER_URL" && \
    \
    # 다운로드 및 설치
    ZIP_FILENAME="chromedriver-linux64.zip" && \
    # 이전 임시 파일/디렉토리 정리
    rm -f /tmp/$ZIP_FILENAME /tmp/chromedriver && rm -rf /tmp/chromedriver-linux64 && \
    echo ">>> Docker build: $ZIP_FILENAME 다운로드 중..." && \
    wget -qO /tmp/$ZIP_FILENAME $CHROMEDRIVER_URL && \
    echo ">>> Docker build: $ZIP_FILENAME 압축 해제 중..." && \
    unzip -o /tmp/$ZIP_FILENAME -d /tmp/ && \
    \
    # CfT zip 파일은 보통 'chromedriver-linux64/chromedriver' 경로로 압축 해제됨
    DRIVER_PATH_IN_ZIP="chromedriver-linux64/chromedriver" && \
    if [ -f "/tmp/$DRIVER_PATH_IN_ZIP" ]; then \
        echo ">>> Docker build: /tmp/$DRIVER_PATH_IN_ZIP 에서 chromedriver 발견." && \
        mv "/tmp/$DRIVER_PATH_IN_ZIP" /usr/bin/chromedriver; \
    elif [ -f "/tmp/chromedriver" ]; then \
        echo ">>> Docker build: /tmp/chromedriver 에서 chromedriver 발견 (직접 압축 해제된 경우)." && \
        mv "/tmp/chromedriver" /usr/bin/chromedriver; \
    else \
        echo ">>> Docker build: ERROR: 압축 해제 후 /tmp/$DRIVER_PATH_IN_ZIP 또는 /tmp/chromedriver 에서 chromedriver를 찾을 수 없습니다." >&2; \
        echo ">>> Docker build: /tmp/ 디렉토리 내용:" && ls -la /tmp/ && \
        if [ -d "/tmp/chromedriver-linux64" ]; then echo ">>> Docker build: /tmp/chromedriver-linux64/ 디렉토리 내용:" && ls -la /tmp/chromedriver-linux64/; fi; \
        exit 1; \
    fi && \
    chmod +x /usr/bin/chromedriver && \
    echo ">>> Docker build: ChromeDriver가 /usr/bin/chromedriver 에 설치되었습니다." && \
    echo ">>> Docker build: 설치된 ChromeDriver 버전 확인 중..." && \
    /usr/bin/chromedriver --version && \
    # 임시 파일 정리
    rm -f /tmp/$ZIP_FILENAME && \
    rm -rf /tmp/chromedriver-linux64/ && \
    rm -f /tmp/chromedriver # 만약을 위해 삭제

# Python 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 앱 복사
COPY app.py .

# 실행
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
