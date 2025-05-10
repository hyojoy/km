import re
import time
import gc
import urllib.parse
import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException

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
def get_driver():
    """안정적인 크롬 드라이버 설정"""
    options = Options()
    options.add_argument("--headless=new")  # 새로운 headless 모드
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    # 메모리 사용량 제한 옵션
    options.add_argument("--disable-features=site-per-process")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-component-extensions-with-background-pages")
    options.add_argument("--disable-default-apps")
    options.add_argument("--blink-settings=imagesEnabled=false")  # 이미지 로딩 비활성화
    
    # 고유한 프로필 디렉토리 설정 (핵심 해결책)
    import uuid
    unique_dir = f"/tmp/chrome-data-{uuid.uuid4()}"
    options.add_argument(f"--user-data-dir={unique_dir}")
    
    # 메모리 최적화
    options.add_argument("--window-size=800x600")
    options.add_argument("--js-flags=--max-old-space-size=64")
    options.add_argument("--renderer-process-limit=1")
    options.add_argument("--single-process")
    
    # User-Agent
    options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")
    
    try:
        service = Service(executable_path="/usr/bin/chromedriver")
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(15)
        driver.set_script_timeout(10)
        return driver
    except Exception as e:
        time.sleep(2)
        # 오류 발생 시 다시 시도
        service = Service(executable_path="/usr/bin/chromedriver")
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(15)
        driver.set_script_timeout(10)
        return driver

def is_driver_alive(driver):
    """드라이버가 살아있는지 확인"""
    try:
        driver.execute_script("return navigator.userAgent")
        return True
    except:
        return False

def quit_driver(driver):
    """드라이버를 안전하게 종료"""
    try:
        driver.quit()
    except:
        pass
    
    # 남은 프로세스 정리
    import os
    try:
        os.system("pkill -f chrome")
        os.system("pkill -f chromedriver")
    except:
        pass
    
    # 메모리 정리
    import gc
    gc.collect()

# 다양한 선택자와 방법으로 요소 찾기를 시도하는 함수
def find_service_rank(driver, gig_id):
    # 검색 결과를 찾기 위한 다양한 방법 시도
    methods = [
        # 1. CSS 선택자를 통한 검색 (기존 방식)
        lambda: driver.find_elements(By.CSS_SELECTOR, 'article.css-790i1i a[href^="/gig/"]'),
        
        # 2. 일반적인 article과 a 태그 조합
        lambda: driver.find_elements(By.CSS_SELECTOR, 'article a[href^="/gig/"]'),
        
        # 3. XPath를 사용한 검색
        lambda: driver.find_elements(By.XPATH, '//a[contains(@href, "/gig/")]'),
        
        # 4. 더 넓은 범위의 검색 (div 내 a 태그)
        lambda: driver.find_elements(By.CSS_SELECTOR, 'div[role="main"] a[href^="/gig/"]'),
        
        # 5. 클래스 이름만 부분적으로 포함하는 선택자
        lambda: driver.find_elements(By.CSS_SELECTOR, '[class*="gig-item"] a[href^="/gig/"]'),
        
        # 6. href 속성에 gig_id가 포함된 a 태그 직접 검색
        lambda: driver.find_elements(By.XPATH, f'//a[contains(@href, "{gig_id}")]'),
    ]
    
    # 각 방법을 시도
    for method in methods:
        try:
            elements = method()
            if elements:  # 요소를 찾았다면
                # 결과 확인
                for i, element in enumerate(elements[:15]):  # 상위 15개까지 확인
                    try:
                        href = element.get_attribute('href')
                        if gig_id in href:
                            return f"{i+1}위", True
                    except StaleElementReferenceException:
                        continue  # 요소가 stale 상태면 다음으로 넘어감
        except Exception:
            continue  # 오류 발생 시 다음 방법 시도
    
    # 모든 방법을 시도했지만 찾지 못한 경우
    # 페이지 소스에서 직접 검색
    if gig_id in driver.page_source:
        return "페이지에 존재하나 선택자로 찾지 못함", True
    
    return "❌ 없음", False

def search_keyword(driver, keyword, gig_id, max_retries=2):
    """키워드 검색 및 서비스 순위 확인"""
    for attempt in range(max_retries):
        try:
            # 드라이버 상태 확인
            if not is_driver_alive(driver):
                quit_driver(driver)
                driver = get_driver()
                time.sleep(2)
            
            # 메모리 정리
            gc.collect()
            
            # 검색 URL 생성 및 접속
            encoded = urllib.parse.quote(keyword)
            url = f"https://kmong.com/search?type=gigs&keyword={encoded}"
            driver.get(url)
            
            # 간단한 대기 (복잡한 WebDriverWait 대신)
            time.sleep(3)
            
            # 서비스 순위 확인
            try:
                rank, found = find_service_rank(driver, gig_id)
            except:
                # 선택자로 찾지 못하면 페이지 소스에서 검색
                if gig_id in driver.page_source:
                    rank = "페이지에 존재하나 위치 확인 불가"
                    found = True
                else:
                    rank = "❌ 없음"
                    found = False
            
            return rank, found
            
        except Exception as e:
            if attempt < max_retries - 1:
                # 실패 시 드라이버 재시작
                quit_driver(driver)
                driver = get_driver()
                time.sleep(3)
            else:
                return f"❌ 오류: {str(e)[:30]}...", False
    
    return "❌ 최대 재시도 횟수 초과", False
