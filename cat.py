import streamlit as st
import requests
from bs4 import BeautifulSoup
import re

def check_service_rank(category_id, service_id):
    """
    크몽 웹사이트에서 특정 카테고리의 전체 서비스 중 사용자의 서비스 순위를 확인합니다.
    
    Args:
        category_id (str): 확인할 카테고리 ID (예: "236")
        service_id (str): 사용자의 서비스 ID (예: "65945")
    
    Returns:
        tuple: (순위, 4위 내 포함 여부, 메시지)
    """
    # 전체 서비스 URL 생성
    url = f"https://kmong.com/category/{category_id}"
    
    try:
        # 웹페이지 요청
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            return -1, False, f"오류: 웹페이지를 가져올 수 없습니다. 상태 코드: {response.status_code}"
        
        # HTML 파싱
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 전체 서비스 탭이 선택되었는지 확인
        # 비즈 전용 서비스가 아닌 전체 서비스 내의 순위를 확인
        all_services_tab = soup.find('h4', string='전체 서비스')
        if not all_services_tab:
            # 전체 서비스 탭으로 이동 필요
            return -1, False, "전체 서비스 탭을 찾을 수 없습니다. URL이 올바른지 확인하세요."
        
        # 서비스 목록 찾기 (article 태그로 각 서비스가 구분된다고 가정)
        service_elements = soup.find_all('article')
        
        if not service_elements:
            return -1, False, "서비스 목록을 찾을 수 없습니다."
        
        # 내 서비스 찾기
        my_service_position = -1
        
        for index, service in enumerate(service_elements):
            # 서비스 링크 확인
            service_link = service.find('a', href=re.compile(f'/gig/{service_id}'))
            if service_link:
                my_service_position = index + 1  # 1부터 시작하는 순위로 변환
                break
        
        # 결과 반환
        if my_service_position == -1:
            return -1, False, "서비스를 찾을 수 없습니다. 서비스 ID가 올바른지 확인하세요."
        elif my_service_position <= 4:
            return my_service_position, True, f"내 서비스는 현재 {my_service_position}위에 있습니다! (4위 내 포함)"
        else:
            return my_service_position, False, f"내 서비스는 현재 {my_service_position}위에 있습니다. (4위 내 미포함)"
            
    except Exception as e:
        return -1, False, f"오류 발생: {str(e)}"

# Streamlit 앱 인터페이스
st.set_page_config(
    page_title="크몽 서비스 순위 확인",
    page_icon="📊",
    layout="centered"
)

st.title("크몽 서비스 순위 확인")
st.markdown("특정 카테고리 내에서 내 서비스가 4위 안에 들어있는지 확인합니다.")

# 사용자 입력
with st.form("rank_check_form"):
    category_id = st.text_input("카테고리 ID", placeholder="예: 236")
    service_id = st.text_input("내 서비스 ID", placeholder="예: 65945")
    
    st.markdown("""
    **카테고리 ID와 서비스 ID 찾는 방법:**
    - 카테고리 ID: 크몽 URL에서 `/category/` 뒤에 오는 숫자 (예: `https://kmong.com/category/236`에서 236)
    - 서비스 ID: 서비스 URL에서 `/gig/` 뒤에 오는 숫자 (예: `https://kmong.com/gig/65945`에서 65945)
    """)
    
    submitted = st.form_submit_button("순위 확인")

# 폼 제출 시 실행
if submitted:
    if not category_id or not service_id:
        st.error("카테고리 ID와 서비스 ID를 모두 입력해주세요.")
    else:
        with st.spinner("순위를 확인하는 중..."):
            position, is_in_top_four, message = check_service_rank(category_id, service_id)
        
        # 결과 표시
        if position == -1:
            st.error(message)
        elif is_in_top_four:
            st.success(message)
        else:
            st.warning(message)
        
        # 결과 상세 정보
        if position > 0:
            st.markdown("### 상세 정보")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("현재 순위", position)
            with col2:
                st.metric("4위 내 포함", "✅" if is_in_top_four else "❌")
            
            st.markdown(f"📊 [카테고리 페이지 보기](https://kmong.com/category/{category_id})")

# 추가 정보
with st.expander("도움말"):
    st.markdown("""
    ### 사용 방법
    1. 크몽 웹사이트에서 확인하고자 하는 카테고리의 ID를 입력합니다.
    2. 내 서비스의 ID를 입력합니다.
    3. '순위 확인' 버튼을 클릭합니다.
    
    ### 주의사항
    - 이 앱은 크몽 웹사이트의 HTML 구조를 기반으로 작동합니다. 웹사이트 구조가 변경되면 정상 작동하지 않을 수 있습니다.
    - 크몽 웹사이트의 정책에 따라 웹 스크래핑이 제한될 수 있습니다.
    - 개인적인 용도로만 사용하시기 바랍니다.
    """)

# 푸터
st.markdown("---")
st.markdown("© 2025 크몽 서비스 순위 확인 | 비공식 도구")
