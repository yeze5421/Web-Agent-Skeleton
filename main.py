from searcher import BrowserSearcher
from extractor import extract_article
from report_writer import save_csv, save_markdown


def run(question: str):
    print(f"\n[1/4] 开始搜索：{question}")
    with BrowserSearcher() as searcher:
        search_results = searcher.search(question)

    if not search_results:
        print("没有搜索到结果。你可以换关键词，或者把 config.py 里的 SEARCH_ENGINE 改成 duckduckgo 再试。")
        return

    print(f"[2/4] 拿到 {len(search_results)} 条搜索结果")
    articles = []

    for i, item in enumerate(search_results, 1):
        print(f"[3/4] 抓取正文 {i}/{len(search_results)}: {item.url}")
        article = extract_article(item.url, question)
        articles.append({
            "rank": i,
            "search_title": item.title,
            "title": article.title,
            "url": article.url,
            "snippet": item.snippet,
            "score": article.score,
            "short_summary": article.short_summary,
            "text": article.text,
            "source_engine": item.source_engine,
        })

    articles.sort(key=lambda x: x["score"], reverse=True)

    csv_path = save_csv(articles)
    md_path = save_markdown(question, articles)

    print("\n[4/4] 完成")
    print(f"CSV 已保存：{csv_path}")
    print(f"Markdown 报告已保存：{md_path}")
    print("\n你现在已经有一个不依赖大模型的网页信息搜集智能体雏形了。")


if __name__ == "__main__":
    question = input("请输入你要搜索的问题：").strip()
    if not question:
        raise ValueError("问题不能为空")
    run(question)
