# 📰 뉴스 검색 웹앱

키워드를 입력하면 관련 뉴스 기사를 찾아주는 간단한 웹 애플리케이션입니다.

## 🚀 기능

* 🔍 키워드 기반 뉴스 검색
* 🌐 Google 뉴스 RSS 활용 (안정적인 데이터 수집)
* 🖱️ 기사 제목 클릭 시 원문 페이지 이동
* 📊 결과를 표 형태로 출력
* 🎨 CSS 적용으로 간단한 UI 개선

## 🛠️ 사용 기술

* Python (Flask)
* BeautifulSoup
* Pandas
* HTML / CSS
* Google News RSS

## 📁 프로젝트 구조

```
Pandas-/
├── app.py
├── requirements.txt
├── static/
│   └── style.css
```

## ▶️ 실행 방법

```bash
pip install -r requirements.txt
python app.py
```

브라우저에서 아래 주소로 접속:

```
http://localhost:5000
```

## 🌍 배포

* Render를 이용해 배포
* 일정 시간 미사용 시 서버가 sleep 상태로 전환됨

## 📌 예시

* "인공지능"
* "삼성전자"
* "아이폰"

## 💡 향후 개선

* 뉴스 출처 및 날짜 표시
* 카드형 UI
* 검색 히스토리 저장
* 다크모드

---

## 👨‍💻 만든 이유

Flask를 활용한 간단한 웹서비스 구현과
크롤링 및 데이터 처리 연습을 위해 제작했습니다.
