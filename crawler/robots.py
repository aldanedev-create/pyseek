from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser
import httpx


def allowed(url: str, user_agent: str) -> bool:
    parts = urlsplit(url)
    robots_url = f"{parts.scheme}://{parts.netloc}/robots.txt"
    try:
        response = httpx.get(robots_url, headers={"user-agent": user_agent}, timeout=5, follow_redirects=True)
        if response.status_code == 404:
            return True
        if response.status_code >= 400:
            return False
        parser = RobotFileParser()
        parser.set_url(robots_url)
        parser.parse(response.text.splitlines())
        return parser.can_fetch(user_agent, url)
    except httpx.HTTPError:
        return False
