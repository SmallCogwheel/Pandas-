import os
import sqlite3
import math
import requests
import pandas as pd
from flask import Flask, request, render_template_string, jsonify
from bs4 import BeautifulSoup

app = Flask(__name__)

# Render에서 가장 안전한 임시 경로 사용
DB_NAME = "/tmp/news_archive.db"
PAGE_SIZE = 10

# --- DB 연결 및 테이블 생성 보장 ---
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

# --- 뉴스 수집 및 DB 저장 ---
def crawl_to_db(keyword):
    url = f"https://news.google.com/rss/search?q={keyword}&hl=ko&gl=KR&ceid=KR:ko"
    headers = {"User-Agent": "Mozilla/5.0"}
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

# --- DB 데이터 로드 ---
def get_news_from_db(keyword, page):
    offset = (page - 1) * PAGE_SIZE
    conn = get_db_conn()
    try:
        query = "SELECT title, link FROM news WHERE keyword = ? ORDER BY id DESC LIMIT ? OFFSET ?"
        df = pd.read_sql_query(query, conn, params=(keyword, PAGE_SIZE, offset))
        total_count = conn.execute("SELECT COUNT(*) FROM news WHERE keyword = ?", (keyword,)).fetchone()[0]
        return df, total_count
    except Exception as e:
        print(f"DB Load Error: {e}")
        return pd.DataFrame(), 0
    finally:
        conn.close()

@app.route("/get_summary")
def get_summary():
    return jsonify({"summary": "Render 무료 플랜 성능 제한으로 인해 상세 요약 기능은 준비 중입니다."})

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
        total_pages = math.ceil(total_news / PAGE_SIZE) if total_news > 0 else 1

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
        else:
            result_table_html = "<p>수집된 데이터가 없습니다.</p>"

    # HTML 템플릿 반환 (f-string 내의 중괄호 처리에 유의하세요)
    return render_template_string(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>뉴스 아카이브</title>
        <link rel="stylesheet" href="/static/style.css">
        <style>
            .news-link {{ color: #4CAF50; text-decoration: underline; cursor: pointer; font-weight: bold; }}
        </style>
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
                <div id="summary-content">왼쪽 리스트에서 뉴스 제목을 클릭하세요.</div>
                <div id="original-link-box" style="margin-top:20px;"></div>
            </div>
        </div>

        <script>
            document.addEventListener('click', function (e) {{
                if (e.target && e.target.classList.contains('news-link')) {{
                    e.preventDefault();
                    
                    const url = e.target.getAttribute('href');
                    const contentBox = document.getElementById('summary-content');
                    const linkBox = document.getElementById('original-link-box');
                    
                    contentBox.innerText = "서버에서 내용을 분석 중입니다...";
                    linkBox.innerHTML = "";

                    fetch(`/get_summary?url=${{encodeURIComponent(url)}}`)
                        .then(res => res.json())
                        .then(data => {{
                            contentBox.innerText = data.summary;
                            linkBox.innerHTML = `<a href="${{url}}" target="_blank" class="btn" style="background:#2196F3;">기사 원문 전체보기</a>`;
                        }})
                        .catch(err => {{
                            contentBox.innerText = "오류가 발생했습니다.";
                        }});
                }}
            }});
        </script>
    </body>
    </html>
    """)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
