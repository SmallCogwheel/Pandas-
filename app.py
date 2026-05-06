import os
import sqlite3
import math
import requests
import pandas as pd
from flask import Flask, request, render_template, jsonify
from bs4 import BeautifulSoup

app = Flask(__name__)

# Render 환경 DB 경로
DB_NAME = "/tmp/news_archive.db"
PAGE_SIZE = 12

def get_db_conn():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT,
            title TEXT,
            link TEXT UNIQUE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    return conn

def crawl_to_db(keyword):
    url = f"https://news.google.com/rss/search?q={keyword}&hl=ko&gl=KR&ceid=KR:ko"
    # 브라우저처럼 보이기 위한 User-Agent 설정
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.content, "xml")
        items = soup.find_all("item")
        
        conn = get_db_conn()
        for item in items:
            title = item.title.get_text()
            link = item.link.get_text()
            conn.execute("INSERT OR IGNORE INTO news (keyword, title, link) VALUES (?, ?, ?)", 
                         (keyword, title, link))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Crawl Error: {e}")

def get_news_from_db(keyword, page):
    offset = (page - 1) * PAGE_SIZE
    conn = get_db_conn()
    try:
        query = "SELECT title, link FROM news WHERE keyword = ? ORDER BY id DESC LIMIT ? OFFSET ?"
        df = pd.read_sql_query(query, conn, params=(keyword, PAGE_SIZE, offset))
        total_count = conn.execute("SELECT COUNT(*) FROM news WHERE keyword = ?", (keyword,)).fetchone()[0]
        return df, total_count
    except:
        return pd.DataFrame(), 0
    finally:
        conn.close()

@app.route("/get_summary")
def get_summary():
    url = request.args.get("url")
    if not url:
        return jsonify({"summary": "URL이 누락되었습니다."})

    try:
        # 1. 기사 페이지 접속 (리다이렉트 허용 및 타임아웃 설정)
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
        res = requests.get(url, headers=headers, timeout=7, allow_redirects=True)
        res.encoding = res.apparent_encoding # 인코딩 자동 감지 (한글 깨짐 방지)
        
        soup = BeautifulSoup(res.text, "html.parser")
        
        # 2. 불필요한 요소 제거 (스크립트, 스타일, 광고 등)
        for s in soup(['script', 'style', 'iframe', 'header', 'footer', 'nav']):
            s.decompose()

        # 3. 본문 추출 전략: 기사 본문에 흔히 쓰이는 class/id 키워드 탐색
        # article, content, body, news 등 기사 본문일 확률이 높은 태그들을 수집
        body_elements = soup.find_all(['div', 'article', 'section', 'p'], 
                                      class_=lambda x: x and any(k in x.lower() for k in ['article', 'content', 'post', 'body', 'news_txt']))
        
        if not body_elements:
            # 특정 클래스가 없으면 모든 p 태그에서 추출
            body_elements = soup.find_all('p')

        # 4. 텍스트 정제 (의미 있는 길이의 문장만 합치기)
        content_parts = []
        for el in body_elements:
            text = el.get_text().strip()
            if len(text) > 30: # 너무 짧은 문구(광고, 버튼 등) 제외
                content_parts.append(text)
        
        full_content = " ".join(content_parts)

        # 5. 최종 결과 반환
        if not full_content or len(full_content) < 50:
            return jsonify({"summary": "이 사이트는 보안 정책이나 구조적 이유로 본문 자동 추출이 차단되었습니다. 자세한 내용은 '원문 보기' 버튼을 이용해 주세요."})
        
        return jsonify({"summary": full_content[:450] + "..."}) # 최대 450자 노출

    except Exception as e:
        print(f"Summary Error: {e}")
        return jsonify({"summary": "뉴스 사이트에 접속할 수 없거나 응답이 너무 느립니다. (타임아웃)"})

@app.route("/", methods=["GET", "POST"])
def home():
    keyword = request.args.get("keyword", "")
    page = int(request.args.get("page", 1))

    if request.method == "POST":
        keyword = request.form.get("keyword", "").strip()
        page = 1
        if keyword:
            crawl_to_db(keyword)

    result_table_html = ""
    total_pages = 1
    
    if keyword:
        df, total_news = get_news_from_db(keyword, page)
        total_pages = math.ceil(total_news / PAGE_SIZE) if total_news > 0 else 1

        if not df.empty:
            # JS에서 인식할 수 있도록 class="news-link" 고정
            df["제목"] = df.apply(
                lambda row: f'<a href="{row["link"]}" class="news-link">{row["title"]}</a>', axis=1
            )
            result_table_html = df[["제목"]].to_html(index=False, escape=False, classes="news-table")

    return render_template("index.html", 
                           keyword=keyword, 
                           result_table_html=result_table_html, 
                           page=page, 
                           total_pages=total_pages)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
