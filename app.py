import re
import time
import urllib.parse
import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException

# Page configuration
st.set_page_config(page_title="키워드 순위 확인기", layout="wide")
st.title("🔍 키워드 순위 확인기")

# Service and keyword data
services = [
    {
        "name": "맞춤형 트래픽", "id": "/gig/65843", "raw_input": """
유입수
970원

트래픽 기밀
1,680원

웹사이트트래픽
1,700원

검색트래픽
1,680원

트래픽 체류시간
1,600원

웹사이트 트래픽
1,310원

국내 트래픽
1,750원

웹트래픽
3,410원

트래픽 교육
1,620원

사이트트래픽
2,110원

트래픽 관리
2,970원

방문자
1,310원

프리미엄 트래픽
2,430원

트래픽 조회
1,060원

웹 트래픽
2,800원

트래픽 솔루션
1,720원

트래픽 제작
1,220원

실사용자 트래픽
2,390원
        """
    },
    {
        "name": "기사형 백링크", "id": "/gig/167816", "raw_input": """
seo
3,720원

트래픽
5,070원

최적화노출
4,330원

백링크사이트
3,550원

백링크 da
3,310원

백링크 직접
3,220원

백링크작업
3,800원

월관리백링크
1,710원
        """
    },
    {
        "name": "프로필 백링크", "id": "/gig/68379", "raw_input": """
최적화
2,440원

백링크 트래픽
910원

대량 백링크
1,940원

웹사이트백링크
2,010원

수작업 백링크
2,420원

백링크n
2,900원

사이트 백링크
2,910원

pbn백링크
2,740원

화이트햇 백링크
2,420원

seo백링크
3,000원

백링크 최적화
2,120원

구글 seo 백링크
2,800원
        """
    },
    {
        "name": "연속성 백링크", "id": "/gig/486622", "raw_input": """
구글 seo 트래픽
520원
        """
    },
    {
        "name": "SEO 사이트맵", "id": "/gig/137608", "raw_input": """
seo
3,720원

최적화노출
4,330원

최적화
2,440원

웹사이트 seo
500원

seo 컨설팅
710원

웹사이트 등록
990원

검색엔진등록
770원

seo 설정
620원

서치어드바이저
110원

테크니컬
1,090원

seo 교육
890원

seo작업
340원

웹사이트 노출
1,680원

웹사이트노출
800원

사이트맵
480원

seo 최적화
1,140원

검색엔진 최적화
1,430원

사이트 seo
860원

사이트 최적화
900원
        """
    },
]

# Function to initialize the Chrome driver with optimized settings for limited resources
def get_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-infobars")
    options.add_argument("--mute-audio")
    options.add_argument("--disable-browser-side-navigation")
    options.add_argument("--disable-web-security")
    options.add_argument("--blink-settings=imagesEnabled=false")  # Disable images
    options.add_argument("--js-flags=--max_old_space_size=128")  # Limit memory usage
    options.add_argument("--window-size=800x600")  # Smaller window size
    
    # Use pre-installed ChromeDriver from Dockerfile
    service = Service(executable_path="/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)
    return driver

# Function to analyze keyword ranking with retry mechanism
def analyze_keyword(gig_id, keyword, max_retries=3):
    retries = 0
    while retries < max_retries:
        driver = None
        try:
            # Create a new driver for each keyword to prevent memory issues
            driver = get_driver()
            
            encoded = urllib.parse.quote(keyword)
            url = f"https://kmong.com/search?type=gigs&keyword={encoded}"
            driver.get(url)
            time.sleep(3)  # Allow page to load properly
            
            # Check if page loaded correctly
            if "kmong" not in driver.current_url.lower():
                raise WebDriverException("Page did not load correctly")
            
            articles = driver.find_elements(By.CSS_SELECTOR, 'article.css-790i1i a[href^="/gig/"]')
            
            # If no articles found, wait a bit longer and try again
            if not articles:
                time.sleep(2)
                articles = driver.find_elements(By.CSS_SELECTOR, 'article.css-790i1i a[href^="/gig/"]')
            
            for i, article in enumerate(articles):
                href = article.get_attribute('href')
                if gig_id in href:
                    driver.quit()
                    if i < 5:
                        return f"- ✅ **{keyword}**: {i+1}위", "success"
                    else:
                        return f"- ⚠️ **{keyword}**: {i+1}위 (5위 밖)", "warning"
            
            driver.quit()
            return f"- ❌ **{keyword}**: 검색결과 없음", "error"
            
        except Exception as e:
            retries += 1
            if driver:
                try:
                    driver.quit()
                except:
                    pass
            
            if retries >= max_retries:
                return f"- ❌ **{keyword}**: {max_retries}회 시도 후 실패", "error"
            
            # Wait before retrying
            time.sleep(2)

# Split keywords into smaller batches to reduce memory usage
def chunk_keywords(keywords, size=3):
    """Split keywords into smaller chunks to process in batches"""
    for i in range(0, len(keywords), size):
        yield keywords[i:i + size]

# Start analysis when user clicks the button
if st.button("키워드 순위 분석 시작"):
    try:
        for service in services:
            name = service["name"]
            gig_id = service["id"]
            raw_input = service["raw_input"]
            keywords = re.findall(r'(.+?)\n[\d,]+원', raw_input.strip())
            keywords = [kw.strip() for kw in keywords]

            st.subheader(f"📦 서비스: {name}")
            
            # Create a progress bar
            progress_bar = st.progress(0)
            
            # Create a placeholder for results
            results_placeholder = st.empty()
            results = []
            
            # Process keywords in smaller batches
            total_keywords = len(keywords)
            processed = 0
            
            for batch in chunk_keywords(keywords):  # Process in batches of 3
                batch_results = []
                
                for keyword in batch:
                    with st.spinner(f"검색 중: {keyword} ({processed+1}/{total_keywords})"):
                        st.write(f"키워드 분석 중: {keyword}")
                        
                        result, status = analyze_keyword(gig_id, keyword)
                        
                        if status == "success":
                            batch_results.append(result)
                        elif status == "warning":
                            batch_results.append(f"<span style='color:orange'>{result}</span>")
                        else:
                            batch_results.append(f"<span style='color:red'>{result}</span>")
                        
                        processed += 1
                        
                        # Update progress
                        progress = int(processed / total_keywords * 100)
                        progress_bar.progress(progress)
                        
                        # Add small delay between keywords
                        time.sleep(1)
                
                # Add batch results to overall results
                results.extend(batch_results)
                
                # Update results display
                results_placeholder.markdown("\n".join(results), unsafe_allow_html=True)
                
                # Clean up memory between batches
                import gc
                gc.collect()
                
                # Add a small delay between batches
                time.sleep(3)
            
            # Clear progress bar after completion
            progress_bar.empty()
        
        st.success("✅ 모든 키워드 분석이 완료되었습니다!")
    
    except Exception as e:
        st.error(f"오류 발생: {str(e)}")
else:
    st.info("👆 분석을 시작하려면 위 버튼을 클릭하세요.")

st.markdown("---")
st.markdown("#### 야옹이 ####")
