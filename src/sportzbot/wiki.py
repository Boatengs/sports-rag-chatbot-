"""Live Wikipedia retrieval: search, fetch the page as HTML, and cut it into passages.

The parsed HTML is used instead of the plain text extract because sports facts often sit in
infoboxes and results tables, which plain text extracts leave out. Tables become one line per row,
with the column headers repeated, so a row still makes sense on its own.
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import asdict, dataclass
from pathlib import Path

import requests
from bs4 import BeautifulSoup, Tag

API = "https://en.wikipedia.org/w/api.php"
USER_AGENT = "sportzbot/2.0 (https://github.com/Boatengs/sports-rag-chatbot-)"
DROP_CLASSES = (
    "navbox",
    "reference",
    "reflist",
    "mw-editsection",
    "hatnote",
    "sistersitebox",
    "metadata",
    "noprint",
    "mw-empty-elt",
    "shortdescription",
    "toc",
)
STOP_SECTIONS = {"references", "external links", "see also", "notes", "further reading", "bibliography", "sources", "citations", "footnotes"}


@dataclass
class Passage:
    title: str
    section: str
    text: str
    revid: int

    @property
    def url(self) -> str:
        return "https://en.wikipedia.org/wiki/" + self.title.replace(" ", "_")

    def render(self) -> str:
        where = self.title if not self.section else f"{self.title} > {self.section}"
        return f"{where}\n{self.text}"


class Wikipedia:
    def __init__(self, cache_dir: Path | None = None, pause: float = 0.1):
        self.s = requests.Session()
        self.s.headers["User-Agent"] = USER_AGENT
        self.cache_dir = Path(cache_dir) if cache_dir else None
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.pause = pause

    def _api(self, **params) -> dict:
        params = {"format": "json", "formatversion": 2, **params}
        for attempt in range(5):
            try:
                r = self.s.get(API, params=params, timeout=60)
                if r.status_code == 429 or r.status_code >= 500:
                    raise requests.HTTPError(str(r.status_code))
                r.raise_for_status()
                time.sleep(self.pause)
                return r.json()
            except (requests.RequestException, ValueError):
                if attempt == 4:
                    raise
                time.sleep(2**attempt)
        raise RuntimeError("unreachable")

    def search(self, query: str, limit: int = 5) -> list[str]:
        j = self._api(action="query", list="search", srsearch=query, srlimit=limit, srprop="", srnamespace=0)
        return [h["title"] for h in j.get("query", {}).get("search", [])]

    def page(self, title: str) -> list[Passage]:
        key = None
        if self.cache_dir:
            key = self.cache_dir / (re.sub(r"[^\w.-]+", "_", title)[:150] + ".json")
            if key.exists():
                return [Passage(**p) for p in json.loads(key.read_text())]
        j = self._api(action="parse", page=title, prop="text|revid", redirects=1, disableeditsection=1)
        if "parse" not in j:
            return []
        p = j["parse"]
        passages = html_to_passages(p["title"], p["text"], p["revid"])
        if key:
            key.write_text(json.dumps([asdict(x) for x in passages], ensure_ascii=False))
        return passages


def _clean(el: Tag) -> str:
    text = el.get_text(" ", strip=True)
    text = re.sub(r"\[\s*(?:\d+|[a-z]|note \d+|citation needed)\s*\]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.replace(" ,", ",").replace(" .", ".").replace("( ", "(").replace(" )", ")").strip()


def _table_rows(table: Tag) -> list[str]:
    cls = table.get("class") or []
    lines = []
    if "infobox" in cls:
        for tr in table.find_all("tr"):
            th, td = tr.find("th"), tr.find("td")
            if th and td:
                lines.append(f"{_clean(th)}: {_clean(td)}")
            elif th and not td and _clean(th):
                lines.append(_clean(th))
        return [x for x in lines if x]
    header: list[str] = []
    caption = table.find("caption")
    cap = _clean(caption) if caption else ""
    for tr in table.find_all("tr"):
        cells = tr.find_all(["th", "td"], recursive=False)
        if not cells:
            continue
        values = [_clean(c) for c in cells]
        if all(c.name == "th" for c in cells) and not header:
            header = values
            continue
        if header and len(values) == len(header):
            row = "; ".join(f"{h}: {v}" for h, v in zip(header, values, strict=True) if v and h)
        else:
            row = " | ".join(v for v in values if v)
        if row:
            lines.append(row)
    return [f"{cap}: {x}" if cap else x for x in lines]


def html_to_passages(title: str, html: str, revid: int, max_words: int = 120) -> list[Passage]:
    soup = BeautifulSoup(html, "lxml")
    root = soup.find("div", class_="mw-parser-output") or soup
    for bad in root.find_all(class_=lambda c: c and any(x in c.split() for x in DROP_CLASSES)):
        bad.decompose()
    for bad in root.find_all(["style", "script", "sup"]):
        bad.decompose()

    units: list[tuple[str, str]] = []
    section = ""
    stop = False

    def visit(node: Tag) -> None:
        nonlocal section, stop
        for el in node.children:
            if stop or not isinstance(el, Tag):
                continue
            if el.name in ("h2", "h3", "h4") or (el.name == "div" and "mw-heading" in (el.get("class") or [])):
                h = el if el.name in ("h2", "h3", "h4") else el.find(["h2", "h3", "h4"])
                section = _clean(h) if h else section
                if section.lower() in STOP_SECTIONS:
                    stop = True
                continue
            if el.name == "p":
                t = _clean(el)
                if t:
                    units.append((section, t))
            elif el.name in ("ul", "ol"):
                for li in el.find_all("li", recursive=False):
                    t = _clean(li)
                    if t:
                        units.append((section, "- " + t))
            elif el.name == "dl":
                t = _clean(el)
                if t:
                    units.append((section, t))
            elif el.name == "table":
                for row in _table_rows(el):
                    units.append((section, row))
            elif el.name in ("div", "section", "blockquote"):
                visit(el)

    visit(root)

    passages: list[Passage] = []
    buf: list[str] = []
    words = 0
    cur = None
    for sec, text in units:
        n = len(text.split())
        if buf and (sec != cur or words + n > max_words):
            passages.append(Passage(title, cur or "", "\n".join(buf), revid))
            buf, words = [], 0
        if n > max_words * 2:
            toks = text.split()
            for i in range(0, len(toks), max_words):
                passages.append(Passage(title, sec, " ".join(toks[i : i + max_words]), revid))
            cur = sec
            continue
        buf.append(text)
        words += n
        cur = sec
    if buf:
        passages.append(Passage(title, cur or "", "\n".join(buf), revid))
    return passages
