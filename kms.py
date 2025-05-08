import streamlit as st
import re
import time
import json
import urllib.parse
import requests
from bs4 import BeautifulSoup

# Streamlit 앱 설정
st.set_page_config(page_title="Kmong 순위 조회기", layout="wide")
st.title("🔍 Kmong 키워드 검색 순위 추적기")

# 이전 결과 파일 업로드
uploaded_file = st.file_uploader("📂 이전 검색 결과 JSON 업로드 (선택)", type="json")
prev_results = {}
if uploaded_file:
    prev_results = json.load(uploaded_file)

# 현재 결과 저장용
current_results = {}

# 서비스 정보 입력 받기
st.subheader("🔧 서비스 정보 입력")
for idx in range(6):
    with st.expander(f"서비스 {idx+1} 입력", expanded=(idx == 0)):
        service_name = st.text_input(f"서비스 이름 {idx+1}", key=f"name_{idx}")
        service_id = st.text_input(f"서비스 번호 예: /gig/65843", key=f"id_{idx}")
        raw_input = st.text_area(f"키워드 + 가격 목록 (한 줄에 하나)", key=f"keywords_{idx}")

        if service_name and service_id and raw_input:
            # 키워드 추출
            pairs = re.findall(r'(.+?)\n[\d,]+원', raw_input.strip())
            keywords = [k.strip() for k in pairs]
            results = {}

            # 웹 크롤링 함수
            def get_search_results(keyword, service_id):
                encoded = urllib.parse.quote(keyword)
                url = f"https://kmong.com/search?type=gigs&keyword={encoded}"
                response = requests.get(url)
                soup = BeautifulSoup(response.text, 'html.parser')

                # 서비스 결과를 찾기
                articles = soup.select('article.css-790i1i a[href^="/gig/"]')
                for i, article in enumerate(articles[:5]):
                    href = article.get('href')
                    if service_id in href:
                        return f"{i+1}위"
                return "없음"

            # 각 키워드 순위 조회
            for keyword in keywords:
                rank = get_search_results(keyword, service_id)
                results[keyword] = rank

            # 결과 저장
            current_results[service_name] = results

            st.markdown("### 📊 결과 비교")
            for keyword, rank in results.items():
                old_rank = prev_results.get(service_name, {}).get(keyword)
                if old_rank == rank:
                    diff = "(변동 없음)"
                elif old_rank is None:
                    diff = f"(신규 검색)"
                elif rank == "없음":
                    diff = f"(이전: {old_rank} → 없음)"
                elif old_rank == "없음":
                    diff = f"(이전: 없음 → {rank})"
                else:
                    try:
                        diff_val = int(old_rank.replace("위", "")) - int(rank.replace("위", ""))
                        arrow = "▲" if diff_val > 0 else "▼"
                        diff = f"({arrow}{abs(diff_val)}위)"
                    except:
                        diff = f"(이전: {old_rank})"
                st.write(f"- {keyword}: {rank} {diff}")

# 결과를 JSON으로 저장할 수 있는 버튼 추가
if current_results:
    st.subheader("📥 결과 저장")
    json_data = json.dumps(current_results, ensure_ascii=False, indent=2)
    st.download_button("📁 결과 JSON 다운로드", json_data, file_name="kmong_results.json", mime="application/json")
