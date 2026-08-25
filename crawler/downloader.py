import httpx


def download(url: str, user_agent: str, max_bytes: int) -> tuple[bytes, int, str]:
    with httpx.Client(follow_redirects=False, timeout=8, headers={"user-agent": user_agent, "accept": "text/html,application/xhtml+xml"}) as client:
        response = client.get(url)
        if response.status_code in {301, 302, 303, 307, 308}:
            raise ValueError("Redirects are not followed automatically; enqueue the validated Location URL")
        if response.status_code >= 400:
            raise ValueError(f"HTTP {response.status_code}")
        content_type = response.headers.get("content-type", "")
        if "html" not in content_type and content_type:
            raise ValueError("Not an HTML document")
        data = response.content
        if len(data) > max_bytes:
            raise ValueError("Document exceeds crawler byte limit")
        return data, response.status_code, response.encoding or "utf-8"
