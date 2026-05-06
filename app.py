import os
import sqlite3
import math
import requests
import pandas as pd
from flask import Flask, request, render_template_string, jsonify
from bs4 import BeautifulSoup

app = Flask(__name__)

# Render 임시 경로 설정
DB_NAME = "/tmp/news_archive.db"
PAGE_SIZE = 12 # 화면이 길어졌으므로 한 페이지당 뉴스 개수를 조금 늘렸습니다.

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
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
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
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        res = requests.get(url, headers=headers, timeout=5)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, "html.parser")
        paragraphs = soup.find_all('p')
        content = " ".join([p.get_text().strip() for p in paragraphs if len(p.get_text()) > 25])
        
        if not content:
            return jsonify({"summary": "본문 추출이 어려운 사이트입니다. 원문 보기 버튼을 클릭해 주세요."})
        return jsonify({"summary": content[:400] + "..."})
    except:
        return jsonify({"summary": "뉴스 내용을 불러올 수 없습니다."})

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
            df["뉴스 제목 (클릭 시 요약)"] = df.apply(
                lambda row: f'<a href="{row["link"]}" class="news-link">{row["title"]}</a>', axis=1
            )
            # 깔끔한 테이블 생성을 위해 '제목' 컬럼만 추출
            result_table_html = df[["뉴스 제목 (클릭 시 요약)"]].to_html(index=False, escape=False, classes="news-table")

            pagination_html = '<div class="pagination">'
            if page > 1:
                pagination_html += f'<a href="/?keyword={keyword}&page={page-1}" class="btn-nav">이전</a>'
            pagination_html += f'<span class="page-num">{page} / {total_pages}</span>'
            if page < total_pages:
                pagination_html += f'<a href="/?keyword={keyword}&page={page+1}" class="btn-nav">다음</a>'
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
        <div class="header-container">
            <h2>📰 뉴스 무한 검색 & 요약 시스템</h2>
            <form method="POST" action="/" class="search-form">
                <input name="keyword" placeholder="키워드 입력 (예: 삼성전자)" value="{keyword}">
                <button type="submit">검색 및 수집</button>
            </form>
        </div>

        <div class="main-container">
            <div class="news-list-box">
                <div class="scroll-area">
                    {result_table_html}
                </div>
                {pagination_html}
            </div>
            
            <div id="summary-panel" class="summary-panel">
                <div class="summary-header">
                    <h3>📄 실시간 뉴스 요약</h3>
                </div>
                <div id="summary-content">왼쪽 리스트에서 기사를 선택하세요.</div>
                <div id="original-link-box"></div>
            </div>
        </div>

        <script>
            document.addEventListener('click', function (e) {{
                if (e.target && e.target.classList.contains('news-link')) {{
                    e.preventDefault();
                    const url = e.target.getAttribute('href');
                    const contentBox = document.getElementById('summary-content');
                    const linkBox = document.getElementById('original-link-box');
                    
                    contentBox.innerHTML = '<div class="loading">기사 본문을 분석 중입니다...</div>';
                    linkBox.innerHTML = "";

                    fetch(`/get_summary?url=${{encodeURIComponent(url)}}`)
                        .then(res => res.json())
                        .then(data => {{
                            contentBox.innerText = data.summary;
                            linkBox.innerHTML = `<a href="${{url}}" target="_blank" class="btn-go">기사 원문 전체보기</a>`;
                        }})
                        .catch(() => {{
                            contentBox.innerText = "내용을 불러오지 못했습니다.";
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
