import re
import urllib.parse
import streamlit as st
from playwright.sync_api import sync_playwright

# 크몽 서비스 키워드 데이터
services = [
    {"name": "기사형 백링크", "id": "/gig/167816", "raw_input": """
마케팅
5,000원
seo
3,720원
트래픽
5,070원
"""}, 
    {"name": "웹사이트 트래픽", "id": "/gig/11111", "raw_input": """
웹사이트트래픽
1,700원
검색트래픽
1,680원
"""}
]

# 키워드 추출 함수
def extract_keywords(raw):
    pairs = re.findall(r'(.+?)\n[\d,]+원', raw.strip())
    return [k.strip() for k in pairs]

# 크몽에서 순위 확인 함수
def check_keyword_rank(playwright, keyword, gig_id):
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()
    encoded = urllib.parse.quote(keyword)
    page.goto(f"https://kmong.com/search?type=gigs&keyword={encoded}")
    page.wait_for_timeout(2500)
    articles = page.query_selector_all('article.css-790i1i a[href^="/gig/"]')

    for i, article in enumerate(articles[:5]):
        href = article.get_attribute("href")
        if gig_id in href:
            browser.close()
            return f"{i+1}위"
    browser.close()
    return "❌ 없음"

# Streamlit 앱
st.set_page_config(page_title="크몽 키워드 순위", layout="wide")
st.title("🔍 크몽 키워드 순위 추적기 (Playwright 버전)")

# 시작 버튼
if st.button("✅ 순위 확인 시작"):
    final_results = {}

    with st.spinner("크몽에서 순위를 조회 중입니다..."):
        with sync_playwright() as playwright:
            total_keywords = sum(len(extract_keywords(s["raw_input"])) for s in services)
            current = 0
            progress = st.progress(0.0)

            for service in services:
                service_name = service["name"]
                gig_id = service["id"]
                keywords = extract_keywords(service["raw_input"])
                final_results[service_name] = {}

                for keyword in keywords:
                    rank = check_keyword_rank(playwright, keyword, gig_id)
                    final_results[service_name][keyword] = rank
                    current += 1
                    progress.progress(current / total_keywords)

    # 결과 출력
    st.success("✅ 모든 키워드 조회 완료!")
    for service_name, keywords in final_results.items():
        st.markdown(f"### 🔹 서비스: {service_name}")
        for keyword, rank in keywords.items():
            if rank == "❌ 없음" or rank.startswith("5"):
                st.markdown(f"<span style='color:red'>🚨 {keyword}: {rank}</span>", unsafe_allow_html=True)
            else:
                st.markdown(f"✅ {keyword}: {rank}")
