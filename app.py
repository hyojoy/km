import re
import time
import urllib.parse
import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
import subprocess # subprocess 모듈 추가

# Selenium 실행 설정
def create_driver():
    st.write("--- create_driver() 호출됨 ---") # 함수 호출 확인 로그

    # 런타임에서 Chrome 및 ChromeDriver 버전 확인
    try:
        chrome_version_proc = subprocess.run(
            ["/usr/bin/google-chrome", "--version"],
            capture_output=True, text=True, check=True
        )
        chrome_version_runtime = chrome_version_proc.stdout.strip()
        st.write(f"Python 런타임 감지 Chrome 버전: {chrome_version_runtime}")
    except Exception as e:
        chrome_version_runtime = f"오류 발생: {e}"
        st.write(f"Python 런타임 Chrome 버전 확인 중 오류: {e}")

    try:
        chromedriver_version_proc = subprocess.run(
            ["/usr/bin/chromedriver", "--version"],
            capture_output=True, text=True, check=True
        )
        chromedriver_version_runtime = chromedriver_version_proc.stdout.strip()
        st.write(f"Python 런타임 감지 ChromeDriver 버전: {chromedriver_version_runtime}")
    except Exception as e:
        chromedriver_version_runtime = f"오류 발생: {e}"
        st.write(f"Python 런타임 ChromeDriver 버전 확인 중 오류: {e}")

    chrome_options = Options()
    chrome_options.binary_location = "/usr/bin/google-chrome"
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1200x800")
    chrome_options.add_argument("--verbose") # Selenium/ChromeDriver 로깅 상세 수준 높임
    chrome_options.add_argument("--log-path=/tmp/chromedriver.log") # ChromeDriver 로그 파일 경로

    service_args = ['--verbose', '--log-path=/tmp/service.log'] # ChromeService 로그
    service = ChromeService(executable_path="/usr/bin/chromedriver", service_args=service_args)
    
    st.write(f"Selenium 초기화 시도: Chrome='{chrome_options.binary_location}', ChromeDriver='{service.path}'")
    st.write(f"감지된 Chrome 버전 (런타임): {chrome_version_runtime}")
    st.write(f"감지된 ChromeDriver 버전 (런타임): {chromedriver_version_runtime}")


    # 이 버전 정보가 오류 메시지의 내용과 일치하는지, 또는 예상과 다른지 확인
    # 예: if "124" in chromedriver_version_runtime and "136" in chrome_version_runtime:
    # st.error("런타임 버전 불일치 감지됨! ChromeDriver는 124, Chrome은 136입니다.")


    return webdriver.Chrome(service=service, options=chrome_options)

# 서비스 및 키워드 데이터 (기존과 동일)
services = [
    {
        "name": "맞춤형 트래픽",
        "id": "/gig/65843",
        "raw_input": """
유입수 970원
트래픽 기밀 1,680원
웹사이트트래픽 1,700원
검색트래픽 1,680원
트래픽 체류시간 1,600원
웹사이트 트래픽 1,310원
국내 트래픽 1,750원
웹트래픽 3,410원
트래픽 교육 1,620원
사이트트래픽 2,110원
트래픽 관리 2,970원
방문자 1,310원
프리미엄 트래픽 2,430원
트래픽 조회 1,060원
웹 트래픽 2,800원
트래픽 솔루션 1,720원
트래픽 제작 1,220원
실사용자 트래픽 2,390원
"""
    },
    # 다른 서비스 생략
]

# 크롤링 수행
def run_search():
    driver = create_driver()
    final_results = {}

    for service_item in services: # 변수명 변경 service -> service_item (service 객체와 혼동 방지)
        name = service_item["name"]
        gig_id = service_item["id"]
        raw = service_item["raw_input"]

        pairs = re.findall(r'(.+?)\s+[\d,]+원', raw.strip())
        keywords = [k.strip() for k in pairs]
        final_results[name] = {}

        for keyword in keywords:
            encoded = urllib.parse.quote(keyword)
            url = f"https://kmong.com/search?type=gigs&keyword={encoded}"
            st.write(f"크롤링 URL: {url}") # 현재 크롤링 중인 URL 로그
            driver.get(url)
            time.sleep(4) 

            articles = driver.find_elements(By.CSS_SELECTOR, 'article[data-testid="gig-item"] a[href^="/gig/"]')
            if not articles:
                 articles = driver.find_elements(By.CSS_SELECTOR, 'article.css-790i1i a[href^="/gig/"]')


            found = False
            for i, article in enumerate(articles[:5]):
                href = article.get_attribute('href')
                if gig_id in href:
                    rank_text = f"{i+1}위"
                    if i >= 4: 
                        rank_text = f"🔴 {rank_text}"
                    final_results[name][keyword] = rank_text
                    found = True
                    break
            
            if not found:
                final_results[name][keyword] = "🔴 ❌ 없음"

    driver.quit()
    return final_results

# Streamlit UI
st.title("🔍 키워드 검색 결과 순위 확인기")

if 'results' not in st.session_state:
    st.session_state.results = None

if st.button("🚀 시작하기"):
    with st.spinner("잠시만 기다려주세요..."):
        try:
            st.session_state.results = run_search()
        except Exception as e:
            st.error(f"오류 발생: {e}")
            # 상세한 트레이스백을 위해 st.exception(e) 사용 가능
            st.exception(e) 
            st.session_state.results = None # 오류 발생 시 결과 초기화

if st.session_state.results:
    st.success("완료!")
    for service_name, keywords_data in st.session_state.results.items():
        st.markdown(f"### 🔹 서비스: {service_name}")
        for keyword, rank in keywords_data.items():
            color = "red" if "🔴" in rank else "black"
            st.markdown(f"<span style='color:{color}'>• {keyword}: {rank}</span>", unsafe_allow_html=True)

    #디버깅 로그 파일 내용 보기 (선택 사항)
    if st.checkbox("ChromeDriver 로그 보기 (/tmp/chromedriver.log)"):
        try:
            with open("/tmp/chromedriver.log", "r") as f:
                st.text_area("ChromeDriver Log", f.read(), height=300)
        except FileNotFoundError:
            st.write("/tmp/chromedriver.log 파일을 찾을 수 없습니다.")
    if st.checkbox("ChromeService 로그 보기 (/tmp/service.log)"):
        try:
            with open("/tmp/service.log", "r") as f:
                st.text_area("ChromeService Log", f.read(), height=300)
        except FileNotFoundError:
            st.write("/tmp/service.log 파일을 찾을 수 없습니다.")
