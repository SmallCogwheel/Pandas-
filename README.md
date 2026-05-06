# 📰 뉴스 아카이브 & 실시간 요약 웹앱

키워드를 입력하면 뉴스를 수집하고 데이터베이스에 저장한 뒤,
선택한 기사 내용을 실시간으로 분석하여 요약해주는 웹 애플리케이션입니다.

👉 배포 주소: https://pandas-nrp0.onrender.com/

---

## 🚀 주요 기능

* 🔍 **키워드 기반 뉴스 수집**
* 💾 **SQLite DB 저장 (중복 자동 제거)**
* 📄 **기사 클릭 시 실시간 요약**
* 📊 **페이지네이션 (이전 / 다음)**
* ⚡ **Fetch API 기반 비동기 데이터 처리**
* 🎨 **분리된 HTML / CSS / JS 구조**

---

## 🛠️ 기술 스택

### Backend

* Python (Flask)
* SQLite3
* BeautifulSoup (XML 파싱)
* Requests

### Frontend

* HTML (Jinja2 Template)
* CSS (스타일 분리)
* JavaScript (이벤트 처리 & API 호출)

### Infra

* Render (배포)
* Gunicorn (프로덕션 서버)

---

## 📁 프로젝트 구조

```bash
Pandas-/
├── app.py
├── requirements.txt
├── templates/
│   └── index.html
├── static/
│   ├── style.css
│   └── script.js
```

---

## ⚙️ 동작 구조

1. 키워드 입력 → Google 뉴스 RSS 요청
2. 뉴스 데이터 파싱 후 SQLite DB 저장
3. DB에서 페이지 단위로 데이터 조회
4. 뉴스 클릭 시 `/get_summary` API 호출
5. 기사 HTML 파싱 후 본문 추출 → 요약 출력

---

## ▶️ 실행 방법

```bash
pip install -r requirements.txt
python app.py
```

접속:

```
http://localhost:5000
```

---

## 🌍 배포

* Render 환경에서 실행
* `/tmp/news_archive.db` 경로 사용 (임시 DB)
* 일정 시간 미사용 시 sleep 상태 진입

---

## 📌 사용 예시

* 인공지능
* 삼성전자
* 테슬라
* 아이폰

---

## ⚠️ 주의 사항

* 일부 뉴스 사이트는 본문 크롤링이 제한될 수 있음
* RSS 특성상 최신 뉴스 위주로 수집됨
* 요약 결과는 사이트 구조에 따라 달라질 수 있음
* Render 환경에서는 DB가 재시작 시 초기화됨

---

## 💡 향후 개선 아이디어

* 🏷️ 뉴스 출처 및 날짜 표시
* ⭐ 즐겨찾기 기능
* 📚 검색 히스토리 저장
* 🤖 AI 기반 요약 (LLM)
* 🌙 다크모드

---

## 👨‍💻 프로젝트 목적

Flask 기반 웹 서비스 개발을 통해
데이터 수집 → 저장 → 처리 → API → 프론트 연동까지
전체 웹 애플리케이션 흐름을 구현하고 이해하기 위해 제작했습니다.
