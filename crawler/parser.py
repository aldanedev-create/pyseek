from urllib.parse import urljoin
from bs4 import BeautifulSoup


def parse(html: bytes, url: str, encoding: str = "utf-8") -> dict:
    soup = BeautifulSoup(html.decode(encoding, errors="replace"), "html.parser")
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()
    title = soup.title.get_text(" ", strip=True) if soup.title else url
    meta = soup.find("meta", attrs={"name": lambda value: value and value.lower() == "description"})
    description = meta.get("content", "").strip() if meta else ""
    text = soup.get_text(" ", strip=True)
    links = []
    for anchor in soup.find_all("a", href=True):
        try:
            links.append(urljoin(url, anchor["href"]))
        except (TypeError, ValueError):
            continue
    return {"title": title[:500], "description": description[:1000], "text": text[:200000], "links": links[:500]}
