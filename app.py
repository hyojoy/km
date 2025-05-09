import re
import time
import urllib.parse
import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
import subprocess 
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os
os.environ["STREAMLIT_WATCHDOG_MODE"] = "none"

def create_driver():
    options = Options()
    options.add_argument("--headless=chrome")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--disable-features=VizDisplayCompositor")
    options.add_argument("--window-size=1920x1080")
    options.add_argument("--blink-settings=imagesEnabled=false")  # 이미지 로딩 꺼서 속도 향상
    options.add_argument("--disable-background-networking")
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--disable-backgrounding-occluded-windows")
    options.add_argument("--disable-renderer-backgrounding")
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(30)  # 전체 timeout 제한
    return driver


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

def safe_get(driver, url, timeout=20):
    try:
        driver.get(url)
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "article[data-testid='gig-item']"))
        )
        return True
    except Exception as e:
        print(f"[!] URL 로드 실패: {url}\n오류: {e}")
        return False


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
            safe_get(driver, url)
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
