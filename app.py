import re
import time
import urllib.parse
import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os

os.environ["STREAMLIT_WATCHDOG_MODE"] = "none"

# 서비스 및 키워드 데이터
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
    }
]

# 키워드 추출
def get_keywords(raw):
    return [k.strip() for k in re.findall(r'(.+?)\s+[\d,]+원', raw.strip())]

# 크롬 드라이버 생성
def create_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--disable-extensions")
    options.add_argument("--window-size=1920x1080")
    options.add_argument("--blink-settings=imagesEnabled=false")
    options.page_load_strategy = 'eager'
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(30)
    return driver

# 페이지 로딩 대기
def safe_get(driver, url, timeout=15):
    try:
        driver.get(url)
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "article[data-testid='gig-item']"))
        )
        return True
    except Exception as e:
        st.warning(f"❌ 페이지 로딩 실패: {url}")
        return False

# 검색 결과에서 순위 찾기
def find_gig_rank(driver, gig_id):
    selectors = [
        'article[data-testid="gig-item"] a[href^="/gig/"]',
        'article.css-790i1i a[href^="/gig/"]'
    ]
    for selector in selectors:
        elements = driver.find_elements(By.CSS_SELECTOR, selector)
        for i, el in enumerate(elements[:5]):
            href = el.get_attribute("href")
            if gig_id in href:
                return f"🔴 {i+1}위" if i >= 4 else f"{i+1}위"
    return "🔴 ❌ 없음"

# 전체 크롤링 로직
def run_search():
    driver = create_driver()
    results = {}

    for service in services:
        name, gig_id, raw = service["name"], service["id"], service["raw_input"]
        keywords = get_keywords(raw)
        results[name] = {}

        for keyword in keywords:
            encoded = urllib.parse.quote(keyword)
            url = f"https://kmong.com/search?type=gigs&keyword={encoded}"
            st.write(f"🔎 검색 중: {keyword}")
            if safe_get(driver, url):
                time.sleep(2)  # 부하 방지
                results[name][keyword] = find_gig_rank(driver, gig_id)
            else:
                results[name][keyword] = "🔴 ❌ 로드 실패"

    driver.quit()
    return results

# Streamlit UI
st.title("🔍 키워드 검색 순위 확인기")

if 'results' not in st.session_state:
    st.session_state.results = None

if st.button("🚀 시작하기"):
    with st.spinner("검색 중입니다..."):
        try:
            st.session_state.results = run_search()
        except Exception as e:
            st.error("❌ 오류 발생")
            st.exception(e)
            st.session_state.results = None

# 결과 표시
if st.session_state.results:
    st.success("✅ 완료!")
    for service_name, keyword_data in st.session_state.results.items():
        st.markdown(f"### 🔹 {service_name}")
        for keyword, rank in keyword_data.items():
            color = "red" if "🔴" in rank else "black"
            st.markdown(f"<span style='color:{color}'>• {keyword}: {rank}</span>", unsafe_allow_html=True)

# 디버깅 로그 보기
if st.checkbox("Chrome 로그 (/tmp/chromedriver.log)"):
    try:
        with open("/tmp/chromedriver.log") as f:
            st.text_area("로그 내용", f.read(), height=300)
    except FileNotFoundError:
        st.write("해당 로그 파일이 없습니다.")
