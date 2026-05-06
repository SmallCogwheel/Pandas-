import sqlite3
import math
import requests
import pandas as pd
from flask import Flask, request, render_template_string, jsonify
from bs4 import BeautifulSoup
from newspaper import Article

app = Flask(__name__)
DB_NAME = "news_archive.db"
PAGE_SIZE = 10

# --- DB 초기화 ---
def init_db():
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

# --- 뉴스 수집 및 DB 저장 ---
def crawl_to_db(keyword):
    url = f"https://news.google.com/rss/search?q={keyword}&hl=ko&gl=KR&ceid=KR:ko"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, headers=headers)
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

# --- 뉴스 요약 API ---
@app.route("/get_summary")
def get_summary():
    url = request.args.get("url")
    try:
        article = Article(url, language='ko')
        article.download()
        article.parse()
        # 본문 앞 500자 추출
        content = article.text[:500] + "..." if len(article.text) > 500 else article.text
        return jsonify({"summary": content if content.strip() else "본문 내용을 가져올 수 없는 사이트입니다."})
    except:
        return jsonify({"summary": "뉴스 읽기에 실패했습니다. 링크를 직접 클릭해 확인하세요."})

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
            # 클릭 시 요약 함수 호출하도록 class 추가
            df["제목"] = df.apply(
                lambda row: f'<a href="{row["link"]}" class="news-link">{row["title"]}</a>', axis=1
            )
            result_table_html = df[["제목"]].to_html(index=False, escape=False, classes="news-table")

            # 페이징 버튼 생성
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
                    
                    contentBox.innerText = "내용을 분석 중입니다. 잠시만 기다려주세요...";
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
    """, keyword=keyword)

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
