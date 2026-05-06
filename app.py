import os
import sqlite3
import math
import requests
import pandas as pd
from flask import Flask, request, render_template_string, jsonify
from bs4 import BeautifulSoup

app = Flask(__name__)

# Render의 휘발성 디스크 경로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "news_archive.db")

# --- DB 초기화 ---
def init_db():
    try:
        with sqlite3.connect(DB_NAME) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS news (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    keyword TEXT,
                    title TEXT,
                    link TEXT UNIQUE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
    except Exception as e:
        print(f"DB Init Error: {e}")

# --- 뉴스 수집 및 DB 저장 ---
def crawl_to_db(keyword):
    url = f"https://news.google.com/rss/search?q={keyword}&hl=ko&gl=KR&ceid=KR:ko"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.content, "xml")
        items = soup.find_all("item")
        
        with sqlite3.connect(DB_NAME) as conn:
            for item in items:
                title = item.title.get_text()
                link = item.link.get_text()
                conn.execute("INSERT OR IGNORE INTO news (keyword, title, link) VALUES (?, ?, ?)", 
                             (keyword, title, link))
            conn.commit()
    except Exception as e:
        print(f"Crawl Error: {e}")

# --- DB 데이터 로드 ---
def get_news_from_db(keyword, page):
    offset = (page - 1) * PAGE_SIZE
    with sqlite3.connect(DB_NAME) as conn:
        query = "SELECT title, link FROM news WHERE keyword = ? ORDER BY id DESC LIMIT ? OFFSET ?"
        df = pd.read_sql_query(query, conn, params=(keyword, PAGE_SIZE, offset))
        total_count = conn.execute("SELECT COUNT(*) FROM news WHERE keyword = ?", (keyword,)).fetchone()[0]
    return df, total_count

PAGE_SIZE = 10

@app.route("/get_summary")
def get_summary():
    # Render 무료 플랜의 메모리 부족을 방지하기 위해 텍스트만 반환하도록 단순화
    return jsonify({"summary": "현재 상세 요약 기능은 서버 안정화를 위해 점검 중입니다. 원문 링크를 통해 전체 내용을 확인해 주세요!"})

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
    pagination_html = ""
    
    if keyword:
        df, total_news = get_news_from_db(keyword, page)
        total_pages = math.ceil(total_news / PAGE_SIZE)

        if not df.empty:
            df["제목"] = df.apply(
                lambda row: f'<a href="{row["link"]}" class="news-link">{row["title"]}</a>', axis=1
            )
            result_table_html = df[["제목"]].to_html(index=False, escape=False, classes="news-table")

            pagination_html = '<div class="pagination">'
            if page > 1:
                pagination_html += f'<a href="/?keyword={keyword}&page={page-1}" class="btn">이전</a>'
            pagination_html += f'<span class="page-num">{page} / {total_pages}</span>'
            if page < total_pages:
                pagination_html += f'<a href="/?keyword={keyword}&page={page+1}" class="btn">다음</a>'
            pagination_html += '</div>'

    return render_template_string(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>뉴스 아카이브</title>
        <link rel="stylesheet" href="/static/style.css">
    </head>
    <body>
        <h2>📰 뉴스 무한 검색 & 요약</h2>
        <form method="POST" action="/">
            <input name="keyword" placeholder="키워드 입력" value="{keyword}">
            <button type="submit">검색 및 수집</button>
        </form>
        <hr>
        <div class="main-container">
            <div class="news-list">
                {result_table_html}
                {pagination_html}
            </div>
            <div id="summary-panel" class="summary-panel">
                <h3>📄 뉴스 미리보기</h3>
                <div id="summary-content">뉴스를 선택하면 요약 내용이 표시됩니다.</div>
                <div id="original-link-box"></div>
            </div>
        </div>

        <script>
            document.querySelectorAll('.news-link').forEach(link => {{
                link.addEventListener('click', function(e) {{
                    e.preventDefault();
                    const url = this.href;
                    const contentBox = document.getElementById('summary-content');
                    const linkBox = document.getElementById('original-link-box');
                    
                    contentBox.innerText = "내용을 불러오는 중...";
                    linkBox.innerHTML = "";

                    fetch(`/get_summary?url=${{encodeURIComponent(url)}}`)
                        .then(res => res.json())
                        .then(data => {{
                            contentBox.innerText = data.summary;
                            linkBox.innerHTML = `<br><a href="${{url}}" target="_blank" class="btn">기사 원문 보기</a>`;
                        }});
                }});
            }});
        </script>
    </body>
    </html>
    """)

if __name__ == "__main__":
    init_db()
    # Render는 PORT 환경변수를 통해 포트를 할당합니다.
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
