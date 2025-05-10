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
    # 메모리 확보를 위한 가비지 컬렉션 강제 실행
    gc.collect()
    
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    # 단일 프로세스 모드 대신 일반 모드로 변경
    # options.add_argument("--single-process") # 이 줄 삭제 또는 주석 처리
    
    # 추가: 크롬 안정성 향상을 위한 옵션
    options.add_argument("--disable-features=NetworkService")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-notifications")
    options.add_argument("--remote-debugging-port=9222") # 디버깅 포트 활성화
    
    try:
        service = Service(executable_path="/usr/bin/chromedriver")
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(15)  # 타임아웃 시간 증가
        return driver
    except Exception as e:
        st.warning(f"드라이버 생성 실패: {str(e)}")
        
        # 정리 후 두 번째 시도
        clean_processes()
        time.sleep(3)
        
        try:
            options = Options()
            options.add_argument("--headless=new")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            service = Service(executable_path="/usr/bin/chromedriver")
            driver = webdriver.Chrome(service=service, options=options)
            return driver
        except Exception as e2:
            st.error(f"드라이버 생성 완전 실패: {str(e2)}")
            raise

def clean_processes():
    """더 강력한 프로세스 정리"""
    import os, signal, subprocess
    
    try:
        # 좀비 프로세스 정리 (SIGTERM으로 먼저 시도하고 SIGKILL)
        os.system("pkill -f chrome")
        os.system("pkill -f chromedriver")
        
        # 강제 종료 전 잠시 대기
        time.sleep(1)
        
        # 그래도 남아있는 프로세스 강제 종료
        os.system("pkill -9 -f chrome")
        os.system("pkill -9 -f chromedriver")
        
        # 메모리 정리
        gc.collect()
    except:
        pass
    
    # 시스템에 자원 정리 시간 제공
    time.sleep(2)

def is_driver_alive(driver):
    """드라이버가 살아있는지 확인"""
    try:
        driver.execute_script("return navigator.userAgent")
        return True
    except:
        return False

def quit_driver(driver):
    """드라이버를 안전하게 종료하고 리소스 정리"""
    try:
        if driver:
            driver.execute_script("window.stop();")  # 페이지 로딩 중지
            time.sleep(0.5)
            driver.quit()
    except Exception as e:
        pass
    finally:
        # 남은 프로세스 정리
        clean_processes()
        # 메모리 정리
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
                # 상위 5개까지만 확인 (중요한 최적화)
                for i, element in enumerate(elements[:5]):  # 5개까지만 확인
                    try:
                        href = element.get_attribute('href')
                        if gig_id in href:
                            if i+1 == 5:  # 정확히 5위인 경우 특별 표시
                                return f"{i+1}위 (경계)", True
                            return f"{i+1}위", True
                    except:
                        continue  # 요소가 stale 상태면 다음으로 넘어감
                
                # 상위 5개 안에 없으면 "5위 밖" 표시
                return "5위 밖", False
        except Exception:
            continue  # 오류 발생 시 다음 방법 시도

    # 모든 방법을 시도했지만 찾지 못한 경우
    # 페이지 소스에서 직접 검색
    if gig_id in driver.page_source:
        return "페이지에 존재하나 5위 밖", False

    return "❌ 없음", False

def format_rank_result(keyword, rank):
    """순위 결과를 색상으로 표시 (5위 기준)"""
    if "위" in rank:
        # 순위 확인
        if "5위 밖" in rank:
            # 5위 밖은 회색
            return f"- ⚠️ **{keyword}**: <span style='color:gray;'>{rank}</span>"
        elif "5위 (경계)" in rank:
            # 정확히 5위는 노란색
            return f"- ✅ **{keyword}**: <span style='color:orange; font-weight:bold;'>{rank}</span>"
        else:
            # 1-4위는 초록색
            return f"- ✅ **{keyword}**: <span style='color:green; font-weight:bold;'>{rank}</span>"
    else:
        # 순위가 없으면 빨간색
        return f"- ❌ **{keyword}**: <span style='color:red;'>{rank}</span>"


