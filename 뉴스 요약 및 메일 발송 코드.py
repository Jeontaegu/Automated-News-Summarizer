import urllib.request
import json
import requests
from bs4 import BeautifulSoup
import re
import google.generativeai as genai

# ---------------------------------------------------------
# 1. API 키 세팅
# ---------------------------------------------------------
NAVER_CLIENT_ID = ""
NAVER_CLIENT_SECRET = ""
GEMINI_API_KEY = ""

# Gemini API 설정
genai.configure(api_key=GEMINI_API_KEY)

# 요약 작업에는 빠르고 효율적인 'gemini-3.5-flash' 모델을 사용합니다.
model = genai.GenerativeModel('gemini-3.5-flash')

# ---------------------------------------------------------
# 2. 기사 본문 스크래핑 함수 (네이버 뉴스 기준)
# ---------------------------------------------------------
def get_article_text(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')

        # 네이버 뉴스 본문이 담긴 id (dic_area) 추출
        article = soup.find('article', id='dic_area')
        if article:
            return article.text.strip()
        return None
    except Exception as e:
        print(f"스크래핑 에러: {e}")
        return None

# ---------------------------------------------------------
# 3. Gemini 3줄 요약 함수
# ---------------------------------------------------------
def summarize_text_with_gemini(text):
    if not text:
        return "기사 본문을 불러오지 못해 요약할 수 없습니다."

    try:
        # Gemini에게 전달할 프롬프트(명령어) 작성
        prompt = f"너는 뉴스 기사 요약 전문가야. 다음 기사 본문을 반드시 '3줄'로 요약해줘.\n\n[기사 본문]\n{text}"

        response = model.generate_content(prompt)
        return response.text

    except Exception as e:
        return f"요약 중 오류 발생: {e}"

# ---------------------------------------------------------
# 4. 메인 실행부
# ---------------------------------------------------------
keyword="부동산"#원하는 키워드 작성
encText = urllib.parse.quote(keyword)
url = "https://openapi.naver.com/v1/search/news?query=" + encText + "&display=100&start=1&sort=sim"

request = urllib.request.Request(url)
request.add_header("X-Naver-Client-Id", NAVER_CLIENT_ID)
request.add_header("X-Naver-Client-Secret", NAVER_CLIENT_SECRET)

response = urllib.request.urlopen(request)
rescode = response.getcode()

if rescode == 200:
    cnt=1
    response_body = response.read()
    data = json.loads(response_body.decode('utf-8'))
    total="" #비어있는 문자열
    total+=("=== [AI 기술] 네이버 뉴스 3줄 요약 (Powered by Gemini) ===\n")

    for i, item in enumerate(data['items'], 1):
        clean_title = re.sub(r'<[^>]*>', '', item['title'])
        news_link = item['link']



        # 네이버 내부 기사만 본문 추출 진행
        if "n.news.naver.com" in news_link:
            print(f"[{cnt}] 제목: {clean_title}")
            total+=(f"[{cnt}] 제목: {clean_title}\n")
            print(f"링크: {news_link}")
            total+=(f"링크: {news_link}\n")

            article_body = get_article_text(news_link)
            summary = summarize_text_with_gemini(article_body)
            print("[3줄 요약]")
            total+=("[3줄 요약]\n")
            print(summary)
            total+=(summary+"\n")


            cnt+=1
            print("-" * 60)
        if cnt==4:
          break
        #else:
        #    print("[알림] 언론사 자체 홈페이지 링크이므로 본문 스크래핑을 건너뜁니다.")


else:
    print("Error Code:" + str(rescode))

print(total)

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import getpass
from datetime import datetime #시간 함수
from zoneinfo import ZoneInfo

def send_email(message_body):
    print("=== 이메일 전송 프로그램 ===")

    # 1. 사용자 입력 받기
    sender_email = input("보내는 사람의 Gmail 주소: ")
    #sender_email="YOUR-EMAIL"
    # 보안을 위해 getpass를 사용하여 비밀번호 입력 시 화면에 표시되지 않게 합니다.
    sender_password = getpass.getpass("Gmail 앱 비밀번호 (16자리): ")

    receiver_email = input("받는 사람의 이메일 주소: ")
    kr_time = datetime.now(ZoneInfo("Asia/Seoul"))
    current_time_kr=kr_time.strftime("%Y-%m-%d %H:%M")
    subject = current_time_kr+" Keyword : "+keyword    #메일 제목
    
    # 2. 이메일 메시지 구성
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject
    msg.attach(MIMEText(message_body, 'plain'))

    # 3. SMTP 서버 연결 및 메일 전송
    try:
        # Gmail SMTP 서버 주소 및 포트 번호 설정
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls() # TLS 보안 연결 시작

        # 로그인
        server.login(sender_email, sender_password)

        # 메일 전송
        server.send_message(msg)
        print("\n✅ 이메일이 성공적으로 전송되었습니다!")

    except smtplib.SMTPAuthenticationError:
        print("\n❌ 로그인 실패: 이메일 주소나 앱 비밀번호를 다시 확인해주세요.")
    except Exception as e:
        print(f"\n❌ 오류가 발생했습니다: {e}")

    finally:
        # 서버 연결 종료
        server.quit()

# 함수 실행
send_email(total)
