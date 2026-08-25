from crawler.parser import parse


def test_parser_extracts_searchable_content_and_links():
    page = parse(b'<html><title>Example</title><meta name="description" content="A page"><script>x()</script><p>Hello world</p><a href="/next">Next</a></html>', "https://example.com/")
    assert page["title"] == "Example"
    assert "Hello world" in page["text"]
    assert page["links"] == ["https://example.com/next"]
