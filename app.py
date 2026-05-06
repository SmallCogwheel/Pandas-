from flask import Flask, request
import requests
from bs4 import BeautifulSoup
import pandas as pd

app = Flask(__name__)


def crawl(keyword):
    url = f"https://news.google.com/rss/search?q={keyword}&hl=ko&gl=KR&ceid=KR:ko"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.content, "html.parser")

    data = []

    for item in soup.select("item")[:10]:
        title = item.title.text if item.title else "제목 없음"
        link = item.link.text if item.link else ""

        # 🔥 링크 보정 (핵심)
        if link.startswith("/"):
            link = "https://news.google.com" + link
        elif not link.startswith("http"):
            link = "#"

        data.append({
            "title": title,
            "link": link
        })

    df = pd.DataFrame(data)

    if not df.empty:
        # 제목 클릭 → 새 탭 이동
        df["title"] = df.apply(
            lambda row: f'<a href="{row["link"]}" target="_blank" rel="noopener noreferrer">{row["title"]}</a>',
            axis=1
        )

        df = df.drop(columns=["link"])
        df.columns = ["제목"]

    return df


@app.route("/", methods=["GET", "POST"])
def home():
    result_html = ""
    keyword = ""

    if request.method == "POST":
        keyword = request.form.get("keyword", "").strip()
        df = crawl(keyword)

        if df.empty:
            result_html = "<p>결과 없음</p>"
        else:
            result_html = "<h3>검색 결과</h3>" + df.to_html(index=False, escape=False)

    return f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <title>뉴스 검색</title>
        <link rel="stylesheet" href="/static/style.css">
    </head>
    <body>
        <h2>📰 뉴스 검색</h2>

        <form method="POST">
            <input name="keyword" placeholder="키워드 입력" value="{keyword}">
            <button type="submit">검색</button>
        </form>

        <hr>

        {result_html}
    </body>
    </html>
    """


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
