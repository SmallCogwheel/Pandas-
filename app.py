from flask import Flask, request
import requests
from bs4 import BeautifulSoup
import pandas as pd

app = Flask(__name__)


def crawl(keyword):
    url = f"https://news.google.com/rss/search?q={keyword}&hl=ko&gl=KR&ceid=KR:ko"

    res = requests.get(url)
    soup = BeautifulSoup(res.content, "xml")

    data = []

    for item in soup.select("item")[:10]:
        title = item.title.text
        link = item.link.text

        data.append({
            "title": title,
            "link": link
        })

    df = pd.DataFrame(data)

    if not df.empty:
        df["link"] = df["link"].apply(
            lambda x: f'<a href="{x}" target="_blank">기사보기</a>'
        )

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
            result_html = df.to_html(index=False, escape=False)

    return f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <title>뉴스 검색</title>
    </head>
    <body>
        <h2>뉴스 검색</h2>

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
