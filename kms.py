import re
import time
import urllib.parse
import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

def run_search():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1200x800")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    services = [
    {"name": "맞춤형 트래픽", "id": "/gig/65843", "raw_input": """
    
    
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
        """},
        {"name": "기사형 백링크", "id": "/gig/167816", "raw_input": """
    
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
        """},
    ]

    final_results = {}

    for service in services:
        name = service["name"]
        gig_id = service["id"]
        raw = service["raw_input"]

        pairs = re.findall(r'(.+?)\n[\d,]+원', raw.strip())
        keywords = [k.strip() for k in pairs]
        final_results[name] = {}

        for keyword in keywords:
            encoded = urllib.parse.quote(keyword)
            url = f"https://kmong.com/search?type=gigs&keyword={encoded}"
            driver.get(url)
            time.sleep(5)

            articles = driver.find_elements(By.CSS_SELECTOR, 'article.css-790i1i a[href^="/gig/"]')

            found = False
            for i, article in enumerate(articles[:5]):
                href = article.get_attribute('href')
                if gig_id in href:
                    final_results[name][keyword] = f"{i+1}위"
                    found = True
                    break
            if not found:
                final_results[name][keyword] = "❌ 없음"

    driver.quit()
    return final_results


# Streamlit 앱 시작
st.title("🕵️‍♂️ 키몽 키워드 검색 랭킹 확인기")
if st.button("🔍 확인 시작"):
    with st.spinner("검색 중입니다..."):
        results = run_search()
    st.success("✅ 완료되었습니다!")

    for service, keywords in results.items():
        st.subheader(f"🔹 서비스: {service}")
        for keyword, rank in keywords.items():
            if rank == "❌ 없음" or (rank.endswith("위") and int(rank[:-1]) >= 5):
                st.markdown(f"❌ **{keyword}**: `{rank}`", unsafe_allow_html=True)
            else:
                st.markdown(f"✅ **{keyword}**: `{rank}`")
