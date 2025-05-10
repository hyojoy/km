import re
import time
import urllib.parse
import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException

# Page configuration
st.set_page_config(page_title="키워드 순위 확인기", layout="wide")
st.title("🔍 키워드 순위 확인기")

# Service and keyword data
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

# Function to initialize the Chrome driver with optimized settings for limited resources
def get_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1200x800")
    
    # Use pre-installed ChromeDriver from Dockerfile
    service = Service(executable_path="/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)
    return driver

# Start analysis when user clicks the button
if st.button("키워드 순위 분석 시작"):
    try:
        # Initialize driver once before starting
        driver = get_driver()
        
        # Dictionary to store results
        results_by_service = {}
        
        # Process all services
        for service_idx, service in enumerate(services):
            name = service["name"]
            gig_id = service["id"]
            raw_input = service["raw_input"]
            
            # Extract keywords using the same regex pattern from the original code
            keywords = re.findall(r'(.+?)\n[\d,]+원', raw_input.strip())
            keywords = [kw.strip() for kw in keywords]
            
            st.subheader(f"📦 서비스: {name}")
            
            # Create a progress bar
            progress_bar = st.progress(0)
            
            # Create a placeholder for results
            results_placeholder = st.empty()
            results = []
            results_by_service[name] = {}
            
            # Process keywords
            for idx, keyword in enumerate(keywords):
                try:
                    with st.spinner(f"검색 중: {keyword}"):
                        encoded = urllib.parse.quote(keyword)
                        url = f"https://kmong.com/search?type=gigs&keyword={encoded}"
                        
                        # Try to navigate to the URL
                        driver.get(url)
                        time.sleep(5)  # Wait for page to load, same as original code
                        
                        # Use the same CSS selector as in the original code
                        articles = driver.find_elements(By.CSS_SELECTOR, 'article.css-790i1i a[href^="/gig/"]')
                        
                        found = False
                        for i, article in enumerate(articles[:5]):  # Only check first 5 results
                            href = article.get_attribute('href')
                            if gig_id in href:
                                rank = f"{i+1}위"
                                results_by_service[name][keyword] = rank
                                results.append(f"- ✅ **{keyword}**: {rank}")
                                found = True
                                break
                                
                        if not found:
                            results_by_service[name][keyword] = "❌ 없음"
                            results.append(f"- ❌ **{keyword}**: 검색결과 없음")
                        
                        # Update progress bar
                        progress_bar.progress((idx + 1) / len(keywords))
                        
                        # Update results display
                        results_placeholder.markdown("\n".join(results), unsafe_allow_html=True)
                        
                except Exception as e:
                    # If an error occurs with one keyword, log it and continue
                    error_msg = f"- ❌ **{keyword}**: 오류 발생 ({str(e)[:100]}...)"
                    results.append(error_msg)
                    results_placeholder.markdown("\n".join(results), unsafe_allow_html=True)
                    
                    # If driver crashed, recreate it
                    try:
                        driver.title  # Test if driver is still responsive
                    except:
                        st.warning("브라우저가 응답하지 않아 재시작합니다...")
                        try:
                            driver.quit()
                        except:
                            pass
                        driver = get_driver()
            
            # Clear progress bar after completion
            progress_bar.empty()
        
        # Quit driver after all operations
        try:
            driver.quit()
        except:
            pass
            
        # Show summary at the end
        st.markdown("---")
        st.subheader("📊 검색 결과 순위 요약")
        
        for service_name, keywords in results_by_service.items():
            st.markdown(f"**🔹 서비스: {service_name}**")
            for keyword, rank in keywords.items():
                st.markdown(f"  - {keyword}: {rank}")
                
        st.success("✅ 모든 키워드 분석이 완료되었습니다!")
    
    except Exception as e:
        st.error(f"오류 발생: {str(e)}")
        # Make sure to quit driver on error
        try:
            if 'driver' in locals():
                driver.quit()
        except:
            pass
else:
    st.info("👆 분석을 시작하려면 위 버튼을 클릭하세요.")

st.markdown("---")
st.markdown("#### 참고사항")
st.markdown("- 검색 결과는 실시간으로 변동될 수 있습니다.")
st.markdown("- 한 번에 너무 많은 키워드를 분석할 경우 시간이 오래 걸릴 수 있습니다.")
