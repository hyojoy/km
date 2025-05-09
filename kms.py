import re
import time
import urllib.parse
import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Streamlit 페이지 설정
st.set_page_config(page_title="크몽 키워드 순위 확인기", layout="wide")
st.title("📈 크몽 키워드 검색 순위 확인기")

# 크롬 드라이버 설정
@st.cache_resource
def get_driver():
    options = Options()
    options.add_argument('--headless=new')  # 최신 방식의 headless 모드
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--no-sandbox')
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1200x800")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

driver = get_driver()

# 서비스 및 키워드 RAW 데이터 정의
services = [
    {"name": "기사형 백링크", "id": "/gig/167816", "raw_input": """
마케팅
5,000원
seo
3,720원
트래픽
5,070원
최적화노출
4,330원
최적화
2,440원
백링크 트래픽
910원
대량 백링크
1,940원
국내포털백링크
740원
수작업 백링크
2,420원
백링크n
2,900원
백링크사이트
3,550원
사이트 백링크
2,910원
백링크 da
3,310원
백링크 직접
3,220원
백링크작업
3,800원
화이트햇 백링크
2,420원
seo백링크
3,000원
백링크 최적화
2,120원
구글 seo 백링크
2,800원
월관리백링크
1,710원
"""}, 
    {"name": "웹사이트 트래픽", "id": "/gig/11111", "raw_input": """
웹사이트트래픽
1,700원
검색트래픽
1,680원
"""}, 
    {"name": "국내 트래픽", "id": "/gig/22222", "raw_input": """
국내 트래픽
1,750원
웹트래픽
3,410원
"""}, 
    {"name": "프리미엄 유입", "id": "/gig/33333", "raw_input": """
프리미엄 트래픽
2,430원
트래픽 조회
1,060원
"""}, 
    {"name": "체류형 트래픽", "id": "/gig/44444", "raw_input": """
트래픽 체류시간
1,600원
트래픽 교육
1,620원
"""}, 
    {"name": "실사용자 유입", "id": "/gig/55555", "raw_input": """
실사용 트래픽
2,390원
트래픽 제
1,220원
"""}, 
    {"name": "트래픽 마케팅", "id": "/gig/66666", "raw_input": """
사이트트래픽
2,110원
트래픽 관리
2,970원
"""}
]

final_results = {}

progress_bar = st.progress(0)
total_tasks = sum(len(re.findall(r'(.+?)\n[\d,]+원', s["raw_input"].strip())) for s in services)
done_tasks = 0

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
        time.sleep(2.5)

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

        done_tasks += 1
        progress_bar.progress(done_tasks / total_tasks)

driver.quit()

# 결과 출력
st.subheader("📊 키워드별 순위 결과")

for service_name, keywords in final_results.items():
    st.markdown(f"### 🔹 서비스: {service_name}")
    for keyword, rank in keywords.items():
        if rank == "❌ 없음" or rank.startswith("5"):
            st.markdown(f"<span style='color:red'>🚨 {keyword}: {rank}</span>", unsafe_allow_html=True)
        else:
            st.markdown(f"✅ {keyword}: {rank}")