# 키워드 처리 함수 수정
def process_keywords(driver, keywords, gig_id, results_placeholder, progress_bar, total_keywords):
    results = []
    keyword_results = {}
    
    for idx, keyword in enumerate(keywords):
        # 2개 키워드마다 드라이버 재시작
        if idx > 0 and idx % 2 == 0:
            quit_driver(driver)
            driver = get_driver()
            time.sleep(2)
        
        with st.spinner(f"검색 중: {keyword} ({idx+1}/{len(keywords)})"):
            # 검색 실행
            rank, success = search_keyword(driver, keyword, gig_id, max_retries=3)
            
            # 결과 저장 및 표시
            keyword_results[keyword] = rank
            results.append(f"- {'✅' if '위' in rank else '❌'} **{keyword}**: {rank}")
            
            # 오류 발생 시 드라이버 재시작
            if not success:
                quit_driver(driver)
                driver = get_driver()
                time.sleep(2)
            
            # 진행 상황 업데이트
            progress_percentage = (idx + 1) / len(keywords)
            progress_bar.progress(min(progress_percentage, 1.0))
            results_placeholder.markdown("\n".join(results), unsafe_allow_html=True)
            
            # 처리 간격
            time.sleep(1)
    
    return keyword_results, results, driver

# 메인 UI 및 실행 코드
if st.button("키워드 순위 분석 시작"):
    try:
        # 서비스 및 키워드 데이터 준비
        total_keywords = sum(len(re.findall(r'(.+?)\n[\d,]+원', service["raw_input"].strip())) for service in services)
        results_by_service = {}
        total_progress = st.progress(0)
        processed_keywords = 0
        
        # 각 서비스별 처리
        for service_idx, service in enumerate(services):
            name = service["name"]
            gig_id = service["id"]
            keywords = re.findall(r'(.+?)\n[\d,]+원', service["raw_input"].strip())
            keywords = [kw.strip() for kw in keywords]
            
            st.subheader(f"📦 서비스: {name} ({len(keywords)} 키워드)")
            service_progress = st.progress(0)
            results_placeholder = st.empty()
            results_by_service[name] = {}
            
            # 키워드 한 개씩 처리 (배치 처리 대신)
            for idx, keyword in enumerate(keywords):
                # 매 키워드마다 새 드라이버 생성
                driver = get_driver()
                time.sleep(1)
                
                with st.spinner(f"검색 중: {keyword} ({idx+1}/{len(keywords)})"):
                    # 검색 실행
                    rank, success = search_keyword(driver, keyword, gig_id, max_retries=2)
                    
                    # 결과 저장
                    results_by_service[name][keyword] = rank
                    
                    # 진행 상황 업데이트
                    progress_percentage = (idx + 1) / len(keywords)
                    service_progress.progress(min(progress_percentage, 1.0))
                    
                    # 결과 표시
                    current_results = []
                    for k_idx, k in enumerate(keywords[:idx+1]):
                        result = results_by_service[name].get(k, "대기 중...")
                        current_results.append(f"- {'✅' if '위' in result else '❌'} **{k}**: {result}")
                    
                    results_placeholder.markdown("\n".join(current_results), unsafe_allow_html=True)
                
                # 드라이버 즉시 종료 (중요!)
                quit_driver(driver)
                
                # 전체 진행 상황 업데이트
                processed_keywords += 1
                total_progress.progress(min(processed_keywords / total_keywords, 1.0))
                
                # 처리 간격
                time.sleep(2)
            
            # 서비스 진행 표시줄 완료
            service_progress.progress(1.0)
            st.markdown("---")
        
        # 모든 작업 완료 후 결과 표시
        st.subheader("📊 검색 결과 순위 요약")
        
        for service_name, keywords in results_by_service.items():
            st.markdown(f"**🔹 서비스: {service_name}**")
            
            # 결과를 성공(순위 있음)과 실패(없음)로 분류
            success_keywords = {k: v for k, v in keywords.items() if "위" in v}
            failed_keywords = {k: v for k, v in keywords.items() if "위" not in v}
            
            # 성공한 키워드 먼저 표시
            if success_keywords:
                st.markdown("✅ **찾은 키워드:**")
                for keyword, rank in success_keywords.items():
                    st.markdown(f"  - {keyword}: {rank}")
            
            # 실패한 키워드 표시
            if failed_keywords:
                st.markdown("❌ **찾지 못한 키워드:**")
                for keyword, rank in failed_keywords.items():
                    st.markdown(f"  - {keyword}: {rank}")
            
            # 성공률 계산
            success_rate = len(success_keywords) / len(keywords) * 100 if keywords else 0
            st.markdown(f"**성공률: {success_rate:.1f}%** ({len(success_keywords)}/{len(keywords)})")
            
            st.markdown("---")
                
        st.success("✅ 모든 키워드 분석이 완료되었습니다!")
    
    except Exception as e:
        st.error(f"전체 처리 오류: {str(e)}")
        # 오류 발생 시 남은 드라이버 정리
        import os
        try:
            os.system("pkill -f chrome")
            os.system("pkill -f chromedriver")
        except:
            pass

st.markdown("---")
st.markdown("#### 참고사항")
