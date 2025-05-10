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

# Railway 환경에 최적화된 웹드라이버 설정
def get_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1280x1024")  # 해상도 증가
    
    # 최적화 옵션
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    
    # Railway 환경에서 메모리 사용 최적화
    options.add_argument("--js-flags=--max-old-space-size=96")
    options.add_argument("--single-process")
    
    # 실제 브라우저처럼 동작하도록 User-Agent 설정
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")
    
    # ChromeDriver 설정
    service = Service(executable_path="/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)
    
    # 페이지 로딩 타임아웃 설정
    driver.set_page_load_timeout(30)
    
    # 페이지 스크립트 타임아웃 설정
    driver.set_script_timeout(30)
    
    return driver

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

# 향상된 키워드 검색 함수
def search_keyword(driver, keyword, gig_id, max_retries=5):  # 재시도 횟수 증가
    for attempt in range(max_retries):
        try:
            # 메모리 정리
            if attempt > 0:  # 첫 시도가 아닌 경우
                gc.collect()
            
            # URL 인코딩 및 검색 URL 생성
            encoded = urllib.parse.quote(keyword)
            url = f"https://kmong.com/search?type=gigs&keyword={encoded}"
            
            # 페이지 로드
            driver.get(url)
            
            # 페이지 완전 로드 확인을 위한 여러 단계
            try:
                # 1. 첫 번째 접근: WebDriverWait로 DOM 요소 대기
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'article a[href^="/gig/"]'))
                )
            except TimeoutException:
                # 2. 첫 번째 방법 실패 시: 페이지 로드 상태 확인
                try:
                    state = driver.execute_script("return document.readyState")
                    if state != "complete":
                        # 페이지가 완전히 로드되지 않았으면 추가 대기
                        time.sleep(10)
                except:
                    # 3. 스크립트 실행 실패 시 단순 대기
                    time.sleep(15)
            
            # 페이지 스크롤 시도
            try:
                # 페이지를 아래로 스크롤하여 더 많은 콘텐츠 로드
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
                time.sleep(1)
                driver.execute_script("window.scrollTo(0, 0);")  # 다시 위로 스크롤
                time.sleep(1)
            except:
                pass  # 스크롤 실패 시 무시하고 계속 진행
            
            # 서비스 랭킹 확인 함수 호출
            rank, found = find_service_rank(driver, gig_id)
            
            # 서비스를 찾았거나 최대 시도 횟수에 도달한 경우
            if found or attempt == max_retries - 1:
                return rank, found
            
            # 이 시점에 도달했다는 것은 재시도가 필요하다는 의미
            time.sleep(3 + attempt * 2)  # 시도 횟수에 따라 대기 시간 증가
            
        except Exception as e:
            # 오류 발생 시 처리
            if attempt < max_retries - 1:
                # 브라우저 상태 확인
                try:
                    driver.execute_script("return window.navigator.userAgent")
                except:
                    # 브라우저 재시작 필요
                    try:
                        driver.quit()
                    except:
                        pass
                    driver = get_driver()
                
                # 재시도 전 대기
                time.sleep(5 + attempt * 3)
            else:
                return f"❌ 오류 발생", False
    
    return "❌ 최대 재시도 횟수 초과", False