def search_keyword(driver, keyword, gig_id, max_retries=3):
    """키워드 검색 및 서비스 순위 확인 - 5위 이내만 확인하도록 최적화"""
    for attempt in range(max_retries):
        try:
            # 드라이버 상태 확인
            if not is_driver_alive(driver):
                quit_driver(driver)
                driver = get_driver()
                time.sleep(2)
            
            # 검색 URL 생성 및 접속
            encoded = urllib.parse.quote(keyword)
            url = f"https://kmong.com/search?type=gigs&keyword={encoded}"
            
            # 페이지 로드 시도
            driver.get(url)
            
            # 페이지 로딩 대기 (최소화)
            time.sleep(3)  # 첫 5개 결과만 필요하므로 대기 시간 단축
            
            # 상위 결과만 확인하기 위한 최소한의 스크롤
            try:
                # 상위 결과 영역만 표시되도록 약간만 스크롤
                driver.execute_script("window.scrollTo(0, 300);")
                time.sleep(0.5)
                
                rank, found = find_service_rank(driver, gig_id)
            except Exception as rank_error:
                # 선택자로 찾지 못하면 페이지 소스에서 검색
                if gig_id in driver.page_source:
                    rank = "페이지에 존재하나 5위 밖"
                    found = False
                else:
                    rank = "❌ 없음"
                    found = False
            
            return rank, found
            
        except WebDriverException as wde:
            # 세션 오류 처리
            if "invalid session id" in str(wde) or "session deleted" in str(wde):
                if attempt < max_retries - 1:
                    # 드라이버 완전히 재시작
                    quit_driver(driver)
                    time.sleep(2)
                    driver = get_driver()
                    time.sleep(3)  # 추가 대기
                else:
                    return f"❌ 세션 오류: 브라우저 연결 끊김", False
            else:
                if attempt < max_retries - 1:
                    quit_driver(driver)
                    driver = get_driver()
                    time.sleep(3)
                else:
                    return f"❌ 드라이버 오류: {str(wde)[:30]}...", False
        except TimeoutException:
            # 타임아웃 특별 처리
            if attempt < max_retries - 1:
                quit_driver(driver)
                driver = get_driver()
                time.sleep(2)
            else:
                return "❌ 페이지 로딩 시간 초과", False
        except Exception as e:
            if attempt < max_retries - 1:
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
        # 매 키워드마다 드라이버 재시작 (더 안정적인 접근)
        if idx > 0:
            quit_driver(driver)
            driver = get_driver()
            time.sleep(2)
        
        with st.spinner(f"검색 중: {keyword} ({idx+1}/{len(keywords)})"):
            # 검색 실행
            try:
                rank, success = search_keyword(driver, keyword, gig_id, max_retries=2)
            except Exception as e:
                # 오류 발생 시 
                st.warning(f"키워드 '{keyword}' 검색 중 오류: {str(e)[:50]}...")
                quit_driver(driver)
                driver = get_driver()
                time.sleep(2)
                # 재시도
                rank, success = search_keyword(driver, keyword, gig_id, max_retries=2)
            
            # 결과 저장 및 표시
            keyword_results[keyword] = rank
            results.append(format_rank_result(keyword, rank))
            
            # 진행 상황 업데이트
            progress_percentage = (idx + 1) / len(keywords)
            progress_bar.progress(min(progress_percentage, 1.0))
            results_placeholder.markdown("\n".join(results), unsafe_allow_html=True)
            
            # 처리 간격 - 충분한 시간 설정
            time.sleep(2)
    
    return keyword_results, results, driver

