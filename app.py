import re
import time
import urllib.parse
import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

st.set_page_config(page_title="키워드 순위 확인기", layout="wide")
st.title("🔍 키워드 순위 확인기")

options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1200x800")

# chromedriver 경로 직접 지정
service = Service("/usr/bin/chromedriver")
driver = webdriver.Chrome(service=service, options=options)


# 서비스와 키워드 데이터
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

# 순위 분석
with st.spinner("🔍 검색 중..."):
    for service in services:
        name = service["name"]
        gig_id = service["id"]
        raw_input = service["raw_input"]
        keywords = re.findall(r'(.+?)\n[\d,]+원', raw_input.strip())
        keywords = [kw.strip() for kw in keywords]

        st.subheader(f"📦 서비스: {name}")
        for keyword in keywords:
            encoded = urllib.parse.quote(keyword)
            url = f"https://kmong.com/search?type=gigs&keyword={encoded}"
            driver.get(url)
            time.sleep(3)

            articles = driver.find_elements(By.CSS_SELECTOR, 'article.css-790i1i a[href^="/gig/"]')

            found = False
            for i, article in enumerate(articles):
                href = article.get_attribute('href')
                if gig_id in href:
                    found = True
                    if i < 5:
                        st.markdown(f"- ✅ **{keyword}**: {i+1}위")
                    else:
                        st.markdown(f"<span style='color:orange'>- ⚠️ <b>{keyword}</b>: {i+1}위 (5위 밖)</span>", unsafe_allow_html=True)
                    break
            if not found:
                st.markdown(f"<span style='color:red'>- ❌ <b>{keyword}</b>: 검색결과 없음</span>", unsafe_allow_html=True)

# 종료
driver.quit()
