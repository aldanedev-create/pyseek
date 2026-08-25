import sys
from crawler.canonical import canonicalize
from database import repositories


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("Usage: python scripts/seed.py https://example.com [https://another.example]")
    urls = [canonicalize(value) for value in sys.argv[1:101]]
    print({"added": repositories.enqueue_urls(list(dict.fromkeys(urls)))})