# 키워드 처리를 위한 메인 함수
def process_keywords(driver, keywords, gig_id, results_placeholder, progress_bar, total_keywords):
    results = []
    keyword_results = {}
    
    for idx, keyword in enumerate(keywords):
        with st.spinner(f"검색 중: {keyword} ({idx+1}/{len(keywords)})"):
            # 시작 전 잠깐 대기
            time.sleep(1)
            
            # 짝수 번째 키워드는 특별 처리 (인덱스는 0부터 시작하므로 1이 짝수 번째임)
            if idx % 2 == 1:
                # 이전 키워드 처리 결과를 바탕으로 추가 대기 시간 조정
                if idx > 0 and "❌" in results[-1]:  # 이전 결과가 실패했다면
                    gc.collect()
                    time.sleep(5)  # 더 긴 대기 시간
                    
                    # 드라이버 재시작 고려
                    try:
                        state = driver.execute_script("return document.readyState")
                        if state != "complete":
                            # 브라우저 재시작
                            try:
                                driver.quit()
                            except:
                                pass
                            driver = get_driver()
                            time.sleep(3)
                    except:
                        # 브라우저 반응 없으면 재시작
                        try:
                            driver.quit()
                        except:
                            pass
                        driver = get_driver()
                        time.sleep(3)
            
            # 검색 실행 (최대 5번 재시도)
            rank, success = search_keyword(driver, keyword, gig_id, max_retries=5)
            
            # 결과 저장
            keyword_results[keyword] = rank
            results.append(f"- {'✅' if '위' in rank else '❌'} **{keyword}**: {rank}")
            
            # 드라이버 상태 확인
            if not success:
                try:
                    driver.quit()
                except:
                    pass
                driver = get_driver()
                time.sleep(3)
            
            # 진행 상황 업데이트
            progress_percentage = (sum(len(k) for k in keywords[:idx+1])) / total_keywords
            progress_bar.progress(min(progress_percentage, 1.0))
            
            # 결과 표시 업데이트
            results_placeholder.markdown("\n".join(results), unsafe_allow_html=True)
            
            # 처리 간격 조정
            if idx < len(keywords) - 1:  # 마지막 키워드가 아니면
                time.sleep(2)  # 키워드 간 기본 대기 시간
    
    return keyword_results, results

# 메인 UI 및 실행 코드
if st.button("키워드 순위 분석 시작"):
    try:
        # 초기 드라이버 설정
        driver = get_driver()
        
        # 전체 키워드 개수 계산 (진행률 계산용)
        total_keywords = sum(len(re.findall(r'(.+?)\n[\d,]+원', service["raw_input"].strip())) for service in services)
        
        # 결과 저장용 딕셔너리
        results_by_service = {}
        
        # 전체 진행 표시줄
        total_progress = st.progress(0)
        
        # 현재까지 처리된 키워드 수
        processed_keywords = 0
        
        # 모든 서비스 처리
        for service_idx, service in enumerate(services):
            name = service["name"]
            gig_id = service["id"]
            raw_input = service["raw_input"]
            
            # 키워드 추출
            keywords = re.findall(r'(.+?)\n[\d,]+원', raw_input.strip())
            keywords = [kw.strip() for kw in keywords]
            
            st.subheader(f"📦 서비스: {name} ({len(keywords)} 키워드)")
            
            # 서비스별 진행 표시줄
            service_progress = st.progress(0)
            
            # 결과 표시용 placeholder
            results_placeholder = st.empty()
            
            # 키워드 배치 처리
            batch_size = 2  # 배치 크기 더 줄임 (더 자주 드라이버 재시작)
            results_by_service[name] = {}
            
            for batch_start in range(0, len(keywords), batch_size):
                # 배치 범위 설정
                batch_end = min(batch_start + batch_size, len(keywords))
                batch_keywords = keywords[batch_start:batch_end]
                
                # 배치마다 드라이버 재시작 (첫 배치 제외)
                if batch_start > 0:
                    try:
                        driver.quit()
                    except:
                        pass
                    driver = get_driver()
                    time.sleep(3)  # 드라이버 초기화 후 대기
                
                # 배치 처리
                batch_results, _ = process_keywords(
                    driver, 
                    batch_keywords, 
                    gig_id, 
                    results_placeholder, 
                    service_progress,
                    len(keywords)
                )
                
                # 결과 통합
                results_by_service[name].update(batch_results)
                
                # 배치 간 휴식
                gc.collect()
                time.sleep(5)
                
                # 전체 진행 상황 업데이트
                processed_keywords += len(batch_keywords)
                total_progress.progress(min(processed_keywords / total_keywords, 1.0))
            
            # 서비스 진행 표시줄 완료 처리
            service_progress.progress(1.0)
            
            # 서비스 간 간격
            st.markdown("---")
        
        # 모든 작업 후 드라이버 종료
        try:
            driver.quit()
        except:
            pass
            
        # 전체 진행 표시줄 완료 처리
        total_progress.progress(1.0)
            
        # 최종 결과 표시
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
        st.error(f"오류 발생: {str(e)}")
        # 오류 발생 시 드라이버 종료
        try:
            if 'driver' in locals():
                driver.quit()
        except:
            pass
else:
    st.info("👆 분석을 시작하려면 위 버튼을 클릭하세요.")

st.markdown("---")
st.markdown("#### 참고사항")
