import re
import time
import urllib.parse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# 크롬 설정
options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1200x800")
options.add_argument("--no-sandbox") 
options.add_argument("--disable-dev-shm-usage") 
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# 서비스 목록 및 키워드 RAW 데이터
services = [
    {"name": "블로그 트래픽", "id": "/gig/65843", "raw_input": """
    유입수
    970원
    트래픽 기밀
    1,680원
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

# 결과 저장
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

driver.quit()

# 결과 출력
print("\n📊 검색 결과 순위 요약:")
for service_name, keywords in final_results.items():
    print(f"\n🔹 서비스: {service_name}")
    for keyword, rank in keywords.items():
        print(f"  - {keyword}: {rank}")
