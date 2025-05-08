import streamlit as st
import re
import urllib.parse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time

st.title("키워드 순위 확인")

service_number = st.text_input("✅ 서비스 번호", "/gig/65843")

user_input = st.text_area("🔍 키워드 + 가격 입력", height=300, placeholder="예:\n유입수\n970원\n\n트래픽 기밀\n1,680원")

if st.button("📊 순위 확인 시작"):
    if not service_number or not user_input:
        st.warning("서비스 번호와 키워드를 입력해주세요.")
    else:
        # 크롬 설정
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1200x800")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

        # 키워드 추출
        pairs = re.findall(r'(.+?)\n[\d,]+원', user_input.strip())
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
                if service_number in href:
                    results[keyword] = f"{i+1}위"
                    found = True
                    break
            if not found:
                results[keyword] = "없음"

        driver.quit()

        # 결과 출력
        st.success("✅ 순위 확인 완료!")
        for keyword, rank in results.items():
            st.write(f"**{keyword}** → {rank}")
