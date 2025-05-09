import re
import urllib.parse
import streamlit as st
import requests
from bs4 import BeautifulSoup

# 서비스 및 키워드 정의
services = [
    {"name": "기사형 백링크", "id": "/gig/167816", "raw_input": """
마케팅
5,000원
seo
3,720원
트래픽
5,070원
"""}
]

# 키워드 추출
def extract_keywords(raw):
    return re.findall(r'(.+?)\n[\d,]+원', raw.strip())

# 크몽 검색 페이지에서 순위 추출
def check_keyword_rank(keyword, gig_id):
    encoded = urllib.parse.quote(keyword)
    url = f"https://kmong.com/search?type=gigs&keyword={encoded}"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    res = requests.get(url, headers=headers)

    if res.status_code != 200:
        return "❌ 요청 실패"

    soup = BeautifulSoup(res.text, "html.parser")
    links = soup.select('article.css-790i1i a[href^="/gig/"]')

    for i, link in enumerate(links[:5]):
        href = link.get("href")
        if gig_id in href:
            return f"{i+1}위"
    return "❌ 없음"

# Streamlit 앱 시작
st.title("📊 크몽 키워드 순위 추적기 (정적 분석 버전)")

if st.button("순위 확인 시작"):
    with st.spinner("분석 중..."):
        results = {}
        for service in services:
            name = service["name"]
            gig_id = service["id"]
            keywords = extract_keywords(service["raw_input"])
            results[name] = {}

            for keyword in keywords:
                rank = check_keyword_rank(keyword, gig_id)
                results[name][keyword] = rank

    # 결과 출력
    st.success("✅ 분석 완료!")
    for name, keywords in results.items():
        st.markdown(f"### 🔹 서비스: {name}")
        for keyword, rank in keywords.items():
            if rank.startswith("5") or "❌" in rank:
                st.markdown(f"<span style='color:red'>🚨 {keyword}: {rank}</span>", unsafe_allow_html=True)
            else:
                st.markdown(f"✅ {keyword}: {rank}")
