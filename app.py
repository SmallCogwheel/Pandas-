import os
import sqlite3
import math
import requests
import pandas as pd
from flask import Flask, request, render_template, jsonify
from bs4 import BeautifulSoup

app = Flask(__name__)

# Render 환경에서 가장 안전한 임시 DB 경로
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
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
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
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=5)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, "html.parser")
        paragraphs = soup.find_all('p')
        content = " ".join([p.get_text().strip() for p in paragraphs if len(p.get_text()) > 25])
        return jsonify({"summary": content[:400] + "..." if content else "본문을 추출할 수 없습니다."})
    except:
        return jsonify({"summary": "내용을 불러오는 데 실패했습니다."})

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
