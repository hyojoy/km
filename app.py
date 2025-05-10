import re
import time
import gc
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
    options.add_argument("--window-size=1200x800")
    
    # 메모리 사용 최적화 옵션 추가
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-browser-side-navigation")
    options.add_argument("--disable-features=TranslateUI")
    options.add_argument("--disable-features=site-per-process")
    options.add_argument("--disable-breakpad")
    options.add_argument("--disable-logging")
    options.add_argument("--disable-default-apps")
    options.add_argument("--incognito")
    options.add_argument("--disable-dev-tools")
    options.add_argument("--disable-browser-side-navigation")
    
    # Railway 환경에 최적화된 메모리 제한 설정
    options.add_argument("--js-flags=--max-old-space-size=128")
    
    # Use pre-installed ChromeDriver from Dockerfile
    service = Service(executable_path="/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)
    return driver

# 검색 함수를 별도로 분리하고 재시도 로직 추가
def search_keyword(driver, keyword, gig_id, max_retries=3):
    for attempt in range(max_retries):
        try:
            # 메모리 정리 먼저 실행
            gc.collect()
            
            encoded = urllib.parse.quote(keyword)
            url = f"https://kmong.com/search?type=gigs&keyword={encoded}"
            
            # 페이지 로드
            driver.get(url)
            
            # 짝수 번째 키워드는 대기 시간을 약간 늘림
            wait_time = 7 if keyword == keyword.strip() and len(keyword) % 2 == 0 else 5
            time.sleep(wait_time)
            
            # 페이지 로드 완료 확인
            articles = driver.find_elements(By.CSS_SELECTOR, 'article.css-790i1i a[href^="/gig/"]')
            
            # 결과 확인
            for i, article in enumerate(articles[:5]):
                href = article.get_attribute('href')
                if gig_id in href:
                    return f"{i+1}위", True
            
            return "❌ 없음", True
            
        except Exception as e:
            if attempt < max_retries - 1:
                # 짧은 대기 후 재시도
                time.sleep(3)
                try:
                    # 브라우저 상태 확인 및 재설정
                    driver.execute_script("return document.readyState")
                except:
                    # 브라우저 재시작
                    try:
                        driver.quit()
                    except:
                        pass
                    driver = get_driver()
            else:
                return f"❌ 오류 발생 ({str(e)[:50]}...)", False
    
    return "❌ 최대 재시도 횟수 초과", False

# Start analysis when user clicks the button
if st.button("키워드 순위 분석 시작"):
    try:
        # Initialize driver once before starting
        driver = get_driver()
        
        # Dictionary to store results
        results_by_service = {}
        
        # Process all services
        for service_idx, service in enumerate(services):
            name = service["name"]
            gig_id = service["id"]
            raw_input = service["raw_input"]
            
            # Extract keywords using the same regex pattern from the original code
            keywords = re.findall(r'(.+?)\n[\d,]+원', raw_input.strip())
            keywords = [kw.strip() for kw in keywords]
            
            st.subheader(f"📦 서비스: {name}")
            
            # Create a progress bar
            progress_bar = st.progress(0)
            
            # Create a placeholder for results
            results_placeholder = st.empty()
            results = []
            results_by_service[name] = {}
            
            # Process keywords with batch processing
            batch_size = 5  # 한 번에 처리할 키워드 수
            for batch_start in range(0, len(keywords), batch_size):
                batch_end = min(batch_start + batch_size, len(keywords))
                batch_keywords = keywords[batch_start:batch_end]
                
                # 배치 처리 전 드라이버 재시작 (메모리 확보)
                if batch_start > 0:
                    try:
                        driver.quit()
                    except:
                        pass
                    driver = get_driver()
                    # 드라이버 초기화 후 짧은 대기
                    time.sleep(2)
                
                # Process batch keywords
                for idx, keyword in enumerate(batch_keywords):
                    global_idx = batch_start + idx
                    
                    with st.spinner(f"검색 중: {keyword} ({global_idx+1}/{len(keywords)})"):
                        # 짝수 번째 키워드 전에 추가 정리 작업
                        if global_idx % 2 == 1:  # 0-기반 인덱스에서 1은 두 번째(짝수) 키워드
                            gc.collect()
                            time.sleep(1)  # 짝수 번째 키워드 전에 추가 대기
                        
                        # 검색 실행
                        rank, success = search_keyword(driver, keyword, gig_id)
                        
                        # 결과 저장
                        results_by_service[name][keyword] = rank
                        results.append(f"- {'✅' if '위' in rank else '❌'} **{keyword}**: {rank}")
                        
                        # 드라이버 초기화가 필요한 경우
                        if not success:
                            try:
                                driver.quit()
                            except:
                                pass
                            driver = get_driver()
                            time.sleep(2)
                        
                        # 짝수 번째 키워드 후에 추가 정리 및 대기
                        if global_idx % 2 == 1:  # 짝수 번째 키워드 후
                            gc.collect()
                            time.sleep(2)  # 추가 대기
                        
                        # Update progress bar
                        progress_bar.progress((global_idx + 1) / len(keywords))
                        
                        # Update results display
                        results_placeholder.markdown("\n".join(results), unsafe_allow_html=True)
                
                # 배치 처리 후 추가 대기
                time.sleep(3)
                gc.collect()
            
            # Clear progress bar after completion
            progress_bar.empty()
        
        # Quit driver after all operations
        try:
            driver.quit()
        except:
            pass
            
        # Show summary at the end
        st.markdown("---")
        st.subheader("📊 검색 결과 순위 요약")
        
        for service_name, keywords in results_by_service.items():
            st.markdown(f"**🔹 서비스: {service_name}**")
            for keyword, rank in keywords.items():
                st.markdown(f"  - {keyword}: {rank}")
                
        st.success("✅ 모든 키워드 분석이 완료되었습니다!")
    
    except Exception as e:
        st.error(f"오류 발생: {str(e)}")
        # Make sure to quit driver on error
        try:
            if 'driver' in locals():
                driver.quit()
        except:
            pass
else:
    st.info("👆 분석을 시작하려면 위 버튼을 클릭하세요.")

st.markdown("---")
st.markdown("#### 참고야옹")
