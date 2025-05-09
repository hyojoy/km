FROM python:3.10-slim

# 필수 패키지 설치 (jq 추가)
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    unzip \
    gnupg \
    libglib2.0-0 \
    libnss3 \
    libgconf-2-4 \
    libfontconfig1 \
    libxss1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    fonts-liberation \
    jq \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Chrome 설치 (최신 안정 버전)
RUN wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    apt-get install -y ./google-chrome-stable_current_amd64.deb && \
    rm google-chrome-stable_current_amd64.deb

# ChromeDriver 설치 (설치된 Chrome 버전에 맞는 ChromeDriver 동적 다운로드)
RUN INSTALLED_CHROME_VERSION=$(google-chrome --version | awk '{print $3}') && \
    echo "Installed Chrome version: $INSTALLED_CHROME_VERSION" && \
    # 알려진 좋은 버전 목록에서 정확한 버전 또는 가장 가까운 버전의 ChromeDriver URL을 찾습니다.
    CHROMEDRIVER_URL=$(curl -s "https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json" | \
                       jq -r --argjson version "\"$INSTALLED_CHROME_VERSION\"" '.versions[] | select(.version==$version) | .downloads.chromedriver[] | select(.platform=="linux64") | .url' | head -n 1) && \
    # 정확한 버전이 없는 경우, MAJOR.MINOR.BUILD 형식으로 시도
    if [ -z "$CHROMEDRIVER_URL" ]; then \
        TRUNCATED_CHROME_VERSION=$(echo $INSTALLED_CHROME_VERSION | sed 's/\.[^.]*$//') && \
        echo "Exact match not found. Trying with truncated Chrome version: $TRUNCATED_CHROME_VERSION" && \
        CHROMEDRIVER_URL=$(curl -s "https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json" | \
                           jq -r --argjson version "\"$TRUNCATED_CHROME_VERSION\"" '.versions[] | select(.version | startswith($version)) | .downloads.chromedriver[] | select(.platform=="linux64") | .url' | head -n 1); \
    fi && \
    # 그래도 없는 경우, MAJOR 버전만으로 최신 릴리즈 시도
    if [ -z "$CHROMEDRIVER_URL" ]; then \
        CHROME_MAJOR_VERSION=$(echo $INSTALLED_CHROME_VERSION | cut -d '.' -f1) && \
        echo "Truncated version not found. Trying with LATEST_RELEASE for major version: $CHROME_MAJOR_VERSION" && \
        CHROMEDRIVER_VERSION_FOR_MAJOR=$(curl -s https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_${CHROME_MAJOR_VERSION}) && \
        echo "Latest ChromeDriver release for Chrome Major $CHROME_MAJOR_VERSION is $CHROMEDRIVER_VERSION_FOR_MAJOR" && \
        CHROMEDRIVER_URL=$(curl -s "https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json" | \
                           jq -r --argjson version "\"$CHROMEDRIVER_VERSION_FOR_MAJOR\"" '.versions[] | select(.version==$version) | .downloads.chromedriver[] | select(.platform=="linux64") | .url' | head -n 1); \
    fi && \
    if [ -z "$CHROMEDRIVER_URL" ]; then \
        echo "ERROR: Could not determine ChromeDriver download URL for Chrome version $INSTALLED_CHROME_VERSION." >&2; exit 1; \
    fi && \
    echo "Using ChromeDriver URL: $CHROMEDRIVER_URL" && \
    ZIP_FILENAME="chromedriver-linux64.zip" && \
    # 이전 zip 파일이 있다면 삭제 (wget -O 옵션으로 덮어쓰기 가능)
    rm -f /tmp/$ZIP_FILENAME && \
    wget -qO /tmp/$ZIP_FILENAME $CHROMEDRIVER_URL && \
    unzip -o /tmp/$ZIP_FILENAME -d /tmp/ && \
    # 압축 해제 후 chromedriver 실행 파일이 chromedriver-linux64 디렉토리 안에 있을 수 있음
    if [ -f /tmp/chromedriver-linux64/chromedriver ]; then \
        mv /tmp/chromedriver-linux64/chromedriver /usr/bin/chromedriver; \
    elif [ -f /tmp/chromedriver ]; then \
        mv /tmp/chromedriver /usr/bin/chromedriver; \
    else \
        echo "ERROR: chromedriver not found in /tmp/chromedriver-linux64/ or /tmp/ after unzip." >&2; exit 1; \
    fi && \
    chmod +x /usr/bin/chromedriver && \
    # 임시 파일 및 디렉토리 정리
    rm -f /tmp/$ZIP_FILENAME && \
    rm -rf /tmp/chromedriver-linux64/

# Python 의존성 설치
COPY requirements.txt .
# webdriver-manager가 requirements.txt에 있다면 제거하는 것을 고려 (수동 관리를 위해)
RUN pip install --no-cache-dir -r requirements.txt

# 앱 복사
COPY app.py .

# 실행
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
