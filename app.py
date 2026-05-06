from flask import Flask, request, render_template_string
import requests
from bs4 import BeautifulSoup
import pandas as pd

app = Flask(__name__)

def crawl(keyword):
    if not keyword:
        return pd.DataFrame()

    url = f"https://news.google.com/rss/search?q={keyword}&hl=ko&gl=KR&ceid=KR:ko"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        res = requests.get(url, headers=headers)
        # XML 파서 사용 권장 (lxml 설치 필요 시 설치하거나 html.parser 유지)
        soup = BeautifulSoup(res.content, "xml") 
        
        data = []
        # RSS의 각 뉴스 항목은 <item> 태그 내에 있음
        items = soup.find_all("item")

        for item in items[:10]:
            title = item.title.get_text() if item.title else "제목 없음"
            link = item.link.get_text() if item.link else "#"
            
            data.append({
                "title": title,
                "link": link
            })

        df = pd.DataFrame(data)

        if not df.empty:
            # HTML 태그 생성
            df["제목"] = df.apply(
                lambda row: f'<a href="{row["link"]}" target="_blank" rel="noopener noreferrer">{row["title"]}</a>',
                axis=1
            )
            df = df[["제목"]] # 제목 컬럼만 남김

        return df
    except Exception as e:
        print(f"Error: {e}")
        return pd.DataFrame()

@app.route("/", methods=["GET", "POST"])
def home():
    result_html = ""
    keyword = ""

    if request.method == "POST":
        keyword = request.form.get("keyword", "").strip()
        df = crawl(keyword)

        if df.empty:
            result_html = "<p style='color:red;'>결과를 찾을 수 없거나 오류가 발생했습니다.</p>"
        else:
            # table 클래스를 추가하여 나중에 스타일 잡기 편하게 설정
            result_html = "<h3>검색 결과</h3>" + df.to_html(index=False, escape=False, classes='news-table')

    return render_template_string(f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <title>뉴스 검색</title>
        <style>
            body {{ font-family: sans-serif; padding: 20px; }}
            .news-table {{ border-collapse: collapse; width: 100%; }}
            .news-table td, .news-table th {{ border: 1px solid #ddd; padding: 8px; }}
            .news-table tr:nth-child(even){{background-color: #f2f2f2;}}
            a {{ text-decoration: none; color: blue; }}
            a:hover {{ text-decoration: underline; }}
        </style>
    </head>
    <body>
        <h2>📰 뉴스 검색</h2>
        <form method="POST">
            <input name="keyword" placeholder="키워드 입력" value="{keyword}" style="padding: 5px; width: 200px;">
            <button type="submit" style="padding: 5px 15px;">검색</button>
        </form>
        <hr>
        {result_html}
    </body>
    </html>
    """)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
