import re
import time
import json
import urllib.parse
from datetime import datetime
import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

class KmongRankTracker:
    def __init__(self):
        # 크롬 설정
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1200x800")
        
        # Streamlit 환경에서는 webdriver-manager를 사용하지 않고 직접 경로 지정 가능
        # Streamlit Cloud에서는 chromium이 기본 설치되어 있음
        try:
            self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        except:
            # Streamlit Cloud 환경에서 실행 시 예외 처리
            self.driver = webdriver.Chrome(options=options)
        
        # 이전 기록을 st.session_state에 저장
        if 'previous_results' not in st.session_state:
            st.session_state.previous_results = {}
        
        # 현재 결과 저장할 딕셔너리
        self.current_results = {}
        
        # 이전 결과 불러오기
        self.previous_results = self.load_previous_results()

    def load_previous_results(self):
        """이전 검색 결과 불러오기 (Streamlit session_state 사용)"""
        return st.session_state.previous_results

    def save_current_results(self):
        """현재 검색 결과 저장하기 (Streamlit session_state 사용)"""
        st.session_state.previous_results = self.current_results.copy()
        st.sidebar.success("✅ 결과가 저장되었습니다. 다음 검색 시 비교에 사용됩니다.")

    def parse_input(self, raw_input):
        """입력 문자열에서 키워드와 가격 추출"""
        pairs = re.findall(r'(.+?)\n([\d,]+)원', raw_input.strip())
        keywords_with_prices = []
        for keyword, price in pairs:
            keywords_with_prices.append({
                'keyword': keyword.strip(),
                'price': price.strip()
            })
        return keywords_with_prices

    def search_rankings(self, service_id, keywords_with_prices):
        """키워드 순위 검색"""
        service_results = {}
        
        # 진행 상황 표시
        progress_text = st.empty()
        keyword_progress = st.progress(0)
        
        total_keywords = len(keywords_with_prices)
        
        for idx, item in enumerate(keywords_with_prices):
            keyword = item['keyword']
            price = item['price']
            
            progress_text.text(f"검색중: '{keyword}' - {price}원 ({idx+1}/{total_keywords})")
            keyword_progress.progress((idx) / total_keywords)
            
            encoded = urllib.parse.quote(keyword)
            url = f"https://kmong.com/search?type=gigs&keyword={encoded}"
            
            self.driver.get(url)
            time.sleep(2.5)  # 로딩 대기
            
            # 현재 페이지 스크린샷 캡처 (디버깅 목적)
            try:
                screenshot = self.driver.get_screenshot_as_png()
                from PIL import Image
                import io
                image = Image.open(io.BytesIO(screenshot))
                
                # 이미지 크기 줄이기
                width, height = image.size
                new_width = 800
                new_height = int(height * (new_width / width))
                resized_image = image.resize((new_width, new_height))
                
                # 디버깅 목적으로 이미지 저장 (토글로 끄고 켤 수 있음)
                if st.session_state.get('show_screenshots', False):
                    st.sidebar.image(resized_image, caption=f"검색: {keyword}", use_column_width=True)
            except Exception as e:
                st.warning(f"스크린샷 캡처 실패: {e}")
            
            articles = self.driver.find_elements(By.CSS_SELECTOR, 'article.css-790i1i a[href^="/gig/"]')
            
            found = False
            for i, article in enumerate(articles[:10]):  # 상위 10개까지 검색
                href = article.get_attribute('href')
                if f"/gig/{service_id}" in href:
                    rank = i + 1
                    service_results[keyword] = {
                        'rank': rank,
                        'price': price,
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    found = True
                    break
                    
            if not found:
                service_results[keyword] = {
                    'rank': "없음", 
                    'price': price,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            
            keyword_progress.progress((idx+1) / total_keywords)
        
        # 진행 표시 지우기
        progress_text.empty()
        keyword_progress.empty()
                
        return service_results

    def get_rank_change(self, service_id, keyword, current_rank):
        """순위 변동 계산"""
        if service_id not in self.previous_results or keyword not in self.previous_results[service_id]:
            return "NEW"
            
        prev_rank = self.previous_results[service_id][keyword]['rank']
        
        if prev_rank == "없음" and current_rank == "없음":
            return "="
        elif prev_rank == "없음":
            return "NEW"
        elif current_rank == "없음":
            return "OUT"
            
        try:
            prev_rank = int(prev_rank)
            current_rank = int(current_rank)
            
            if prev_rank == current_rank:
                return "="
            elif current_rank < prev_rank:
                return f"+{prev_rank - current_rank}"
            else:
                return f"-{current_rank - prev_rank}"
        except:
            return "?"

    def display_results(self):
        """Streamlit을 사용하여 결과 출력 및 이전 결과와 비교"""
        st.header("📊 크몽 키워드 순위 추적 결과")
        st.subheader(f"현재 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        for service_id, keywords in self.current_results.items():
            st.subheader(f"🔍 서비스 번호: {service_id}")
            
            # 데이터프레임용 데이터 준비
            df_data = []
            
            for keyword, data in keywords.items():
                current_rank = data['rank']
                change = self.get_rank_change(service_id, keyword, current_rank)
                
                # 변동에 따라 표시 형식 변경
                if change == "=":
                    change_display = "="
                elif change == "NEW":
                    change_display = "NEW"
                elif change == "OUT":
                    change_display = "OUT"
                elif change.startswith("+"):
                    change_display = f"↑{change[1:]}"
                elif change.startswith("-"):
                    change_display = f"↓{change[1:]}"
                else:
                    change_display = change
                
                df_data.append({
                    "키워드": keyword,
                    "가격": data['price'],
                    "순위": current_rank,
                    "변동": change_display
                })
            
            # Streamlit 데이터프레임으로 표시
            import pandas as pd
            df = pd.DataFrame(df_data)
            st.dataframe(df, use_container_width=True)
            
            # CSV 다운로드 버튼 추가
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label=f"서비스 {service_id} 결과 CSV 다운로드",
                data=csv,
                file_name=f"kmong_rank_service_{service_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
            )
            
            st.markdown("---")

    def run(self, services_data):
        """메인 실행 함수"""
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            total_services = len(services_data)
            
            for i, service_item in enumerate(services_data):
                service_id = service_item['service_id']
                raw_input = service_item['keywords_input']
                
                status_text.text(f"🔍 서비스 {service_id} 순위 검색 중... ({i+1}/{total_services})")
                progress_bar.progress((i) / total_services)
                
                keywords_with_prices = self.parse_input(raw_input)
                
                # 검색 실행 및 결과 저장
                service_results = self.search_rankings(service_id, keywords_with_prices)
                self.current_results[service_id] = service_results
                
                progress_bar.progress((i+1) / total_services)
            
            status_text.text("✅ 검색 완료")
            progress_bar.progress(1.0)
            
            # 결과 표시
            self.display_results()
            
            # 현재 결과 저장
            self.save_current_results()
            
        finally:
            self.driver.quit()


# Streamlit 앱 설정
def main():
    st.set_page_config(
        page_title="크몽 키워드 순위 추적기",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("크몽 키워드 순위 추적기")
    st.markdown("특정 서비스의 크몽 검색 순위를 추적하는 도구입니다.")
    
    with st.sidebar:
        st.header("설정")
        
        # 서비스 데이터 입력 (최대 6개)
        service_count = st.slider("추적할 서비스 수", 1, 6, 1)
        
        services_data = []
        for i in range(service_count):
            st.subheader(f"서비스 #{i+1}")
            service_id = st.text_input(f"서비스 ID #{i+1} (URL의 /gig/ 뒤 숫자)", key=f"service_id_{i}")
            
            # 예시 데이터 버튼
            if st.button(f"예시 데이터 입력 #{i+1}", key=f"example_btn_{i}"):
                example_data = """유입수
970원
트래픽 기밀
1,680원
웹사이트트래픽
1,700원
검색트래픽
1,680원"""
                st.session_state[f"keywords_{i}"] = example_data
            
            keywords_input = st.text_area(f"키워드 및 가격 입력 #{i+1} (키워드와 가격을 번갈아 한 줄씩 입력)", 
                                        height=150, key=f"keywords_{i}")
            
            # 예시 키워드로 서비스 ID가 비어있는 경우에도 기본값 제공
            if service_id or keywords_input:
                services_data.append({
                    'service_id': service_id if service_id else "예시ID입력필요",
                    'keywords_input': keywords_input
                })
        
        # 디버깅 옵션
        st.checkbox("검색 스크린샷 표시 (디버깅)", key="show_screenshots")
        
        # 트래커 실행 버튼
        if st.button("순위 추적 시작", type="primary"):
            if services_data:
                if any(item['service_id'] == "예시ID입력필요" for item in services_data):
                    st.error("서비스 ID를 모두 입력해주세요.")
                else:
                    tracker = KmongRankTracker()
                    tracker.run(services_data)
            else:
                st.error("최소 하나의 서비스 ID와 키워드를 입력해주세요.")
                
        # 세션 초기화 버튼
        if st.button("이전 결과 초기화"):
            st.session_state.previous_results = {}
            st.success("이전 결과가 초기화되었습니다.")
            
        # 결과 내보내기 및 가져오기
        st.subheader("결과 관리")
        
        # 결과 내보내기 버튼
        if st.session_state.previous_results:
            results_json = json.dumps(st.session_state.previous_results, ensure_ascii=False)
            st.download_button(
                label="이전 결과 내보내기 (JSON)",
                data=results_json,
                file_name=f"kmong_rank_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
            )
        
        # 결과 가져오기 업로더
        uploaded_file = st.file_uploader("이전 결과 가져오기 (JSON)", type="json")
        if uploaded_file is not None:
            try:
                uploaded_data = json.load(uploaded_file)
                st.session_state.previous_results = uploaded_data
                st.success("이전 결과를 성공적으로 가져왔습니다!")
            except Exception as e:
                st.error(f"파일 처리 중 오류가 발생했습니다: {e}")
        
        # 도움말
        with st.expander("사용 방법"):
            st.markdown("""
            1. 서비스 ID를 입력합니다 (크몽 URL에서 /gig/ 뒤의 숫자).
            2. 키워드와 가격을 번갈아 한 줄씩 입력합니다.
               ```
               유입수
               970원
               트래픽 기밀
               1,680원
               ```
            3. '순위 추적 시작' 버튼을 클릭합니다.
            4. 결과는 CSV로 다운로드할 수 있습니다.
            5. 다음 검색 시 순위 변동이 표시됩니다.
            """)

# Streamlit 앱 실행
if __name__ == "__main__":
    # 세션 상태 초기화
    if 'show_screenshots' not in st.session_state:
        st.session_state.show_screenshots = False
    
    if 'previous_results' not in st.session_state:
        st.session_state.previous_results = {}
    
    main()
