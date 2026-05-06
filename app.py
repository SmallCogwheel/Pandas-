from flask import Flask, request, render_template_string
import requests
from bs4 import BeautifulSoup
import pandas as pd
import math

app = Flask(__name__)

# 한 페이지에 보여줄 뉴스 개수
PAGE_SIZE = 10

def crawl(keyword):
    if not keyword:
        return []

    # RSS는 최대 100개 정도까지 한 번에 가져올 수 있음
    url = f"https://news.google.com/rss/search?q={keyword}&hl=ko&gl=KR&ceid=KR:ko"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.content, "xml")
        
        items = soup.find_all("item")
        data = []

        for item in items:
            title = item.title.get_text() if item.title else "제목 없음"
            link = item.link.get_text() if item.link else "#"
            data.append({"title": title, "link": link})
        
        return data
    except Exception as e:
        print(f"Error: {e}")
        return []

@app.route("/", methods=["GET", "POST"])
def home():
    keyword = request.args.get("keyword", "") # GET 방식으로 키워드 유지
    page = int(request.args.get("page", 1))   # 현재 페이지 번호 (기본값 1)

    # 만약 POST로 검색이 들어오면 (새로운 검색)
    if request.method == "POST":
        keyword = request.form.get("keyword", "").strip()
        page = 1 # 검색 시 첫 페이지로 리셋

    news_data = crawl(keyword)
    total_news = len(news_data)
    total_pages = math.ceil(total_news / PAGE_SIZE)

    # 현재 페이지에 해당하는 데이터만 슬라이싱
    start_idx = (page - 1) * PAGE_SIZE
    end_idx = start_idx + PAGE_SIZE
    current_items = news_data[start_idx:end_idx]

    # 결과 HTML 생성
    result_html = ""
    if keyword:
        if not current_items:
            result_html = "<p>결과가 없습니다.</p>"
        else:
            df = pd.DataFrame(current_items)
            df["제목"] = df.apply(
                lambda row: f'<a href="{row["link"]}" target="_blank" rel="noopener noreferrer">{row["title"]}</a>',
                axis=1
            )
            result_html = "<h3>검색 결과</h3>" + df[["제목"]].to_html(index=False, escape=False)

            # 페이징 버튼 생성
            pagination_html = '<div class="pagination">'
            if page > 1:
                pagination_html += f'<a href="/?keyword={keyword}&page={page-1}" class="btn">이전</a>'
            
            pagination_html += f' <span class="page-num">{page} / {total_pages}</span> '

            if page < total_pages:
                pagination_html += f'<a href="/?keyword={keyword}&page={page+1}" class="btn">다음</a>'
            pagination_html += '</div>'
            
            result_html += pagination_html

    return render_template_string(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>뉴스 검색</title>
        <link rel="stylesheet" href="/static/style.css">
    </head>
    <body>
        <h2>📰 뉴스 검색</h2>
        <form method="POST" action="/">
            <input name="keyword" placeholder="키워드 입력" value="{keyword}">
            <button type="submit">검색</button>
        </form>
        <hr>
        <div class="container">
            {result_html}
        </div>
    </body>
    </html>
    """)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
