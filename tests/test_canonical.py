import pytest
from crawler.canonical import canonicalize


def test_canonicalizes_http_url():
    assert canonicalize("HTTPS://Example.COM/a#fragment") == "https://example.com/a"


@pytest.mark.parametrize("url", ["javascript:alert(1)", "file:///tmp/a", "http://127.0.0.1/"])
def test_rejects_unsafe_url(url):
    with pytest.raises(ValueError):
        canonicalize(url)
