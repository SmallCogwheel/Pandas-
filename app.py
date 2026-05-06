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

# --- 뉴스 요약 API (직접 추출 방식) ---
@app.route("/get_summary")
def get_summary():
    url = request.args.get("url")
    if not url:
        return jsonify({"summary": "유효하지 않은 URL입니다."})
    
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        res = requests.get(url, headers=headers, timeout=5)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, "html.parser")
        
        # 기사 본문의 p 태그 중 의미 있는 길이만 수집
        paragraphs = soup.find_all('p')
        content = " ".join([p.get_text().strip() for p in paragraphs if len(p.get_text()) > 20])
        
        if not content:
            return jsonify({"summary": "기사 본문을 자동으로 가져올 수 없는 사이트입니다. 원문 보기 버튼을 클릭해 주세요."})

        summary = content[:350] + "..." # 앞부분 약 350자 추출
        return jsonify({"summary": summary})
    except:
        return jsonify({"summary": "뉴스 내용을 불러오는 데 실패했습니다. 보안이 걸린 사이트일 수 있습니다."})

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
            # 클릭 이벤트를 위해 class와 href 설정
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
            result_table_html = "<p>데이터가 없습니다. 검색 버튼을 다시 눌러주세요.</p>"

    return render_template_string(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>뉴스 아카이브</title>
        <link rel="stylesheet" href="/static/style.css">
        <style>
            .news-link {{ color: #4CAF50; text-decoration: underline; cursor: pointer; font-weight: bold; }}
            .summary-panel {{ min-height: 400px; }}
            #summary-content {{ line-height: 1.6; white-space: pre-wrap; }}
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
                <div id="summary-content">왼쪽 기사 제목을 클릭하면 요약본이 나타납니다.</div>
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
                    
                    contentBox.innerText = "기사 본문을 분석 중입니다... 잠시만 기다려주세요.";
                    linkBox.innerHTML = "";

                    fetch(`/get_summary?url=${{encodeURIComponent(url)}}`)
                        .then(res => res.json())
                        .then(data => {{
                            contentBox.innerText = data.summary;
                            linkBox.innerHTML = `<a href="${{url}}" target="_blank" class="btn" style="background:#2196F3;">기사 원문 전체보기</a>`;
                        }})
                        .catch(() => {{
                            contentBox.innerText = "요약을 불러오지 못했습니다.";
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
