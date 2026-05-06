# 📰 뉴스 아카이브 & 자동 요약 웹앱

키워드를 입력하면 뉴스를 수집하고, 데이터베이스에 저장한 뒤
클릭 시 기사 내용을 자동으로 요약해주는 웹 애플리케이션입니다.

👉 배포 주소: https://pandas-nrp0.onrender.com/

---

## 🚀 주요 기능

* 🔍 키워드 기반 뉴스 검색 및 수집
* 💾 SQLite DB에 뉴스 저장 (중복 자동 제거)
* 📄 뉴스 클릭 시 본문 자동 요약
* 📊 페이지네이션 (이전 / 다음)
* 🧠 요약 API (`/get_summary`)
* ⚡ 실시간 데이터 로딩 (Fetch API)

---

## 🛠️ 기술 스택

* Python (Flask)
* SQLite3 (데이터 저장)
* BeautifulSoup + lxml (크롤링)
* Pandas (데이터 처리)
* newspaper3k (기사 본문 파싱 및 요약)
* HTML / CSS / JavaScript
* Gunicorn (배포 서버)

---

## 📁 프로젝트 구조

```bash
Pandas-/
├── app.py
├── news_archive.db
├── requirements.txt
├── static/
│   └── style.css
```

---

## ⚙️ 동작 방식

1. 키워드 입력 → Google 뉴스 RSS에서 기사 수집
2. SQLite DB에 저장 (중복 링크 방지)
3. DB에서 데이터 불러와 페이지 단위로 출력
4. 기사 클릭 시 `/get_summary` API 호출
5. newspaper3k로 기사 본문 분석 후 요약 반환

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

* Render를 이용해 배포
* Gunicorn 기반 실행
* 일정 시간 미사용 시 sleep 상태 진입

---

## 📌 사용 예시

* 인공지능
* 삼성전자
* 테슬라
* 아이폰

---

## ⚠️ 주의 사항

* 일부 뉴스 사이트는 크롤링/요약이 제한될 수 있음
* RSS 특성상 최신 뉴스 기준으로 수집됨
* 요약 결과는 원문 구조에 따라 정확도가 달라질 수 있음

---

## 💡 향후 개선 아이디어

* 🔎 검색 히스토리 저장
* 🏷️ 뉴스 카테고리 분류
* ⭐ 즐겨찾기 기능
* 🌙 다크모드
* 🤖 AI 기반 요약 개선

---

## 👨‍💻 프로젝트 목적

Flask 기반 웹 서비스 구현과
데이터 수집 → 저장 → 처리 → 출력 → API 설계까지
전체 흐름을 학습하기 위해 제작했습니다.
