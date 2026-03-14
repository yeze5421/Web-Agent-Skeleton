from dataclasses import dataclass, asdict
from typing import List
import re

import requests
from bs4 import BeautifulSoup

import config


@dataclass
class Article:
    title: str
    url: str
    text: str
    short_summary: str
    score: int

    def to_dict(self):
        return asdict(self)


def fetch_html(url: str) -> str:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/123.0.0.0 Safari/537.36"
        )
    }
    resp = requests.get(url, headers=headers, timeout=config.REQUEST_TIMEOUT_S)
    resp.raise_for_status()
    return resp.text


def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_main_text(html: str) -> tuple[str, str]:
    soup = BeautifulSoup(html, "lxml")

    for tag in soup(["script", "style", "noscript", "svg", "footer", "nav", "aside"]):
        tag.decompose()

    title = soup.title.get_text(" ", strip=True) if soup.title else "无标题"

    candidates: List[str] = []
    for selector in ["article", "main", "body"]:
        node = soup.select_one(selector)
        if node:
            text = node.get_text(" ", strip=True)
            if len(text) > 200:
                candidates.append(text)

    full_text = max(candidates, key=len) if candidates else soup.get_text(" ", strip=True)
    full_text = clean_text(full_text)
    return title, full_text[:12000]


def make_short_summary(text: str, max_sentences: int = 3) -> str:
    parts = re.split(r"(?<=[。！？.!?])", text)
    picked = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        picked.append(p)
        if len(picked) >= max_sentences:
            break
    summary = "".join(picked)
    return summary[:350] if summary else text[:350]


def simple_score(query: str, title: str, text: str) -> int:
    keywords = [x.strip().lower() for x in re.split(r"\s+", query) if x.strip()]
    hay = f"{title} {text[:4000]}".lower()

    score = 0
    for kw in keywords:
        score += hay.count(kw)
    return score


def extract_article(url: str, query: str) -> Article:
    try:
        html = fetch_html(url)
        title, text = extract_main_text(html)
        short_summary = make_short_summary(text)
        score = simple_score(query, title, text)

        return Article(
            title=title,
            url=url,
            text=text,
            short_summary=short_summary,
            score=score,
        )
    except Exception as e:
        return Article(
            title="抓取失败",
            url=url,
            text=f"抓取失败：{e}",
            short_summary=f"抓取失败：{e}",
            score=0,
        )