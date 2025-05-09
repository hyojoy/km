import re
import time
import urllib.parse
import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options

# Selenium 실행 설정
def create_driver():
    chrome_options = Options()
    chrome_options.binary_location = "/usr/bin/google-chrome"
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1200x800")

    return webdriver.Chrome(
        service=ChromeService("/usr/bin/chromedriver"),
        options=chrome_options
    )

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
    },
    # 다른 서비스 생략 (같은 구조로 추가 가능)
]

# 크롤링 수행
def run_search():
    driver = create_driver()
    final_results = {}

    for service in services:
        name = service["name"]
        gig_id = service["id"]
        raw = service["raw_input"]

        pairs = re.findall(r'(.+?)\s+[\d,]+원', raw.strip())
        keywords = [k.strip() for k in pairs]
        final_results[name] = {}

        for keyword in keywords:
            encoded = urllib.parse.quote(keyword)
            url = f"https://kmong.com/search?type=gigs&keyword={encoded}"
            driver.get(url)
            time.sleep(4)

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

if st.button("🚀 시작하기"):
    with st.spinner("잠시만 기다려주세요..."):
        results = run_search()

    st.success("완료!")

    for service_name, keywords in results.items():
        st.markdown(f"### 🔹 서비스: {service_name}")
        for keyword, rank in keywords.items():
            color = "red" if "🔴" in rank else "black"
            st.markdown(f"<span style='color:{color}'>• {keyword}: {rank}</span>", unsafe_allow_html=True)
