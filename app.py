from flask import Flask, request
import requests
from bs4 import BeautifulSoup
import pandas as pd

app = Flask(__name__)

def crawl(keyword):
    url = "https://news.ycombinator.com/"
    res = requests.get(url)
    soup = BeautifulSoup(res.text, "html.parser")

    data = []

    for item in soup.select(".titleline > a"):
        title = item.text

        if keyword.lower() in title.lower():
            data.append({
                "title": title,
                "link": item["href"]
            })

    return pd.DataFrame(data)

@app.route("/", methods=["GET", "POST"])
def home():
    result_html = ""
    keyword = ""

    if request.method == "POST":
        keyword = request.form.get("keyword")
        df = crawl(keyword)

        if len(df) == 0:
            result_html = "<p>결과 없음</p>"
        else:
            result_html = df.to_html(index=False, escape=False)

    return f"""
    <html>
    <body>
        <h2>키워드 크롤링</h2>

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
    app.run(debug=True)
