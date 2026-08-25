import os
from urllib.parse import urlsplit
from crawler.canonical import canonicalize
from crawler.downloader import download
from crawler.parser import parse
from crawler.robots import allowed
from database import repositories


def crawl_batch(limit: int | None = None) -> dict:
    limit = limit or int(os.getenv("CRAWL_BATCH_SIZE", "5"))
    user_agent = os.getenv("CRAWLER_USER_AGENT", "PySeekBot/0.1 (+https://example.com/pyseek)")
    max_bytes = int(os.getenv("CRAWL_MAX_BYTES", str(2 * 1024 * 1024)))
    items = repositories.claim_batch(limit)
    indexed = failed = 0
    for item in items:
        try:
            url = canonicalize(item["url"])
            if not allowed(url, user_agent):
                raise ValueError("Blocked by robots.txt or robots.txt unavailable")
            body, status, encoding = download(url, user_agent, max_bytes)
            page = parse(body, url, encoding)
            repositories.save_document({**page, "url": url, "canonical_url": url, "domain": urlsplit(url).hostname or "", "status_code": status})
            child_urls = []
            for link in page["links"]:
                try:
                    child = canonicalize(link)
                    if urlsplit(child).netloc == urlsplit(url).netloc:
                        child_urls.append(child)
                except ValueError:
                    pass
            repositories.enqueue_urls(list(dict.fromkeys(child_urls)), url)
            repositories.finish_queue_item(item["id"], True)
            indexed += 1
        except Exception as exc:
            repositories.finish_queue_item(item["id"], False, str(exc))
            failed += 1
    return {"claimed": len(items), "indexed": indexed, "failed": failed}
