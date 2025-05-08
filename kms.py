import streamlit as st
import re
import time
import json
import urllib.parse
from io import StringIO
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

st.set_page_config(page_title="Kmong 순위 조회기", layout="wide")
st.title("🔍 Kmong 키워드 검색 순위 추적기")

# 이전 결과 파일 업로드
uploaded_file = st.file_uploader("📂 이전 검색 결과 JSON 업로드 (선택)", type="json")
prev_results = {}
if uploaded_file:
    prev_results = json.load(uploaded_file)

# Chrome headless 설정
options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1200x800")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# 현재 결과 저장용
current_results = {}

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

            for keyword in keywords:
                encoded = urllib.parse.quote(keyword)
                url = f"https://kmong.com/search?type=gigs&keyword={encoded}"
                driver.get(url)
                time.sleep(2.5)
                articles = driver.find_elements(By.CSS_SELECTOR, 'article.css-790i1i a[href^="/gig/"]')

                found = False
                for i, article in enumerate(articles[:5]):
                    href = article.get_attribute('href')
                    if service_id in href:
                        results[keyword] = f"{i+1}위"
                        found = True
                        break
                if not found:
                    results[keyword] = "없음"

            current_results[service_name] = results

            st.markdown("### 📊 결과 비교")
            for keyword, rank in results.items():
                if prev_results:
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
                else:
                    st.write(f"- {keyword}: {rank}")


driver.quit()

# 다운로드용 JSON 만들기
if current_results:
    st.subheader("📥 결과 저장")
    json_data = json.dumps(current_results, ensure_ascii=False, indent=2)
    st.download_button("📁 결과 JSON 다운로드", json_data, file_name="kmong_results.json", mime="application/json")