if st.button("키워드 순위 분석 시작"):
    # 시작 전 철저한 시스템 정리
    st.info("시스템 리소스 정리 중...")
    clean_processes()
    gc.collect()
    time.sleep(3)
    
    try:
        # 한 번에 처리할 키워드 수 제한
        MAX_KEYWORDS_PER_BATCH = 3  # 더 작은 배치 크기로 변경
        
        # 서비스 및 키워드 데이터 준비
        total_keywords = sum(len(re.findall(r'(.+?)\n[\d,]+원', service["raw_input"].strip())) for service in services)
        results_by_service = {}
        total_progress = st.progress(0)
        processed_keywords = 0
        
        for service_idx, service in enumerate(services):
            name = service["name"]
            gig_id = service["id"]
            all_keywords = re.findall(r'(.+?)\n[\d,]+원', service["raw_input"].strip())
            all_keywords = [kw.strip() for kw in all_keywords]
            
            st.subheader(f"📦 서비스: {name} ({len(all_keywords)} 키워드)")
            service_progress = st.progress(0)
            results_placeholder = st.empty()
            results_by_service[name] = {}
            
            # 키워드를 소규모 배치로 나눠서 처리
            for batch_start in range(0, len(all_keywords), MAX_KEYWORDS_PER_BATCH):
                # 철저한 청소 및 리소스 정리
                clean_processes()
                gc.collect()
                time.sleep(2)
                
                # 현재 배치 키워드
                batch_keywords = all_keywords[batch_start:batch_start + MAX_KEYWORDS_PER_BATCH]
                
                # 현재 배치 처리
                st.info(f"배치 처리 중: {batch_start+1}-{min(batch_start+MAX_KEYWORDS_PER_BATCH, len(all_keywords))}/{len(all_keywords)}")
                
                # 배치 내 키워드 처리
                for idx, keyword in enumerate(batch_keywords):
                    batch_idx = batch_start + idx
                    
                    # 새 드라이버 생성
                    driver = None
                    try:
                        with st.spinner(f"검색 중: {keyword} ({batch_idx+1}/{len(all_keywords)})"):
                            # 3번까지 드라이버 생성 시도
                            for attempt in range(3):
                                try:
                                    driver = get_driver()
                                    break
                                except Exception as e:
                                    if attempt < 2:  # 2번까지는 재시도
                                        st.warning(f"드라이버 생성 실패 ({attempt+1}/3): {str(e)[:30]}...")
                                        clean_processes()
                                        time.sleep(3)
                                    else:
                                        raise Exception(f"드라이버 생성 최대 시도 횟수 초과: {str(e)}")
                            
                            # 검색 실행
                            if driver:
                                rank, success = search_keyword(driver, keyword, gig_id, max_retries=2)
                            else:
                                rank = "❌ 드라이버 생성 실패"
                                success = False
                            
                            # 결과 저장
                            results_by_service[name][keyword] = rank
                            
                            # 진행 상황 업데이트
                            progress_percentage = (batch_idx + 1) / len(all_keywords)
                            service_progress.progress(min(progress_percentage, 1.0))
                            
                            # 지금까지의 결과 표시
                            current_results = []
                            for k_idx, k in enumerate(all_keywords[:batch_idx+1]):
                                result = results_by_service[name].get(k, "대기 중...")
                                current_results.append(format_rank_result(k, result))
                            
                            results_placeholder.markdown("\n".join(current_results), unsafe_allow_html=True)
                    
                    except Exception as e:
                        # 키워드 처리 중 오류 발생 시 기록하고 계속 진행
                        error_msg = f"❌ 처리 오류: {str(e)[:50]}..."
                        results_by_service[name][keyword] = error_msg
                        st.warning(f"키워드 '{keyword}' 처리 중 오류: {error_msg}")
                    
                    finally:
                        # 반드시 드라이버 종료 및 리소스 정리
                        if driver:
                            quit_driver(driver)
                        
                        # 전체 진행 상황 업데이트
                        processed_keywords += 1
                        total_progress.progress(min(processed_keywords / total_keywords, 1.0))
                        
                        # 처리 간격 - 충분한 시간을 두어 리소스 회복
                        time.sleep(3)
                
                # 배치 처리 후 철저한 정리
                clean_processes()
                gc.collect()
                time.sleep(3)
            
            # 서비스 진행 표시줄 완료
            service_progress.progress(1.0)
            st.markdown("---")
        
        # 모든 작업 완료 후 결과 표시
        st.subheader("📊 검색 결과 순위 요약")
        
        for service_name, keywords in results_by_service.items():
            st.markdown(f"**🔹 서비스: {service_name}**")
            
            # 결과를 카테고리로 분류
            top5_keywords = {}
            outside5_keywords = {}
            not_found_keywords = {}
            
            for kw, rank in keywords.items():
                if "위" in rank and "5위 밖" not in rank and "페이지에 존재" not in rank:
                    # 5위 이내
                    top5_keywords[kw] = rank
                elif "5위 밖" in rank or "페이지에 존재" in rank:
                    # 5위 밖
                    outside5_keywords[kw] = rank
                else:
                    # 찾지 못함
                    not_found_keywords[kw] = rank
            
            # 5위 이내 키워드 표시
            if top5_keywords:
                st.markdown("✅ **5위 이내 키워드:**")
                for keyword, rank in top5_keywords.items():
                    if "5위 (경계)" in rank:
                        st.markdown(f"  - {keyword}: <span style='color:orange; font-weight:bold;'>{rank}</span>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"  - {keyword}: <span style='color:green; font-weight:bold;'>{rank}</span>", unsafe_allow_html=True)
            
            # 5위 밖 키워드 표시
            if outside5_keywords:
                st.markdown("⚠️ **5위 밖 키워드:**")
                for keyword, rank in outside5_keywords.items():
                    st.markdown(f"  - {keyword}: <span style='color:gray;'>{rank}</span>", unsafe_allow_html=True)
            
            # 찾지 못한 키워드 표시
            if not_found_keywords:
                st.markdown("❌ **찾지 못한 키워드:**")
                for keyword, rank in not_found_keywords.items():
                    st.markdown(f"  - {keyword}: <span style='color:red;'>{rank}</span>", unsafe_allow_html=True)

            
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
