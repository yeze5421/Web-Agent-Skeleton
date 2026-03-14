from dataclasses import dataclass, asdict
from typing import List
from urllib.parse import quote

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

import config


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
    source_engine: str

    def to_dict(self):
        return asdict(self)


class BrowserSearcher:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    def __enter__(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=config.HEADLESS)
        self.context = self.browser.new_context()
        self.page = self.context.new_page()
        self.page.set_default_timeout(config.PAGE_TIMEOUT_MS)
        return self

    def __exit__(self, exc_type, exc, tb):
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def search(self, query: str, limit: int | None = None) -> List[SearchResult]:
        limit = limit or config.MAX_RESULTS
        engine = config.SEARCH_ENGINE.lower().strip()

        if engine == "duckduckgo":
            results = self._search_duckduckgo(query, limit)
        else:
            results = self._search_bing(query, limit)
            if not results:
                results = self._search_duckduckgo(query, limit)

        return self._deduplicate(results)[:limit]

    def _search_bing(self, query: str, limit: int) -> List[SearchResult]:
        results: List[SearchResult] = []
        max_pages = getattr(config, "MAX_SEARCH_PAGES", 3)
        wait_ms = getattr(config, "SEARCH_PAGE_WAIT_MS", 1500)

        for page_no in range(max_pages):
            first = page_no * 10 + 1
            url = f"https://www.bing.com/search?q={quote(query)}&first={first}"

            try:
                print(f"[Bing] 打开第 {page_no + 1} 页：{url}")
                self.page.goto(url, wait_until="domcontentloaded")
                self.page.wait_for_timeout(wait_ms)

                cards = self.page.locator("li.b_algo")
                card_count = cards.count()

                if card_count == 0:
                    print("[Bing] 当前页没有结果，停止翻页")
                    break

                before = len(results)

                for i in range(card_count):
                    if len(results) >= limit:
                        break

                    card = cards.nth(i)
                    try:
                        title = card.locator("h2").inner_text().strip()
                        link = card.locator("h2 a").get_attribute("href")
                        snippet = ""

                        if card.locator(".b_caption p").count() > 0:
                            snippet = card.locator(".b_caption p").inner_text().strip()

                        if title and link:
                            results.append(SearchResult(title, link, snippet, "bing"))
                    except Exception:
                        continue

                results = self._deduplicate(results)
                got_this_page = len(results) - before
                print(f"[Bing] 第 {page_no + 1} 页新增 {got_this_page} 条，累计 {len(results)} 条")

                if len(results) >= limit:
                    break

                if got_this_page == 0:
                    print("[Bing] 当前页没有新增有效结果，停止翻页")
                    break

            except PlaywrightTimeoutError:
                print(f"[Bing] 第 {page_no + 1} 页超时，停止翻页")
                break
            except Exception as e:
                print(f"[Bing] 第 {page_no + 1} 页出错：{e}")
                break

        return results[:limit]

    def _search_duckduckgo(self, query: str, limit: int) -> List[SearchResult]:
        results: List[SearchResult] = []
        max_pages = getattr(config, "MAX_SEARCH_PAGES", 3)
        wait_ms = getattr(config, "SEARCH_PAGE_WAIT_MS", 1500)

        for page_no in range(max_pages):
            offset = page_no * 30
            url = f"https://duckduckgo.com/html/?q={quote(query)}&s={offset}"

            try:
                print(f"[DuckDuckGo] 打开第 {page_no + 1} 页：{url}")
                self.page.goto(url, wait_until="domcontentloaded")
                self.page.wait_for_timeout(wait_ms)

                cards = self.page.locator(".result")
                card_count = cards.count()

                if card_count == 0:
                    print("[DuckDuckGo] 当前页没有结果，停止翻页")
                    break

                before = len(results)

                for i in range(card_count):
                    if len(results) >= limit:
                        break

                    card = cards.nth(i)
                    try:
                        title = ""
                        link = ""
                        snippet = ""

                        if card.locator(".result__title").count() > 0:
                            title = card.locator(".result__title").inner_text().strip()

                        if card.locator(".result__title a").count() > 0:
                            link = card.locator(".result__title a").get_attribute("href") or ""

                        if card.locator(".result__snippet").count() > 0:
                            snippet = card.locator(".result__snippet").inner_text().strip()

                        if title and link:
                            results.append(SearchResult(title, link, snippet, "duckduckgo"))
                    except Exception:
                        continue

                results = self._deduplicate(results)
                got_this_page = len(results) - before
                print(f"[DuckDuckGo] 第 {page_no + 1} 页新增 {got_this_page} 条，累计 {len(results)} 条")

                if len(results) >= limit:
                    break

                if got_this_page == 0:
                    print("[DuckDuckGo] 当前页没有新增有效结果，停止翻页")
                    break

            except PlaywrightTimeoutError:
                print(f"[DuckDuckGo] 第 {page_no + 1} 页超时，停止翻页")
                break
            except Exception as e:
                print(f"[DuckDuckGo] 第 {page_no + 1} 页出错：{e}")
                break

        return results[:limit]

    @staticmethod
    def _deduplicate(items: List[SearchResult]) -> List[SearchResult]:
        seen = set()
        out = []
        for item in items:
            if not item.url or item.url in seen:
                continue
            seen.add(item.url)
            out.append(item)
        return out