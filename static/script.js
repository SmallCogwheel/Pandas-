document.addEventListener('click', function (e) {
    if (e.target && e.target.classList.contains('news-link')) {
        e.preventDefault();
        
        const url = e.target.getAttribute('href');
        const contentBox = document.getElementById('summary-content');
        const linkBox = document.getElementById('original-link-box');
        
        contentBox.innerHTML = '<div class="loading">기사를 분석 중입니다...</div>';
        linkBox.innerHTML = "";

        fetch(`/get_summary?url=${encodeURIComponent(url)}`)
            .then(res => res.json())
            .then(data => {
                contentBox.innerText = data.summary;
                linkBox.innerHTML = `<a href="${url}" target="_blank" class="btn-go">기사 원문 보기</a>`;
            })
            .catch(() => {
                contentBox.innerText = "내용을 불러오지 못했습니다.";
            });
    }
});
